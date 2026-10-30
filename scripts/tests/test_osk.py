#!/usr/bin/env python3
"""osk.py and the on-screen keyboard layout: every key must type what it shows."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

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


class SuggestionKeyTests(unittest.TestCase):
    def test_the_layout_can_type_every_suggestion(self):
        labels = {key.get('label') for row in LAYOUT['pages']['letters'] for key in row['keys']}
        labels |= {key['label'] for variants in LAYOUT['accents'].values() for key in variants}
        for letter in 'abcdefghijklmnopqrstuvwxyzàèéìòù':
            self.assertIn(letter, labels)
        self.assertTrue(osk.predict.TYPABLE.fullmatch('abcdefghijklmnopqrstuvwxyzàèéìòù'))

    def test_backspace_and_space_are_on_the_letters_page(self):
        actions = {key.get('action') for row in LAYOUT['pages']['letters'] for key in row['keys']}
        self.assertLessEqual({'backspace', 'space'}, actions)


class SecretFieldTests(InputMethodTests):
    def purpose(self, hint, name):
        method = self.method()
        method.event(0, b'')
        method.event(4, struct.pack('<II', hint, osk.PURPOSES.index(name)))
        method.event(5, b'')
        return method.emitted[-1]['purpose']

    def test_hidden_or_sensitive_text_counts_as_a_password(self):
        self.assertEqual(self.purpose(0x40, 'normal'), 'password')
        self.assertEqual(self.purpose(0x80, 'alpha'), 'password')

    def test_other_hints_change_nothing(self):
        self.assertEqual(self.purpose(0x1 | 0x2 | 0x4, 'normal'), 'normal')

    def test_a_hidden_pin_stays_on_the_digits(self):
        self.assertEqual(self.purpose(0x40, 'pin'), 'pin')


class PredictionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        for name, value in (('DIRECTORY', self.directory), ('MEMORY', self.directory / 'memory.json')):
            patcher = mock.patch.object(osk.predict, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_missing_lists_are_fetched_once_and_type_nothing(self):
        prediction = osk.Prediction()
        with mock.patch.object(osk.subprocess, 'Popen') as popen:
            self.assertEqual(prediction.letters(''), {})
            self.assertEqual(prediction.letters('ca'), {})
        popen.assert_called_once()

    def test_a_failed_fetch_does_not_reach_the_keys(self):
        prediction = osk.Prediction()
        with mock.patch.object(osk.subprocess, 'Popen', side_effect=OSError):
            self.assertEqual(prediction.letters(''), {})

    def test_a_broken_list_is_not_read_again(self):
        for path in osk.predict.paths():
            path.write_text('casa molte\n')
        prediction = osk.Prediction()
        with mock.patch.object(osk.predict, 'Words', side_effect=ValueError) as words:
            self.assertEqual(prediction.letters(''), {})
            self.assertEqual(prediction.letters('c'), {})
        words.assert_called_once()

    def test_lists_load_when_they_arrive(self):
        for path in osk.predict.paths():
            path.write_text('casa 30\ncane 10\n')
        self.assertEqual(osk.Prediction().letters('ca'), {'s': 0.75, 'n': 0.25})

    def test_the_answer_names_its_word(self):
        with mock.patch.object(osk, 'emit') as emit, mock.patch.object(osk.PREDICTION, 'letters', return_value={'a': 1.0}):
            osk.handle(None, 'predict ca')
            osk.handle(None, 'predict')
        self.assertEqual([call.args[0]['word'] for call in emit.call_args_list], ['ca', ''])

    def test_learning_goes_through_the_words(self):
        with mock.patch.object(osk.PREDICTION, 'words') as words:
            osk.handle(None, 'learn casa')
            osk.handle(None, 'forget cane')
        words.learn.assert_called_once_with('casa')
        words.forget.assert_called_once_with('cane')

    def test_a_full_disk_does_not_reach_the_keys(self):
        with mock.patch.object(osk.PREDICTION, 'words') as words:
            words.learn.side_effect = OSError
            osk.handle(None, 'learn casa')

    def test_learning_before_the_lists_arrive_is_ignored(self):
        osk.handle(None, 'learn casa')

    def test_a_malformed_line_is_ignored(self):
        with mock.patch.object(osk, 'emit') as emit:
            osk.handle(None, 'predict too many words')
        emit.assert_not_called()


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
