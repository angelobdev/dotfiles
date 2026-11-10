#!/usr/bin/env python3
"""common.py: atomic replacement keeps permissions, follows or replaces links, and leaves nothing behind."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

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

    def test_a_private_file_gets_its_mode_whatever_it_had(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.json'
            path.write_text('old\n')
            os.chmod(path, 0o755)
            common.write_atomic(path, 'new\n', mode=0o600)
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


    def test_a_download_that_does_not_match_keeps_the_old_file(self):
        import hashlib
        import io
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'list.txt'
            target.write_text('old')
            body = b'new words'
            with mock.patch('urllib.request.urlopen', return_value=io.BytesIO(body)):
                with self.assertRaisesRegex(ValueError, 'no match'):
                    common.download('https://example.com/list', target, '0' * 64, mismatch='no match')
            self.assertEqual(target.read_text(), 'old')
            self.assertEqual(sorted(path.name for path in Path(folder).iterdir()), ['list.txt'])
            with mock.patch('urllib.request.urlopen', return_value=io.BytesIO(body)):
                with self.assertRaisesRegex(ValueError, 'too big'):
                    common.download('https://example.com/list', target, limit=4, too_large='too big')
            self.assertEqual(target.read_text(), 'old')
            with mock.patch('urllib.request.urlopen', return_value=io.BytesIO(body)):
                common.download('https://example.com/list', target, hashlib.sha256(body).hexdigest())
            self.assertEqual(target.read_bytes(), body)


class JobFileTests(unittest.TestCase):
    def test_a_json_object_or_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            self.assertEqual(common.read_json(path), {})
            for text, value in (('{"running": true}', {'running': True}), ('[1]', {}), ('{', {}), ('null', {})):
                path.write_text(text)
                self.assertEqual(common.read_json(path), value)

    def test_a_lock_is_held_only_while_another_holds_it(self):
        import fcntl
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / 'jobs/.x.lock'
            self.assertFalse(common.lock_held(lock))
            with lock.open('a') as handle:
                fcntl.flock(handle, fcntl.LOCK_EX)
                # Another open of the file: flock locks belong to the open file, as in another process.
                self.assertTrue(common.lock_held(lock))
            self.assertFalse(common.lock_held(lock))

    def test_the_last_lines_skip_empty_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'x.log'
            self.assertEqual(common.last_lines(log, 3), [])
            log.write_text('one\n\ntwo\n   \nthree\nfour\n')
            self.assertEqual(common.last_lines(log, 3), ['two', 'three', 'four'])


if __name__ == '__main__':
    unittest.main()
