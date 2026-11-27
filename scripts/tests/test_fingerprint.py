#!/usr/bin/env python3
"""fingerprint.py: the arguments it takes, the listing without a reader, and fprintd's errors in words."""
from pathlib import Path
import sys
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import fingerprint  # noqa: E402


class FingerprintTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(fingerprint, 'tr', side_effect=lambda key, args=(): ' '.join([key, *map(str, args)]))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_ten_fingers_of_fprintd(self):
        self.assertEqual(len(fingerprint.FINGERS), 10)
        self.assertIn('right-index-finger', fingerprint.FINGERS)
        self.assertIn('left-thumb', fingerprint.FINGERS)

    def test_unknown_fingers_and_commands_are_refused(self):
        with mock.patch('builtins.print'):
            self.assertEqual(fingerprint.main(['enroll', 'nose']), 2)
            self.assertEqual(fingerprint.main(['format']), 2)

    def test_no_reader_lists_nothing(self):
        with mock.patch.object(fingerprint, 'bus', return_value=object()), mock.patch.object(fingerprint, 'device', return_value=''):
            self.assertEqual(fingerprint.listing(), {'device': '', 'fingers': [], 'stages': 0})

    def test_errors_in_words(self):
        self.assertEqual(fingerprint.message('GDBus.Error:net.reactivated.Fprint.Error.PermissionDenied: Not Authorized'), 'fingerprint.errors.denied')
        self.assertEqual(fingerprint.message('GDBus.Error:net.reactivated.Fprint.Error.AlreadyInUse: Device was already claimed'), 'fingerprint.errors.busy')
        self.assertEqual(fingerprint.message('GDBus.Error:x: broken'), 'fingerprint.errors.failed broken')


if __name__ == '__main__':
    unittest.main()
