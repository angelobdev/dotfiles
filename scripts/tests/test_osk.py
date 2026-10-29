#!/usr/bin/env python3
"""osk.py and the on-screen keyboard layout: every key must type what it shows."""
import json
from pathlib import Path
import struct
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import osk  # noqa: E402

LAYOUT = json.loads((REPO / 'quickshell/.config/quickshell/desktop/osk/layouts/it.json').read_text(encoding='utf-8'))


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xkb = osk.Xkb('it')

    def typed(self, code, mods):
        return self.xkb.lookup(code, mods)['text']

    def test_every_label_is_what_the_key_types(self):
        for name, rows in LAYOUT['pages'].items():
            for row in rows:
                for key in row['keys']:
                    if 'label' not in key:
                        continue
                    with self.subTest(page=name, key=key['label']):
                        self.assertEqual(self.typed(key['code'], key.get('mods', 0)), key['label'])
                        if 'shift' in key:
                            self.assertEqual(self.typed(key['code'], 1), key['shift'])
                        elif key['label'].isalpha() and key.get('mods', 0) == 0 and name == 'letters':
                            self.assertEqual(self.typed(key['code'], 1), key['label'].upper())

    def test_accents_type_the_accented_vowels(self):
        for letter, variants in LAYOUT['accents'].items():
            for key in variants:
                with self.subTest(key=key['label']):
                    self.assertEqual(self.typed(key['code'], key.get('mods', 0)), key['label'])
                    self.assertEqual(key['label'][0].encode('ascii', 'ignore'), b'')

    def test_rows_are_ten_units_wide(self):
        for name, rows in LAYOUT['pages'].items():
            for index, row in enumerate(rows):
                width = 2 * row.get('indent', 0) + sum(key.get('width', 1) for key in row['keys'])
                self.assertEqual(width, 10, '%s row %d' % (name, index))

    def test_pages_link_to_each_other(self):
        for rows in LAYOUT['pages'].values():
            for row in rows:
                for key in row['keys']:
                    if key.get('action') == 'page':
                        self.assertIn(key['page'], LAYOUT['pages'])

    def test_extra_keys_are_named_or_drawn(self):
        for key in LAYOUT['extra']:
            self.assertTrue('name' in key or 'label' in key or 'icon' in key)
            self.assertTrue('code' in key or key.get('action') == 'modifier')


class WireTests(unittest.TestCase):
    def test_strings_are_length_prefixed_and_padded(self):
        encoded = osk.Wayland.string('wl_seat')
        self.assertEqual(struct.unpack('<I', encoded[:4])[0], 8)
        self.assertEqual(encoded[4:12], b'wl_seat\0')
        self.assertEqual(len(encoded) % 4, 0)
        self.assertEqual(len(osk.Wayland.string('abc')), 8)

    def test_modifier_masks(self):
        self.assertEqual((osk.MASKS['shift'], osk.MASKS['ctrl'], osk.MASKS['alt'], osk.MASKS['altgr']), (1, 4, 8, 128))


if __name__ == '__main__':
    unittest.main()
