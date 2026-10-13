#!/usr/bin/env python3
"""Validate translation catalogs, locale selection, and parameter handling."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
DESKTOP = ROOT / 'quickshell/.config/quickshell/desktop'
CATALOGS = DESKTOP / 'i18n'
HELPER = ROOT / 'shell/.local/libexec/desktop/i18n.py'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('desktop_i18n', HELPER)
i18n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i18n)


class TranslationTests(unittest.TestCase):
    def test_locale_selection(self):
        cases = [
            ('LANG="en_US.UTF-8"', {'LANG': 'it_IT'}, 'en_US'),
            ("LANG='it_IT.UTF-8'", {}, 'it_IT'),
            (' LANG = it_IT.UTF-8 # comment', {}, 'it_IT'),
            ('LANG=en_US\nLC_MESSAGES=it_IT.UTF-8', {}, 'it_IT'),
            ('LANG=it_IT\nLC_MESSAGES=en_US.UTF-8', {}, 'en_US'),
            ('LANG=it_IT\nLC_MESSAGES=', {}, 'it_IT'),
            ('LANG=it-IT.UTF-8@euro', {}, 'it_IT'),
            ('LANG=en_GB.UTF-8', {}, 'en_US'),
            ('LANG=de_DE.UTF-8', {}, 'en_US'),
            ('LANG=C.UTF-8', {}, 'en_US'),
            ('LANG=POSIX', {}, 'en_US'),
            ('# LANG=it_IT', {'LC_MESSAGES': 'it_IT.UTF-8'}, 'it_IT'),
            ('', {'LC_ALL': 'it_IT', 'LANG': 'en_US'}, 'it_IT'),
            ('LANG="unterminated', {'LANG': 'en_US'}, 'en_US'),
            ('LANG=it_IT;touch /tmp/not-a-command', {}, 'en_US'),
            ('', {}, 'en_US'),
        ]
        for text, env, expected in cases:
            with self.subTest(text=text, env=env):
                self.assertEqual(i18n.language_from_config(text, env), expected)

    def test_catalog_parity_and_placeholders(self):
        italian = json.loads((CATALOGS / 'it_IT.json').read_text())
        english = json.loads((CATALOGS / 'en_US.json').read_text())
        self.assertEqual(italian.keys(), english.keys())
        for key in italian:
            with self.subTest(message=key):
                self.assertIsInstance(italian[key], str)
                self.assertIsInstance(english[key], str)
                self.assertTrue(italian[key])
                self.assertTrue(english[key])
                placeholders = lambda text: sorted(re.findall(r'%[1-9][0-9]*', text))
                self.assertEqual(placeholders(italian[key]), placeholders(english[key]))

    def test_helper_uses_shared_catalogs(self):
        config = ROOT / 'quickshell/.config'
        for lang, expected in [('it_IT', 'Applicazioni'), ('en_US', 'Applications')]:
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(config)}), patch.object(i18n, 'language', return_value=lang):
                self.assertEqual(i18n.tr('Applicazioni'), expected)
                self.assertEqual(i18n.tr('Password per ') + 'a$&b', ('Password per ' if lang == 'it_IT' else 'Password for ') + 'a$&b')
                self.assertEqual(i18n.tr('Sposta al workspace %1', [4]), 'Sposta al workspace 4' if lang == 'it_IT' else 'Move to workspace 4')
                self.assertEqual(i18n.tr('Unknown %1', ['$&']), 'Unknown $&')
                self.assertEqual(i18n.tr('Unknown %1'), 'Unknown %1')

    def test_static_qml_messages_exist(self):
        catalog = json.loads((CATALOGS / 'en_US.json').read_text())
        for path in DESKTOP.rglob('*.qml'):
            if path.name.startswith('test-'):
                continue
            for match in re.finditer(r'''I18n\.tr\(\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')''', path.read_text()):
                with self.subTest(file=str(path), message=match[1]):
                    self.assertTrue(ast.literal_eval(match[1]) in catalog, "Missing translation: " + match[1])


if __name__ == '__main__':
    unittest.main()
