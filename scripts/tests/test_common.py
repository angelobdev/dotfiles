#!/usr/bin/env python3
"""common.py: atomic replacement keeps permissions, follows or replaces links, and leaves nothing behind."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import common  # noqa: E402


class CommonTests(unittest.TestCase):
    def test_new_files_are_0644_and_existing_ones_keep_their_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested/file.json'
            common.write_atomic(path, 'one\n')
            self.assertEqual(path.read_text(), 'one\n')
            self.assertEqual(path.stat().st_mode & 0o777, 0o644)
            os.chmod(path, 0o600)
            common.write_atomic(path, 'two\n')
            self.assertEqual(path.read_text(), 'two\n')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_links_are_followed_or_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, link = root / 'target.conf', root / 'link.conf'
            target.write_text('old\n')
            link.symlink_to(target)
            common.write_atomic(link, 'through\n')
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_text(), 'through\n')
            common.write_atomic(link, 'own\n', follow=False)
            self.assertFalse(link.is_symlink())
            self.assertEqual(link.read_text(), 'own\n')
            self.assertEqual(target.read_text(), 'through\n')

    def test_a_failed_block_keeps_the_old_file_and_no_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'image.jpg'
            path.write_text('old')
            with self.assertRaises(RuntimeError):
                with common.replacing(path, suffix='.jpg') as temporary:
                    self.assertEqual(temporary.suffix, '.jpg')
                    temporary.write_text('partial')
                    raise RuntimeError
            self.assertEqual(path.read_text(), 'old')
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ['image.jpg'])


if __name__ == '__main__':
    unittest.main()
