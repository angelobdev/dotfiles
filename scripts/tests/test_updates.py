#!/usr/bin/env python3
"""updates.py: dnf and Flatpak listings to updates.json, the Hyprland flag, errors kept apart."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import updates  # noqa: E402


def done(stdout='', code=0, stderr=''):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class UpdatesTests(unittest.TestCase):
    def test_dnf_lines_are_parsed_and_sorted(self):
        output = 'kernel\t7.2.14-200.fc44\tupdates\nhyprland\t0.56.3-1.fc44\tcopr:nett00n:hyprland\n\nnoise\n'
        self.assertEqual(updates.dnf_updates(output), [
            {'name': 'hyprland', 'version': '0.56.3-1.fc44', 'repo': 'copr:nett00n:hyprland'},
            {'name': 'kernel', 'version': '7.2.14-200.fc44', 'repo': 'updates'}])

    def test_flatpak_columns(self):
        self.assertEqual(updates.flatpak_updates('com.spotify.Client\t1.2.70\tflathub\n'),
                         [{'id': 'com.spotify.Client', 'version': '1.2.70', 'origin': 'flathub'}])

    def test_hyprland_sets_the_compositor_flag(self):
        replies = [done('hyprland\t0.56.3-1.fc44\tcopr\n'), done('')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check()
        self.assertTrue(result['compositor'])
        self.assertEqual((len(result['packages']), result['flatpaks'], result['errors']), (1, [], []))

    def test_a_failing_source_is_an_error_not_an_empty_list(self):
        replies = [done('', 1, 'Cannot download repomd.xml'), done('org.app\t2\tflathub\n')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check()
        self.assertEqual(result['errors'], ['updates.errors.dnf'])
        self.assertEqual(len(result['flatpaks']), 1)

    def test_a_failing_source_keeps_its_last_list(self):
        before = {'checked': 1.0, 'packages': [{'name': 'kernel', 'version': '1', 'repo': 'updates'}],
                  'flatpaks': [{'id': 'org.app', 'version': '1', 'origin': 'flathub'}]}
        replies = [done('', 1, 'Cannot download repomd.xml'), done('', 1, 'Unable to connect')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check(before)
        self.assertEqual((result['packages'], result['flatpaks'], result['checked']), (before['packages'], before['flatpaks'], 1.0))
        self.assertEqual(result['errors'], ['updates.errors.dnf', 'updates.errors.flatpak'])

    def test_a_failed_check_is_tried_again_later(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'updates.json'
            for errors, retried in (([], False), (['offline'], True)):
                with mock.patch.object(updates, 'STATE', state), mock.patch.object(updates, 'check', return_value={'errors': errors}), \
                        mock.patch.object(sys, 'argv', ['updates.py', 'check']), mock.patch.object(updates, 'retry_later') as retry:
                    updates.main()
                self.assertEqual(retry.called, retried)

    def test_check_writes_the_state_file(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'updates.json'
            with mock.patch.object(updates, 'STATE', state), mock.patch.object(updates, 'check', return_value={'packages': []}), \
                    mock.patch.object(sys, 'argv', ['updates.py', 'check']), mock.patch.object(updates, 'retry_later'):
                self.assertEqual(updates.main(), 0)
            self.assertEqual(json.loads(state.read_text()), {'packages': []})


if __name__ == '__main__':
    unittest.main()
