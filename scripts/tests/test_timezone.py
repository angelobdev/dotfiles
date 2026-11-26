#!/usr/bin/env python3
"""timezone.py: the zones it lists with their offsets, and what it says when timedated refuses."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import timezone as helper  # noqa: E402

WINTER = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
SUMMER = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)


def completed(stdout='', stderr='', code=0):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class TimeZoneTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(helper, 'tr', side_effect=lambda key, args=(): key)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_offsets_follow_daylight_saving(self):
        self.assertEqual(helper.offset('Europe/Rome', WINTER), 60)
        self.assertEqual(helper.offset('Europe/Rome', SUMMER), 120)
        self.assertEqual(helper.offset('America/New_York', WINTER), -300)
        self.assertEqual(helper.offset('Asia/Kolkata', WINTER), 330)
        self.assertIsNone(helper.offset('Nowhere/Atlantis', WINTER))

    def test_listing_keeps_known_zones(self):
        answers = {'show': completed('America/New_York\n'), 'list-timezones': completed('Europe/Rome\nNowhere/Atlantis\nUTC\n')}
        with mock.patch.object(helper, 'run', side_effect=lambda command, timeout: answers[command[1]]):
            found = helper.listing(WINTER)
        self.assertEqual(found['current'], 'America/New_York')
        self.assertEqual(found['offset'], -300)
        self.assertEqual(found['zones'], [{'name': 'Europe/Rome', 'offset': 60}, {'name': 'UTC', 'offset': 0}])

    def test_an_unknown_zone_is_refused_before_timedated(self):
        with mock.patch.object(helper, 'run', return_value=completed('Europe/Rome\n')) as run:
            with self.assertRaisesRegex(ValueError, 'timezone.errors.unknown'):
                helper.set_zone('Europe/Atlantis')
        self.assertEqual([call.args[0][1] for call in run.call_args_list], ['list-timezones'])

    def test_a_refused_prompt_says_so(self):
        answers = {'list-timezones': completed('Europe/Rome\n'),
                   'set-timezone': completed(stderr='Failed to set time zone: Access denied\n', code=1)}
        with mock.patch.object(helper, 'run', side_effect=lambda command, timeout: answers[command[1]]):
            with self.assertRaisesRegex(ValueError, 'timezone.errors.denied'):
                helper.set_zone('Europe/Rome')

    def test_set_returns_the_new_zone(self):
        answers = {'list-timezones': completed('Europe/Rome\n'), 'set-timezone': completed(), 'show': completed('Europe/Rome\n')}
        with mock.patch.object(helper, 'run', side_effect=lambda command, timeout: answers[command[1]]) as run:
            self.assertEqual(helper.set_zone('Europe/Rome')['current'], 'Europe/Rome')
        self.assertIn(['timedatectl', 'set-timezone', 'Europe/Rome'], [call.args[0] for call in run.call_args_list])


if __name__ == '__main__':
    unittest.main()
