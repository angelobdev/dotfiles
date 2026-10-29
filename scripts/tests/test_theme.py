#!/usr/bin/env python3
"""Graphite rendered by theme.py must match the fallbacks the stowed configs keep."""
import json
from pathlib import Path
import re
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import theme  # noqa: E402

TEMPLATES = REPO / 'shell/.local/share/desktop/templates'
GRAPHITE = json.loads((REPO / 'shell/.local/share/desktop/themes/graphite/theme.json').read_text(encoding='utf-8'))


class GraphiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = theme.render_all(GRAPHITE, TEMPLATES)

    def test_hyprlock_matches_the_stowed_fallback(self):
        self.assertEqual(self.out['hyprlock.conf'], (REPO / 'hyprlock/.config/hypr/hyprlock.conf').read_text(encoding='utf-8'))

    def test_qt_matches_the_stowed_schemes(self):
        for version in ('qt5ct', 'qt6ct'):
            self.assertEqual(self.out['qt-colors.conf'], (REPO / f'qt/.config/{version}/colors/desktop.conf').read_text(encoding='utf-8'))

    def test_kitty_matches_the_values_in_kitty_conf(self):
        stowed = {}
        for line in (REPO / 'kitty/.config/kitty/kitty.conf').read_text(encoding='utf-8').splitlines():
            if line and not line.startswith('#') and not line.startswith('include '):
                key, _, value = line.partition(' ')
                stowed[key] = value.strip()
        for line in self.out['kitty.conf'].splitlines():
            if line and not line.startswith('#'):
                key, _, value = line.partition(' ')
                self.assertEqual(stowed.get(key), value.strip(), key)

    def test_quickshell_matches_the_theme_defaults(self):
        source = (REPO / 'quickshell/.config/quickshell/desktop/Theme.qml').read_text(encoding='utf-8')
        defaults = dict(re.findall(r'^\s+property (?:color|string) (\w+): "([^"]+)"', source, re.M))
        rendered = json.loads(self.out['quickshell.json'])
        self.assertEqual(set(rendered), set(defaults))
        for key, value in rendered.items():
            self.assertEqual(value.lower(), defaults[key].lower(), key)

    def test_hyprland_matches_the_lua_defaults(self):
        source = (REPO / 'hypr/.config/hypr/config/theme.lua').read_text(encoding='utf-8')
        defaults = dict(re.findall(r'^\s+(\w+) = (0x[0-9a-f]{8}),', source, re.M))
        rendered = dict(re.findall(r'^\s+(\w+) = (0x[0-9a-f]{8}),', self.out['hyprland.lua'], re.M))
        self.assertEqual(rendered, defaults)

    def test_gtk_defines_every_colour(self):
        names = re.findall(r'^@define-color (\w+) #[0-9a-f]{6};$', self.out['gtk.css'], re.M)
        self.assertEqual(len(names), 37)
        self.assertNotIn('{{', self.out['gtk.css'])


class RendererTests(unittest.TestCase):
    def test_filters(self):
        values = {'c': '#11223344', 'o': '#112233'}
        self.assertEqual(theme.render('{{ c | hex }}', values, 't'), '#112233')
        self.assertEqual(theme.render('{{ c | rgba }} {{ o | rgba }} {{ o | rgba:cc }}', values, 't'), '11223344 112233ff 112233cc')
        self.assertEqual(theme.render('{{ c | qt }} {{ o | qt }} {{ o | qt:ff }}', values, 't'), '#44112233 #112233 #ff112233')
        self.assertEqual(theme.render('{{ c | hypr }} {{ c | hexrgba }}', values, 't'), '0x44112233 0x11223344')

    def test_unknown_values_and_bad_colours_fail(self):
        with self.assertRaises(ValueError):
            theme.render('{{ missing }}', {}, 't')
        with self.assertRaises(ValueError):
            theme.render('{{ group }}', {'group': {'a': 1}}, 't')
        with self.assertRaises(ValueError):
            theme.render('{{ c | hex }}', {'c': 'red'}, 't')

    def test_theme_names_are_checked(self):
        with self.assertRaises(ValueError):
            theme.theme_path('../etc')


if __name__ == '__main__':
    unittest.main()
