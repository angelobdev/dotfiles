#!/usr/bin/env python3
"""store.py: unpacking other people's archives safely, finding the themes in them, and what it may remove."""
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
import zipfile

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import store  # noqa: E402


def add(archive, name, data=b'', link=None):
    info = tarfile.TarInfo(name)
    if link is not None:
        info.type, info.linkname = tarfile.SYMTYPE, link
    else:
        info.size = len(data)
    archive.addfile(info, io.BytesIO(data) if link is None else None)


class UnpackTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def test_tar_members_that_leave_the_folder_are_dropped(self):
        path = self.root / 'theme.tar'
        with tarfile.open(path, 'w') as archive:
            add(archive, 'Theme/index.theme', b'[Icon Theme]\nDirectories=16x16/apps\n')
            add(archive, 'Theme/16x16/apps/a.svg', b'<svg/>')
            add(archive, 'Theme/16x16/apps/b.svg', link='a.svg')
            add(archive, 'Theme/16x16/apps/c.svg', link='/etc/passwd')
            add(archive, '../outside.txt', b'no')
        target = self.root / 'out'
        target.mkdir()
        store.unpack(path, target)
        self.assertTrue((target / 'Theme/16x16/apps/b.svg').is_symlink())
        self.assertFalse((target / 'Theme/16x16/apps/c.svg').exists())
        self.assertFalse((self.root / 'outside.txt').exists())

    def test_a_zip_that_leaves_the_folder_is_refused(self):
        path = self.root / 'theme.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('Theme/cursors/left_ptr', b'x')
            archive.writestr('../evil', b'x')
        target = self.root / 'out'
        target.mkdir()
        with self.assertRaises(ValueError):
            store.unpack(path, target)
        self.assertFalse((self.root / 'evil').exists())

    def test_something_else_is_refused(self):
        path = self.root / 'script.sh'
        path.write_text('#!/bin/sh\n')
        with self.assertRaises(ValueError):
            store.unpack(path, self.root)


class ThemeTests(unittest.TestCase):
    def test_themes_are_found_at_any_depth_and_only_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'pack/Dark/cursors').mkdir(parents=True)
            (root / 'pack/Light/cursors').mkdir(parents=True)
            (root / 'pack/Icons').mkdir(parents=True)
            (root / 'pack/Icons/index.theme').write_text('[Icon Theme]\nName=Icons\nDirectories=16x16/apps\n')
            (root / 'pack/Cursorish').mkdir()
            (root / 'pack/Cursorish/index.theme').write_text('[Icon Theme]\nInherits=Adwaita\n')
            self.assertEqual([path.name for path in store.themes_in(root, 'cursors')], ['Dark', 'Light'])
            self.assertEqual([path.name for path in store.themes_in(root, 'icons')], ['Icons'])


class InstallTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.archive = self.root / 'pack.tar.gz'
        with tarfile.open(self.archive, 'w:gz') as archive:
            add(archive, 'Pointer/cursors/left_ptr', b'x')
            add(archive, 'Pointer/index.theme', b'[Icon Theme]\nName=Pointer\n')
        for patcher in (mock.patch.object(store, 'ICONS', self.root / 'icons'), mock.patch.object(store, 'LEDGER', self.root / 'store.json'),
                        mock.patch.object(store, 'tr', side_effect=lambda key, args=(): key)):
            patcher.start()
            self.addCleanup(patcher.stop)
        item = {'id': 7, 'name': 'Pointer', 'downloadlink1': 'https://example.com/pack.tar.gz', 'downloadname1': 'pack.tar.gz', 'downloadmd5sum1': ''}
        fetch = mock.patch.object(store, 'fetch_json', return_value={'data': [item]})
        fetch.start()
        self.addCleanup(fetch.stop)
        get = mock.patch.object(store, 'download', side_effect=lambda url, destination, md5: destination.write_bytes(self.archive.read_bytes()))
        get.start()
        self.addCleanup(get.stop)

    def test_install_keeps_the_theme_and_notes_it(self):
        self.assertEqual(store.install('cursors', 7, 1), {'installed': ['Pointer']})
        self.assertTrue((self.root / 'icons/Pointer/cursors/left_ptr').is_file())
        self.assertEqual(json.loads((self.root / 'store.json').read_text())['Pointer']['id'], 7)

    def test_a_theme_from_elsewhere_is_never_replaced_or_removed(self):
        (self.root / 'icons/Pointer').mkdir(parents=True)
        (self.root / 'icons/Pointer/mine').write_text('mine')
        with self.assertRaises(ValueError):
            store.install('cursors', 7, 1)
        self.assertTrue((self.root / 'icons/Pointer/mine').exists())
        with self.assertRaises(ValueError):
            store.remove('Pointer')

    def test_remove_takes_only_what_the_store_installed(self):
        store.install('cursors', 7, 1)
        self.assertEqual(store.remove('Pointer'), {'removed': 'Pointer'})
        self.assertFalse((self.root / 'icons/Pointer').exists())
        self.assertEqual(json.loads((self.root / 'store.json').read_text()), {})



class DownloadTests(unittest.TestCase):
    def response(self, data):
        response = mock.MagicMock()
        response.__enter__.return_value = io.BytesIO(data)
        return response

    def test_the_checksum_is_checked_when_the_store_gives_one(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(store, 'tr', side_effect=lambda key, args=(): key):
            target = Path(folder) / 'x'
            with mock.patch('urllib.request.urlopen', return_value=self.response(b'data')):
                store.download('https://example.com/x', target, '8d777f385d3dfec8815d20f7496026dc')
            self.assertEqual(target.read_bytes(), b'data')
            with mock.patch('urllib.request.urlopen', return_value=self.response(b'data')), self.assertRaises(ValueError):
                store.download('https://example.com/x', target, '0' * 32)

    def test_a_download_over_the_limit_stops(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(store, 'tr', side_effect=lambda key, args=(): key), \
                mock.patch.object(store, 'MAX_DOWNLOAD', 3), mock.patch('urllib.request.urlopen', return_value=self.response(b'data')):
            with self.assertRaises(ValueError):
                store.download('https://example.com/x', Path(folder) / 'x', '')


if __name__ == '__main__':
    unittest.main()
