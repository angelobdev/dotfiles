#!/usr/bin/env python3
"""xwayland.py: Aseprite's whole-number scale, its ini file edited in place, and a sane cursor size."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import xwayland  # noqa: E402


class AsepriteTests(unittest.TestCase):
    def test_the_scale_is_the_nearest_whole_number(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('DESKTOP_ASEPRITE_SCALE', None)
            self.assertEqual([xwayland.aseprite_scale(scale) for scale in (1, 1.25, 1.5, 1.667, 2)], [2, 3, 3, 3, 4])
        with mock.patch.dict(os.environ, {'DESKTOP_ASEPRITE_SCALE': '1'}):
            self.assertEqual(xwayland.aseprite_scale(1.667), 2)
        with mock.patch.dict(os.environ, {'DESKTOP_ASEPRITE_SCALE': 'big'}), \
                mock.patch.object(xwayland, 'tr', side_effect=lambda key, values=(): key), self.assertRaises(ValueError):
            xwayland.aseprite_scale(1)

    def test_an_ini_value_is_replaced_in_its_section_only(self):
        with tempfile.TemporaryDirectory() as folder:
            ini = Path(folder) / 'aseprite.ini'
            ini.write_text('[general]\nscreen_scale = 1\nui_scale = 1\n\n[theme]\nscreen_scale = 9\n')
            xwayland.set_ini_value(ini, 'general', 'screen_scale', 3)
            self.assertEqual(ini.read_text(), '[general]\nscreen_scale = 3\nui_scale = 1\n\n[theme]\nscreen_scale = 9\n')
            xwayland.set_ini_value(ini, 'general', 'ui_scale', 2, overwrite=False)
            self.assertIn('ui_scale = 1\n', ini.read_text())
            xwayland.set_ini_value(ini, 'misc', 'key', 'v')
            self.assertTrue(ini.read_text().endswith('[misc]\nkey = v\n'))

    def test_a_missing_ini_gets_its_section(self):
        with tempfile.TemporaryDirectory() as folder:
            ini = Path(folder) / 'aseprite.ini'
            xwayland.set_ini_value(ini, 'general', 'screen_scale', 2)
            self.assertEqual(ini.read_text(), '[general]\nscreen_scale = 2\n')


class CursorTests(unittest.TestCase):
    def test_the_cursor_size_falls_back_when_gsettings_has_none_or_an_odd_one(self):
        for output, code, size in (('32\n', 0, 32), ('2\n', 0, xwayland.CURSOR_SIZE), ('', 1, xwayland.CURSOR_SIZE), ('x\n', 0, xwayland.CURSOR_SIZE)):
            with self.subTest(output=output), mock.patch.object(xwayland.subprocess, 'run', return_value=mock.Mock(returncode=code, stdout=output)):
                self.assertEqual(xwayland.cursor_size(), size)


if __name__ == '__main__':
    unittest.main()
