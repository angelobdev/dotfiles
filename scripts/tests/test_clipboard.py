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
        for patcher in (mock.patch.dict(os.environ, {'XDG_CACHE_HOME': folder.name, 'XDG_RUNTIME_DIR': folder.name}),
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
                                           {'id': '11', 'preview': '[[ binary data 3 KiB png 10x10 ]]', 'image': True,
                                            'size': '3 KiB', 'format': 'png', 'width': 10, 'height': 10}])

    def test_an_image_without_type_or_size_still_has_its_size_in_bytes(self):
        self.assertEqual(clipboard.describe('4', '[[ binary data 812 B ]]'),
                         {'id': '4', 'preview': '[[ binary data 812 B ]]', 'image': True, 'size': '812 B'})
        self.assertEqual(clipboard.describe('5', '[[ binary data 1.5 MiB jpeg 4000x3000 ]]')['width'], 4000)
        self.assertNotIn('size', clipboard.describe('6', 'binary data, not really'))

    def test_a_thumbnail_is_made_once_privately_and_listed_by_id(self):
        def run(command, **kwargs):
            if command[0] == 'magick':
                Path(command[-1].removeprefix('png:')).write_bytes(b'thumbnail')
            return mock.Mock(returncode=0, stdout=b'image bytes', stderr=b'')
        with mock.patch.object(clipboard.sys, 'argv', ['clipboard.py', 'thumbnails', '7']), \
                mock.patch.object(clipboard.subprocess, 'run', side_effect=run) as calls, \
                mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            clipboard.main()
        path = Path(json.loads(out.getvalue())['7'])
        self.assertEqual(path, clipboard.thumbnail_folder() / '7.png')
        self.assertEqual(path.read_bytes(), b'thumbnail')
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(calls.call_args_list[0].args[0], ['cliphist', 'decode', '7'])
        self.assertEqual(calls.call_args_list[1].kwargs['input'], b'image bytes')
        self.assertEqual([entry.name for entry in path.parent.iterdir()], ['7.png'])
        # Made already: no second decode.
        out, run_again = self.run_main('thumbnails', '7')
        self.assertEqual(json.loads(out), {'7': str(path)})
        run_again.assert_not_called()

    def test_an_entry_that_does_not_decode_has_no_thumbnail(self):
        failure = clipboard.subprocess.CalledProcessError(1, ['cliphist'])
        with mock.patch.object(clipboard.sys, 'argv', ['clipboard.py', 'thumbnails', '8']), \
                mock.patch.object(clipboard.subprocess, 'run', side_effect=failure), \
                mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            clipboard.main()
        self.assertEqual(json.loads(out.getvalue()), {})
        with mock.patch('sys.stderr'), self.assertRaises(SystemExit):
            self.run_main('thumbnails', '8', '../x')

    def test_thumbnails_go_with_their_entries(self):
        folder = clipboard.thumbnail_folder()
        folder.mkdir(parents=True)
        for name in ('11.png', '12.png', '13.png', '.writing.png'):
            (folder / name).write_bytes(b'x')
        self.run_main('list', stdout=b'11\t[[ binary data 3 KiB png 10x10 ]]\n12\ttext\n')
        self.assertEqual(sorted(entry.name for entry in folder.iterdir()), ['.writing.png', '11.png'])
        self.run_main('delete', '11')
        self.assertEqual(sorted(entry.name for entry in folder.iterdir()), ['.writing.png'])
        (folder / '14.png').write_bytes(b'x')
        self.run_main('clear')
        self.assertEqual(list(folder.iterdir()), [])

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
