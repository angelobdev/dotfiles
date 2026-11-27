#!/usr/bin/env python3
"""migrations.py: the order, once only, "not yet" stopping the queue, a failure stopping it, and a new install."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import migrations  # noqa: E402


class MigrationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        self.folder, self.state, self.log = root / 'migrations', root / 'state/migrations', root / 'state/migrations.log'
        self.folder.mkdir()
        self.ran = root / 'ran'
        for name, value in (('tr', lambda key, args=(): ' '.join([key, *map(str, args)])),):
            patcher = mock.patch.object(migrations, name, side_effect=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        notify = mock.patch.object(migrations, 'notify')
        self.notify = notify.start()
        self.addCleanup(notify.stop)

    def write(self, name, body):
        (self.folder / name).write_text(body)

    def run_all(self):
        return migrations.run(self.folder, self.state, self.log)

    def test_only_named_files_in_order(self):
        for name in ('202611280900-second.sh', '202611271200-first.py', 'README.md', '2026-bad.sh', '202611281000-Upper.sh'):
            self.write(name, '')
        self.assertEqual(migrations.migrations(self.folder), ['202611271200-first.py', '202611280900-second.sh'])

    def test_each_runs_once_in_order(self):
        self.write('202611271200-first.sh', f'echo first >> "{self.ran}"\n')
        self.write('202611280900-second.py', f'open({str(self.ran)!r}, "a").write("second\\n")\n')
        self.assertEqual(self.run_all(), 0)
        self.assertEqual(self.run_all(), 0)
        self.assertEqual(self.ran.read_text().split(), ['first', 'second'])
        self.assertEqual(migrations.pending(self.folder, self.state), [])
        self.assertIn('== 202611271200-first.sh (0)', self.log.read_text())

    def test_not_yet_stops_the_queue_without_an_error(self):
        self.write('202611271200-waits.sh', 'echo "needs jq"; exit 75\n')
        self.write('202611280900-later.sh', f'echo later >> "{self.ran}"\n')
        self.assertEqual(self.run_all(), 0)
        self.assertFalse(self.ran.exists())
        self.assertIn('needs jq', self.notify.call_args.args[0])
        self.assertEqual(migrations.pending(self.folder, self.state), ['202611271200-waits.sh', '202611280900-later.sh'])

    def test_a_failure_stops_the_queue_and_says_so(self):
        self.write('202611271200-broken.sh', 'echo "no such key" >&2; exit 3\n')
        self.write('202611280900-later.sh', f'echo later >> "{self.ran}"\n')
        self.assertEqual(self.run_all(), 1)
        self.assertFalse(self.ran.exists())
        self.assertIn('migrations.failed 202611271200-broken.sh no such key', self.notify.call_args.args[0])
        # Fixed in a later pull, it runs then.
        self.write('202611271200-broken.sh', 'exit 0\n')
        self.assertEqual(self.run_all(), 0)
        self.assertTrue(self.ran.exists())

    def test_a_new_install_marks_every_one_as_done(self):
        self.write('202611271200-first.sh', f'echo first >> "{self.ran}"\n')
        with mock.patch.object(migrations, 'FOLDER', self.folder), mock.patch.object(migrations, 'STATE', self.state):
            self.assertEqual(migrations.main(['mark-all']), 0)
        self.assertEqual(self.run_all(), 0)
        self.assertFalse(self.ran.exists())

    def test_the_repository_is_in_the_environment(self):
        self.write('202611271200-where.sh', f'echo "$DOTFILES_REPO" > "{self.ran}"\n')
        self.run_all()
        self.assertEqual(self.ran.read_text().strip(), str(migrations.REPO))


if __name__ == '__main__':
    unittest.main()
