#!/usr/bin/env python3
"""recording.py: an area to record must be well formed and lie on the display, in logical pixels."""
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import recording  # noqa: E402

# A 2880x1800 panel at scale 1.5 is 1920x1200 logical; on its side (transform 1) it is 1200x1920.
MONITOR = {'name': 'eDP-1', 'x': 0, 'y': 0, 'width': 2880, 'height': 1800, 'scale': 1.5, 'transform': 0}


class Reached(Exception):
    """The checks passed: the run went on to ask where videos go."""


class AreaTests(unittest.TestCase):
    def run_with(self, geometry, monitor=MONITOR):
        def run(command, **kwargs):
            if command[:3] == ['hyprctl', '-j', 'monitors']:
                return mock.Mock(stdout=json.dumps([monitor]))
            raise Reached
        arguments = ['recording.py', '--output', 'eDP-1'] + (['--geometry', geometry] if geometry is not None else [])
        with mock.patch.object(recording.sys, 'argv', arguments), mock.patch.object(recording.subprocess, 'run', side_effect=run), \
                mock.patch.object(recording, 'tr', side_effect=lambda key, values=(): key), mock.patch('sys.stderr'):
            try:
                recording.main()
            except Reached:
                return 'accepted'
            except SystemExit:
                return 'refused'
        return 'finished'

    def test_an_area_on_the_display_is_accepted(self):
        self.assertEqual(self.run_with(None), 'accepted')
        self.assertEqual(self.run_with('0,0 1920x1200'), 'accepted')
        self.assertEqual(self.run_with('100,50 640x480'), 'accepted')

    def test_an_area_past_the_logical_size_is_refused(self):
        # 2880 is the size in hardware pixels; at scale 1.5 the display ends at 1920.
        self.assertEqual(self.run_with('0,0 2880x1800'), 'refused')
        self.assertEqual(self.run_with('-1,0 100x100'), 'refused')
        self.assertEqual(self.run_with('1900,0 40x40'), 'refused')

    def test_a_rotated_display_swaps_width_and_height(self):
        rotated = dict(MONITOR, transform=1)
        self.assertEqual(self.run_with('0,0 1200x1920', rotated), 'accepted')
        self.assertEqual(self.run_with('0,0 1920x1200', rotated), 'refused')

    def test_a_malformed_area_is_refused(self):
        for geometry in ('0,0 0x10', '0 0 10x10', '0,0 10x10; rm -rf ~', 'a,b cxd'):
            with self.subTest(geometry=geometry):
                self.assertEqual(self.run_with(geometry), 'refused')


if __name__ == '__main__':
    unittest.main()
