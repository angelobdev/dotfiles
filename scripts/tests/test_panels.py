#!/usr/bin/env python3
"""The panel names: ShellState.panels, the LazyPanels of shell.qml and desktop-shell toggle must agree."""
from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[2]
SHELL = REPO / 'quickshell/.config/quickshell/desktop'


class PanelTests(unittest.TestCase):
    def test_the_three_lists_name_the_same_panels(self):
        state = re.search(r'readonly property var panels: \[([^\]]*)\]', (SHELL / 'ShellState.qml').read_text())
        allowed = set(re.findall(r'"([a-z]+)"', state[1]))
        lazy = set(re.findall(r'LazyPanel \{\s*(?:id: \w+\s*)?name: "([a-z]+)"', (SHELL / 'shell.qml').read_text()))
        toggle = re.search(r'toggle\)\s*case "\$\{2:-\}" in ([a-z|]+)\)', (REPO / 'shell/.local/bin/desktop-shell').read_text())
        wrapper = set(toggle[1].split('|'))
        # Former panels that are now a section of another (ShellState.aliases) stay accepted by desktop-shell.
        aliases = re.search(r'readonly property var aliases: \(\{(.*?)\n        \}\)', (SHELL / 'ShellState.qml').read_text(), re.S)
        renamed = set(re.findall(r'^            (\w+): \{', aliases[1], re.M))
        self.assertTrue(allowed)
        self.assertTrue(renamed)
        self.assertFalse(renamed & allowed, 'an alias is also a panel')
        self.assertEqual(lazy, allowed, 'shell.qml LazyPanels vs ShellState.panels')
        self.assertEqual(wrapper, allowed | renamed, 'desktop-shell toggle vs ShellState.panels and aliases')

    def test_no_method_is_named_after_a_javascript_global(self):
        # QML refuses such a method ("Illegal method name") and the whole file fails to load: a NetworkView with
        # escape() took the shell down on 2026-11-06.
        globals_ = {'escape', 'unescape', 'eval', 'isNaN', 'isFinite', 'parseInt', 'parseFloat', 'encodeURI',
                    'decodeURI', 'encodeURIComponent', 'decodeURIComponent'}
        for path in SHELL.rglob('*.qml'):
            for name in re.findall(r'^\s*function (\w+)\(', path.read_text(), re.M):
                self.assertNotIn(name, globals_, f'{path.relative_to(SHELL)}: function {name}()')

    def test_every_singleton_of_services_is_registered(self):
        # A singleton missing from services/qmldir is not found by the files that use it, and the shell does not
        # start.
        registered = set(re.findall(r'^singleton (\w+) ', (SHELL / 'services/qmldir').read_text(), re.M))
        for path in (SHELL / 'services').glob('*.qml'):
            if 'pragma Singleton' in path.read_text():
                self.assertIn(path.stem, registered, f'services/{path.name} is not in services/qmldir')


if __name__ == '__main__':
    unittest.main()
