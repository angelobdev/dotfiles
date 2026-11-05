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
        self.assertTrue(allowed)
        self.assertEqual(lazy, allowed, 'shell.qml LazyPanels vs ShellState.panels')
        self.assertEqual(wrapper, allowed, 'desktop-shell toggle vs ShellState.panels')


if __name__ == '__main__':
    unittest.main()
