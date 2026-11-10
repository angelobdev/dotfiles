#!/usr/bin/env python3
"""stow.py: the dry-run passes over files that apply would back up, and apply backs them up and links."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
STOW = REPO / 'scripts/stow.py'


@unittest.skipUnless(shutil.which('stow'), 'GNU Stow is not installed')
class StowTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.target = Path(self.directory.name) / 'home'
        self.target.mkdir()
        # Never the real state: apply writes its backups there.
        self.environment = {**os.environ, 'XDG_STATE_HOME': str(Path(self.directory.name) / 'state')}

    def stow(self, action):
        return subprocess.run([str(STOW), action, '--target', str(self.target)], capture_output=True, text=True,
                              env=self.environment, timeout=120)

    def in_the_way(self):
        # A file of the user's and a link of another dotfiles setup, both where the repository links.
        mine = self.target / '.config/kitty/kitty.conf'
        mine.parent.mkdir(parents=True)
        mine.write_text('mine\n')
        elsewhere = Path(self.directory.name) / 'other/settings.ini'
        elsewhere.parent.mkdir()
        elsewhere.write_text('other\n')
        theirs = self.target / '.config/gtk-3.0/settings.ini'
        theirs.parent.mkdir(parents=True)
        theirs.symlink_to(elsewhere)
        return mine, theirs

    def test_a_dry_run_over_files_in_the_way_succeeds_and_changes_nothing(self):
        mine, theirs = self.in_the_way()
        result = self.stow('dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stdout + result.stderr
        self.assertIn(f'Will back up on apply: {mine}', output)
        self.assertIn(f'Will back up on apply: {theirs}', output)
        self.assertNotIn('conflicts', output)
        # Only the paths in the way are left out of the simulation: a neighbour with the same ending still links.
        self.assertIn('LINK: .local/share/desktop/templates/kitty.conf.tpl', output)
        self.assertEqual(mine.read_text(), 'mine\n')
        self.assertTrue(theirs.is_symlink())
        self.assertFalse((Path(self.directory.name) / 'state').exists())

    def test_apply_backs_up_what_is_in_the_way_and_links_the_rest(self):
        mine, theirs = self.in_the_way()
        result = self.stow('apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mine.resolve(), REPO / 'kitty/.config/kitty/kitty.conf')
        self.assertEqual(theirs.resolve(), REPO / 'gtk/.config/gtk-3.0/settings.ini')
        backups = list((Path(self.directory.name) / 'state/dotfiles/backups').iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / '.config/kitty/kitty.conf').read_text(), 'mine\n')
        self.assertTrue((backups[0] / '.config/gtk-3.0/settings.ini').is_symlink())
        again = self.stow('dry-run')
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertNotIn('Will back up', again.stdout + again.stderr)


if __name__ == '__main__':
    unittest.main()
