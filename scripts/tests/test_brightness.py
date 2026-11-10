#!/usr/bin/env python3
"""brightness.py: what a backend may name, DDC/CI readings, and the laptop panel found without a mapping."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import brightness  # noqa: E402


class Sandbox(unittest.TestCase):
    """A /sys/class/backlight of its own, and catalog keys instead of translated text."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.backlight = Path(folder.name)
        for patcher in (mock.patch.object(brightness, 'BACKLIGHT', self.backlight),
                        mock.patch.object(brightness, 'tr', side_effect=lambda key, values=(): key)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def device(self, name, current, maximum):
        folder = self.backlight / name
        folder.mkdir()
        (folder / 'brightness').write_text(f'{current}\n')
        (folder / 'max_brightness').write_text(f'{maximum}\n')


class BackendTests(Sandbox):
    def test_a_backlight_is_a_plain_name_that_exists(self):
        self.device('intel_backlight', 50, 100)
        self.assertEqual(brightness.validate_backend({'type': 'backlight', 'device': 'intel_backlight', 'extra': 1}),
                         {'type': 'backlight', 'device': 'intel_backlight'})
        for device in ('..', '.', '../intel_backlight', 'a/b', '', 3):
            with self.subTest(device=device), self.assertRaises(ValueError) as caught:
                brightness.validate_backend({'type': 'backlight', 'device': device})
            self.assertEqual(str(caught.exception), 'brightness.errors.invalidBacklight')
        with self.assertRaises(ValueError) as caught:
            brightness.validate_backend({'type': 'backlight', 'device': 'acpi_video0'})
        self.assertEqual(str(caught.exception), 'brightness.errors.backlightUnavailable')

    def test_a_ddc_bus_is_a_number_and_needs_ddcutil(self):
        with mock.patch.object(brightness.shutil, 'which', return_value='/usr/bin/ddcutil'):
            self.assertEqual(brightness.validate_backend({'type': 'ddc', 'bus': 7}), {'type': 'ddc', 'bus': 7})
            for bus in (True, -1, 65536, '7', None):
                with self.subTest(bus=bus), self.assertRaises(ValueError):
                    brightness.validate_backend({'type': 'ddc', 'bus': bus})
        with mock.patch.object(brightness.shutil, 'which', return_value=None), self.assertRaises(ValueError) as caught:
            brightness.validate_backend({'type': 'ddc', 'bus': 7})
        self.assertEqual(str(caught.exception), 'brightness.errors.ddcutilMissing')
        for backend in (None, [], {'type': 'other'}):
            with self.subTest(backend=backend), self.assertRaises(ValueError):
                brightness.validate_backend(backend)

    def test_readings_are_percentages_of_the_maximum(self):
        self.device('intel_backlight', 9600, 19200)
        self.assertEqual(brightness.read_backend({'type': 'backlight', 'device': 'intel_backlight'}), (50, 19200))
        with mock.patch.object(brightness.shutil, 'which', return_value='/usr/bin/ddcutil'), \
                mock.patch.object(brightness, 'run', return_value='VCP 10 C 30 120\n') as run:
            self.assertEqual(brightness.read_backend({'type': 'ddc', 'bus': 4}), (25, 120))
        run.assert_called_once_with(['ddcutil', '--bus', '4', 'getvcp', '10', '--terse'])
        with mock.patch.object(brightness.shutil, 'which', return_value='/usr/bin/ddcutil'), \
                mock.patch.object(brightness, 'run', return_value='VCP 10 ERR\n'), self.assertRaises(ValueError) as caught:
            brightness.read_backend({'type': 'ddc', 'bus': 4})
        self.assertEqual(str(caught.exception), 'brightness.errors.ddcUnsupported')

    def test_a_new_level_stays_between_1_and_100_percent(self):
        self.device('intel_backlight', 10, 100)
        with mock.patch.object(brightness, 'run') as run:
            brightness.set_brightness({'type': 'backlight', 'device': 'intel_backlight'}, 0)
            brightness.set_brightness({'type': 'backlight', 'device': 'intel_backlight'}, 250)
        self.assertEqual([call.args[0][-1] for call in run.call_args_list], ['1%', '100%'])
        with self.assertRaises(ValueError):
            brightness.set_brightness({'type': 'backlight', 'device': 'intel_backlight'}, float('nan'))


class DiscoverTests(Sandbox):
    def test_the_laptop_panel_gets_the_only_backlight(self):
        self.device('intel_backlight', 50, 100)
        rows = brightness.discover(['eDP-1', 'DP-2', 'eDP-1'], {})
        self.assertEqual([row['name'] for row in rows], ['eDP-1', 'DP-2'])
        self.assertEqual((rows[0]['available'], rows[0]['percent'], rows[0]['backend']),
                         (True, 50, {'type': 'backlight', 'device': 'intel_backlight'}))
        self.assertEqual((rows[1]['available'], rows[1]['error']), (False, 'brightness.errors.configureBackend'))

    def test_with_two_backlights_nobody_can_tell_which_one(self):
        self.device('intel_backlight', 50, 100)
        self.device('nvidia_0', 50, 100)
        self.assertFalse(brightness.discover(['eDP-1'], {})[0]['available'])
        mapped = brightness.discover(['eDP-1'], {'eDP-1': {'type': 'backlight', 'device': 'nvidia_0'}})
        self.assertEqual(mapped[0]['backend'], {'type': 'backlight', 'device': 'nvidia_0'})

    def test_a_list_that_is_not_one_is_refused(self):
        for names, mappings in (('eDP-1', {}), ([1], {}), (['eDP-1'], [])):
            with self.subTest(names=names), self.assertRaises(ValueError):
                brightness.discover(names, mappings)


if __name__ == '__main__':
    unittest.main()
