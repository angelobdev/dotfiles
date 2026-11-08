#!/usr/bin/env python3
"""jobs.py: background operations from Settings, by name, behind one pkexec prompt when they need root."""
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import jobs  # noqa: E402


class JobTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        for patcher in (mock.patch.object(jobs, 'JOBS', Path(folder.name)),
                        mock.patch.object(jobs, 'tr', side_effect=lambda key, args=(): ' '.join([key, *map(str, args)]))):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_job(self, arguments, code=0, line='Done.'):
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if hasattr(kwargs.get('stdout'), 'write'):
                kwargs['stdout'].write(line + '\n')
            return subprocess.CompletedProcess(command, code)

        with mock.patch('subprocess.run', side_effect=run):
            status = jobs.main(arguments)
        return status, calls

    def test_a_job_as_the_user(self):
        status, calls = self.run_job(['run', 'agent-install', '--title', 'Install Codex', '--', 'sh', '-c', 'npm install'])
        self.assertEqual(status, 0)
        self.assertEqual(calls[0], ['sh', '-c', 'npm install'])
        self.assertEqual(calls[1][0], 'notify-send')
        self.assertIn('Install Codex', calls[1])
        value = jobs.status('agent-install')
        self.assertEqual((value['running'], value['status'], value['log']), (False, 0, ['Done.']))

    def test_root_goes_through_the_broker(self):
        _, calls = self.run_job(['run', 'profile', '--root', '--', 'install-desktop.py', 'apply'])
        self.assertEqual(calls[0][1:], [str(jobs.HERE / 'privileged.py'), 'run', 'install-desktop.py', 'apply'])
        # No title, no notification.
        self.assertEqual(len(calls), 1)

    def test_a_failure_names_the_last_line(self):
        status, calls = self.run_job(['run', 'profile', '--title', 'Remove media', '--', 'false'], code=3, line='Authentication was cancelled.')
        self.assertEqual(status, 3)
        self.assertIn('jobs.failed Authentication was cancelled.', calls[-1])
        self.assertEqual(jobs.status('profile')['status'], 3)

    def test_one_at_a_time_per_name(self):
        _, _, lock = jobs.paths('profile')
        jobs.JOBS.mkdir(parents=True, exist_ok=True)
        with lock.open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.assertEqual(self.run_job(['run', 'profile', '--', 'true']), (1, []))
            # Another name runs.
            self.assertEqual(self.run_job(['run', 'other', '--', 'true'])[0], 0)
            jobs.paths('profile')[0].write_text(json.dumps({'running': True}))
            self.assertTrue(jobs.status('profile')['running'])
        # Its lock is gone without a result: it stopped.
        self.assertEqual(jobs.status('profile')['status'], -1)

    def test_names_and_arguments(self):
        for arguments in (['run', '../x', '--', 'true'], ['run', 'Up', '--', 'true']):
            with self.assertRaises(ValueError):
                self.run_job(arguments)
        import contextlib
        import io
        for arguments in (['run', 'x', '--'], ['run', 'x', '--bogus', '--', 'true'], ['run', 'x', 'true'], ['nothing']):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.run_job(arguments), (2, []))


if __name__ == '__main__':
    unittest.main()
