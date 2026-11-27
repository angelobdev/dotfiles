#!/usr/bin/env python3
"""install_snapshots.py: a pre and a post snapshot around a system update, only with snapper on btrfs, never on top of
snap-pac, and a failure that never stops the update."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
SANDBOX = tempfile.TemporaryDirectory()
os.environ['XDG_STATE_HOME'] = SANDBOX.name
sys.path.insert(0, str(REPO / 'scripts/install'))
import install_plan  # noqa: E402
import install_snapshots  # noqa: E402


def done(stdout='', code=0, stderr=''):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.config = self.root / 'root'
        self.config.write_text('')
        for name, value in (('CONFIG', self.config), ('SNAP_PAC', self.root / 'no-hook')):
            patcher = mock.patch.object(install_snapshots, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for patcher in (mock.patch('shutil.which', return_value='/usr/bin/snapper'), mock.patch('builtins.print'),
                        mock.patch.object(install_plan, 'query', return_value=done('btrfs\n'))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_a_pair_around_the_update(self):
        with mock.patch('subprocess.run', side_effect=[done('12\n'), done('13\n')]) as run:
            number = install_snapshots.before()
            install_snapshots.after(number)
        self.assertEqual(number, '12')
        pre, post = (call.args[0] for call in run.call_args_list)
        self.assertEqual(pre[:6], ('sudo', 'snapper', '-c', 'root', 'create', '--type'))
        self.assertIn('pre', pre)
        self.assertEqual(post[post.index('--pre-number') + 1], '12')

    def test_nothing_without_btrfs_or_snapper(self):
        with mock.patch.object(install_plan, 'query', return_value=done('xfs\n')), mock.patch('subprocess.run') as run:
            self.assertEqual(install_snapshots.before(), '')
        run.assert_not_called()
        with mock.patch('shutil.which', return_value=None), mock.patch('subprocess.run') as run:
            self.assertEqual(install_snapshots.before(), '')
        run.assert_not_called()

    def test_snap_pac_takes_them_itself(self):
        hook = self.root / 'hook'
        hook.write_text('')
        with mock.patch.object(install_snapshots, 'SNAP_PAC', hook), mock.patch('subprocess.run') as run:
            self.assertEqual(install_snapshots.before(), '')
        run.assert_not_called()

    def test_the_first_update_makes_the_config(self):
        self.config.unlink()
        with mock.patch('subprocess.run', side_effect=[done(), done(), done('1\n')]) as run:
            self.assertEqual(install_snapshots.before(), '1')
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0][-2:], ('create-config', '/'))
        self.assertIn('NUMBER_LIMIT=5', commands[1])

    def test_a_failed_snapshot_never_stops_the_update(self):
        with mock.patch('subprocess.run', return_value=done('', 1, 'no space')):
            self.assertEqual(install_snapshots.before(), '')
        with mock.patch('subprocess.run') as run:
            install_snapshots.after('')
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
