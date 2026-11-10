#!/usr/bin/env python3
"""clipboard.py: the history as JSON entries, ids that are only digits, and an empty history that is no error."""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import clipboard  # noqa: E402


class ClipboardTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        for patcher in (mock.patch.dict(os.environ, {'XDG_CACHE_HOME': folder.name}),
                        mock.patch.object(clipboard, 'tr', side_effect=lambda key, values=(): key)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *arguments, stdout=b'', stderr=b'', code=0):
        reply = mock.Mock(returncode=code, stdout=stdout, stderr=stderr, args=['cliphist'])
        with mock.patch.object(clipboard.sys, 'argv', ['clipboard.py', *arguments]), \
                mock.patch.object(clipboard.subprocess, 'run', return_value=reply) as run, \
                mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            clipboard.main()
        return out.getvalue(), run

    def test_the_history_lists_ids_previews_and_images(self):
        listing = '12\thello world\n11\t[[ binary data 3 KiB png 10x10 ]]\nnot an entry\nx\tbad id\n'.encode()
        out, _ = self.run_main('list', stdout=listing)
        self.assertEqual(json.loads(out), [{'id': '12', 'preview': 'hello world', 'image': False},
                                           {'id': '11', 'preview': '[[ binary data 3 KiB png 10x10 ]]', 'image': True}])

    def test_an_empty_history_is_an_empty_list(self):
        out, _ = self.run_main('list', stderr=b'please store something first', code=1)
        self.assertEqual(json.loads(out), [])
        with self.assertRaises(clipboard.subprocess.CalledProcessError):
            self.run_main('list', stderr=b'database is locked', code=1)

    def test_an_id_is_digits_only(self):
        for value in (None, '', '12; rm -rf ~', '-1', '1a'):
            with self.subTest(value=value), mock.patch('sys.stderr'), self.assertRaises(SystemExit):
                self.run_main('delete', *([value] if value is not None else []))
        _, run = self.run_main('delete', '12')
        self.assertEqual(run.call_args.kwargs['input'], b'12\n')

    def test_the_cache_folder_is_private(self):
        self.run_main('list')
        self.assertEqual((Path(os.environ['XDG_CACHE_HOME']) / 'cliphist').stat().st_mode & 0o777, 0o700)


if __name__ == '__main__':
    unittest.main()
