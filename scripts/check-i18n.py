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

    def flattened_catalog(self, language):
        data = json.loads((CATALOGS / (language + '.json')).read_text())
        result = {}

        def visit(branch, prefix=''):
            self.assertIsInstance(branch, dict)
            self.assertTrue(branch)
            for name, value in branch.items():
                self.assertRegex(name, r'^[a-z][a-zA-Z0-9]*$')
                key = prefix + name
                if isinstance(value, dict):
                    visit(value, key + '.')
                else:
                    self.assertIsInstance(value, str)
                    self.assertTrue(value)
                    self.assertIn('.', key, 'Messages must belong to a namespace')
                    result[key] = value
        visit(data)
        return result

    def test_catalog_parity_and_placeholders(self):
        italian = self.flattened_catalog('it_IT')
        english = self.flattened_catalog('en_US')
        self.assertEqual(italian.keys(), english.keys())
        for key in italian:
            with self.subTest(key=key):
                placeholders = lambda text: sorted(re.findall(r'%[1-9][0-9]*', text))
                self.assertEqual(placeholders(italian[key]), placeholders(english[key]))

    def test_helper_uses_shared_catalogs(self):
        config = ROOT / 'quickshell/.config'
        for lang in ('it_IT', 'en_US'):
            expected = self.flattened_catalog(lang)
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(config)}), patch.object(i18n, 'language', return_value=lang):
                self.assertEqual(i18n.tr('launcher.title'), expected['launcher.title'])
                self.assertEqual(i18n.tr('network.passwordFor', ['a$&b']), expected['network.passwordFor'].replace('%1', 'a$&b'))
                self.assertEqual(i18n.tr('bindings.moveToWorkspace', [4]), expected['bindings.moveToWorkspace'].replace('%1', '4'))
                self.assertEqual(i18n.tr('missing.key'), 'missing.key')
                self.assertEqual(i18n.tr('bindings.moveToWorkspace'), expected['bindings.moveToWorkspace'])
                self.assertEqual(i18n.tr('bindings.moveDirection', ['$&']), expected['bindings.moveDirection'].replace('%1', '$&'))

    def test_nested_lookup_and_english_fallback(self):
        self.assertEqual(i18n.lookup({'clipboard': {'title': 'Clipboard'}}, 'clipboard.title'), 'Clipboard')
        for key in ('clipboard', 'clipboard.missing', 'clipboard.title.child', 'missing.key'):
            self.assertIsNone(i18n.lookup({'clipboard': {'title': 'Clipboard'}}, key))
        catalogs = {'it_IT': {'clipboard': {}}, 'en_US': {'clipboard': {'title': 'Clipboard'}}}
        with patch.object(i18n, 'language', return_value='it_IT'), patch.object(i18n, 'catalog', side_effect=catalogs.get):
            self.assertEqual(i18n.tr('clipboard.title'), 'Clipboard')
            self.assertEqual(i18n.tr('clipboard.missing'), 'clipboard.missing')

    def assert_translation_key(self, key, catalog):
        self.assertRegex(key, r'^[a-z][a-zA-Z0-9]*(?:\.[a-z][a-zA-Z0-9]*)+$')
        self.assertIn(key, catalog, 'Missing translation: ' + key)

    def test_qml_and_adapter_references(self):
        catalog = self.flattened_catalog('en_US')
        literal = r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'"
        for path in DESKTOP.rglob('*.qml'):
            if path.name.startswith('test-'):
                continue
            text = path.read_text()
            # Exact first arguments catch accidental source strings. Semantic literals
            # also cover ternary keys and both singular/plural variants.
            for match in re.finditer(r'I18n\.(?:tr|plural)\(\s*(' + literal + ')', text):
                with self.subTest(file=str(path), key=match[1]):
                    self.assert_translation_key(ast.literal_eval(match[1]), catalog)
            for match in re.finditer(literal, text):
                value = ast.literal_eval(match[0])
                if re.fullmatch(r'[a-z][a-zA-Z0-9]*(?:\.[a-z][a-zA-Z0-9]*)+', value) and value.split('.')[0] in {key.split('.')[0] for key in catalog}:
                    with self.subTest(file=str(path), key=value):
                        self.assert_translation_key(value, catalog)
        adapters = (DESKTOP / 'i18n/Sources.js').read_text()
        bind_labels = json.loads(re.search(r'var bindKeys = (\{.*?\});', adapters, re.S)[1])
        for label, key in bind_labels.items():
            self.assertEqual(label, catalog[key], 'Bind source descriptions must use the English catalog text')
        for match in re.finditer(r':\s*("[^"\n]+")', adapters):
            self.assert_translation_key(json.loads(match[1]), catalog)

    def test_python_and_command_references(self):
        catalog = self.flattened_catalog('en_US')
        for path in HELPER.parent.glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'tr' and node.args and isinstance(node.args[0], ast.Constant):
                    with self.subTest(file=str(path), key=node.args[0].value):
                        self.assert_translation_key(node.args[0].value, catalog)
        # Wrappers and the Hyprland config call i18n.py directly (or desktop-power's message()): every key
        # after it must exist.
        sources = list((ROOT / 'shell/.local/bin').glob('desktop-*')) + list((ROOT / 'hypr/.config/hypr/config').glob('*.lua'))
        for path in sources:
            text = path.read_text()
            keys = re.findall(r"message '([^']+)'", text)
            for line in text.splitlines():
                if 'i18n.py' in line and 'message()' not in line:
                    after = line.split('i18n.py', 1)[1]
                    keys += re.findall(r'(?<![\w$/-])([a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9]+)+)(?![\w/])', after)
            for key in keys:
                with self.subTest(file=str(path), key=key):
                    self.assert_translation_key(key, catalog)


if __name__ == '__main__':
    unittest.main()
