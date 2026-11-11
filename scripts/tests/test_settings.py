#!/usr/bin/env python3
"""SettingsSchema.js against Config.qml and the catalogs: same defaults, sane limits, every label translated."""
import json
from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[2]
SHELL = REPO / 'quickshell/.config/quickshell/desktop'


def schema():
    # One option per line in SettingsSchema.js: { key: "…", section: "…", … } (a choice may wrap onto a second line).
    text = (SHELL / 'SettingsSchema.js').read_text(encoding='utf-8')
    body = text[text.index('const options = ['):text.index('];')]
    entries = []
    for block in re.findall(r'\{ key:.*?\}(?=,\s*(?:\{|//)|\s*$)', body, re.S):
        fields = {}
        for name, value in re.findall(r'(\w+): ("[^"]*"|\[[^\]]*\]|true|false|-?[0-9.]+)', block):
            fields[name] = json.loads(value)
        entries.append(fields)
    return entries


def config_defaults():
    text = (SHELL / 'Config.qml').read_text(encoding='utf-8')
    return {name: json.loads(value) for name, value in re.findall(r'pick\("(\w+)", ("[^"]*"|true|false|-?[0-9.]+)\)', text)}


def lookup(catalog, key):
    value = catalog
    for part in key.split('.'):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.options = schema()
        cls.defaults = config_defaults()
        cls.catalogs = {name: json.loads((SHELL / f'i18n/{name}.json').read_text(encoding='utf-8')) for name in ('en_US', 'it_IT')}

    def test_the_schema_was_read(self):
        self.assertGreater(len(self.options), 20)
        self.assertEqual(len({option['key'] for option in self.options}), len(self.options), 'a key listed twice')

    def test_defaults_match_config(self):
        for option in self.options:
            self.assertIn(option['key'], self.defaults, option['key'])
            self.assertEqual(option['fallback'], self.defaults[option['key']], option['key'])

    def test_limits_hold_the_default(self):
        for option in self.options:
            key, fallback = option['key'], option['fallback']
            if option['type'] == 'number':
                self.assertLessEqual(option['min'], fallback, key)
                self.assertLessEqual(fallback, option['max'], key)
                steps = (fallback - option['min']) / option['step']
                self.assertAlmostEqual(steps, round(steps), msg=key)
            elif option['type'] == 'choice':
                self.assertIn(fallback, option['options'], key)
            elif option['type'] == 'bool':
                self.assertIsInstance(fallback, bool, key)
            elif option['type'] == 'time':
                self.assertRegex(fallback, r'^([01][0-9]|2[0-3]):[0-5][0-9]$', key)
            else:
                self.assertEqual(option['type'], 'text', key)

    def test_every_label_is_in_both_catalogs(self):
        keys = set()
        for option in self.options:
            keys |= {f'settings.options.{option["key"]}', f'settings.groups.{option["group"]}', f'settings.sections.{option["section"]}'}
            if option.get('hint'):
                keys.add(f'settings.hints.{option["key"]}')
            if option.get('placeholder'):
                keys.add(f'settings.placeholders.{option["key"]}')
        for name, catalog in self.catalogs.items():
            for key in sorted(keys):
                self.assertIsInstance(lookup(catalog, key), str, f'{name}: {key}')
        # No hint text without an option that shows it.
        hinted = {option['key'] for option in self.options if option.get('hint')}
        for name, catalog in self.catalogs.items():
            self.assertEqual(set(catalog['settings']['hints']), hinted, name)

    def test_every_section_is_in_the_sidebar(self):
        panel = (SHELL / 'panels/SettingsPanel.qml').read_text(encoding='utf-8')
        sidebar = set(re.findall(r'name: "(\w+)",\s*icon:', panel))
        self.assertLessEqual({option['section'] for option in self.options}, sidebar)


class SearchTests(unittest.TestCase):
    """panels/settings/SettingsSearch.js: its catalog keys and tabs; the matching itself is tst_settings_search.qml."""

    @classmethod
    def setUpClass(cls):
        cls.search = (SHELL / 'panels/settings/SettingsSearch.js').read_text(encoding='utf-8')
        cls.catalogs = {name: json.loads((SHELL / f'i18n/{name}.json').read_text(encoding='utf-8')) for name in ('en_US', 'it_IT')}

    def test_every_key_is_in_both_catalogs(self):
        keys = re.findall(r'"((?:settings|theming)\.[a-zA-Z.]+)"', self.search)
        self.assertGreater(len(keys), 20)
        for name, catalog in self.catalogs.items():
            for key in keys:
                self.assertIsInstance(lookup(catalog, key), str, f'{name}: {key}')
        # No keyword list that the index does not read.
        for name, catalog in self.catalogs.items():
            listed = set()

            def visit(branch, prefix):
                for part, value in branch.items():
                    if isinstance(value, dict):
                        visit(value, f'{prefix}.{part}')
                    else:
                        listed.add(f'{prefix}.{part}')
            visit(catalog['settings']['search']['keywords'], 'settings.search.keywords')
            self.assertEqual(listed, {key for key in keys if key.startswith('settings.search.keywords.')}, name)

    def test_tabs_match_their_views(self):
        tabs = {}
        for section, body in re.findall(r'\n    (\w+): \[\n(.*?)\n    \]', self.search, re.S):
            tabs[section] = re.findall(r'name: "(\w+)"', body)
        system = (SHELL / 'panels/system/SystemView.qml').read_text(encoding='utf-8')
        theming = (SHELL / 'panels/theming/ThemingView.qml').read_text(encoding='utf-8')
        self.assertEqual(tabs['system'], json.loads(re.search(r'property var tabs: (\[.*?\])', system)[1]))
        self.assertEqual(tabs['appearance'], json.loads(re.search(r'property var cycle: (\[.*?\])', theming)[1]))

    def test_common_words_find_a_page_in_both_languages(self):
        # Words the issue (#213) asks to find, typed in either language: each starts a word of a keyword list or
        # of a section or tab title.
        for name, catalog in self.catalogs.items():
            settings = catalog['settings']
            texts = list(settings['sections'].values()) + list(catalog['theming']['tabs'].values())
            texts += [settings['system'][tab] for tab in ('about', 'updates', 'profiles', 'plugins', 'advanced')]

            def collect(branch):
                for value in branch.values():
                    if isinstance(value, dict):
                        collect(value)
                    else:
                        texts.append(value)
            collect(settings['search']['keywords'])
            words = set(re.findall(r'\w+', ' '.join(texts).lower()))
            for wanted in ('wifi', 'font', 'cursor', 'wallpaper', 'plugin', 'update', 'monitor', 'scale', 'volume'):
                with self.subTest(language=name, word=wanted):
                    self.assertTrue(any(word.startswith(wanted) for word in words), wanted)


if __name__ == '__main__':
    unittest.main()
