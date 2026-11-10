#!/usr/bin/env python3
"""bar_visibility.py: a monitor counts as hiding its bar once every bar layer on it is fully transparent."""
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import bar_visibility  # noqa: E402


def layers(**monitors):
    # hyprctl layers -j: per monitor, levels of layers with their namespace and alpha.
    return {name: {'levels': {'2': [{'namespace': namespace, 'alpha': alpha} for namespace, alpha in entries]}}
            for name, entries in monitors.items()}


class HiddenBarTests(unittest.TestCase):
    def test_only_monitors_whose_bars_are_all_faded_out(self):
        listing = layers(**{'eDP-1': [('desktop-bar', 0.0), ('desktop-notifications', 1.0)],
                            'DP-2': [('desktop-bar', 0.0), ('desktop-bar', 0.4)],
                            'HDMI-A-1': [('desktop-bar', 1.0)],
                            'DP-3': [('wallpaper', 0.0)]})
        self.assertEqual(bar_visibility.hidden_bars(listing), ['eDP-1'])

    def test_a_layer_without_alpha_is_shown(self):
        self.assertEqual(bar_visibility.hidden_bars({'eDP-1': {'levels': {'2': [{'namespace': 'desktop-bar'}]}}}), [])
        self.assertEqual(bar_visibility.hidden_bars({'eDP-1': {}}), [])


if __name__ == '__main__':
    unittest.main()
