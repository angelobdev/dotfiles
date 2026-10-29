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


class InputMethodTests(unittest.TestCase):
    def method(self):
        method = osk.InputMethod.__new__(osk.InputMethod)
        method.emitted = []
        method.emit = method.emitted.append
        method.pending, method.active, method.purpose = {}, False, 'normal'
        return method

    def test_events_apply_on_done(self):
        method = self.method()
        method.event(0, b'')
        method.event(4, struct.pack('<II', 0, osk.PURPOSES.index('digits')))
        self.assertEqual(method.emitted, [])
        method.event(5, b'')
        self.assertEqual(method.emitted, [{'event': 'activate', 'purpose': 'digits'}])
        method.event(1, b'')
        method.event(5, b'')
        self.assertEqual(method.emitted[-1], {'event': 'deactivate'})

    def test_a_repeated_done_reports_nothing_new(self):
        method = self.method()
        method.event(0, b'')
        method.event(5, b'')
        method.event(5, b'')
        self.assertEqual(method.emitted, [{'event': 'activate', 'purpose': 'normal'}])

    def test_a_new_purpose_while_active_is_reported(self):
        method = self.method()
        method.event(0, b'')
        method.event(5, b'')
        method.event(4, struct.pack('<II', 0, osk.PURPOSES.index('terminal')))
        method.event(5, b'')
        self.assertEqual(method.emitted[-1], {'event': 'activate', 'purpose': 'terminal'})

    def test_unknown_purposes_are_normal_and_unavailable_is_reported(self):
        method = self.method()
        method.event(0, b'')
        method.event(4, struct.pack('<II', 0, 99))
        method.event(5, b'')
        method.event(6, b'')
        self.assertEqual(method.emitted, [{'event': 'activate', 'purpose': 'normal'}, {'event': 'unavailable'}])


class WireTests(unittest.TestCase):
    def test_strings_are_length_prefixed_and_padded(self):
        encoded = osk.Wayland.string('wl_seat')
        self.assertEqual(struct.unpack('<I', encoded[:4])[0], 8)
        self.assertEqual(encoded[4:12], b'wl_seat\0')
        self.assertEqual(len(encoded) % 4, 0)
        self.assertEqual(len(osk.Wayland.string('abc')), 8)

    def test_modifier_masks_type_what_the_layout_says(self):
        xkb = osk.Xkb('it')
        self.assertEqual(xkb.lookup(16, 1)['text'], 'Q')
        self.assertEqual(xkb.lookup(39, 128)['text'], '@')


if __name__ == '__main__':
    unittest.main()
