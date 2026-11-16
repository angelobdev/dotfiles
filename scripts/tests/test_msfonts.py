#!/usr/bin/env python3
"""msfonts.py: the fonts of a Windows image or folder, copied for the user, without the emoji font unless asked."""
import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import msfonts  # noqa: E402

LISTING = '''
Listing archive: Win11.iso

--
Path = Win11.iso
Type = Udf
Physical Size = 5800000000

----------
Path = sources/install.wim
Folder = -
Size = 5368709120
Packed Size = 5368709120
Modified = 2026-04-01 10:00:00
'''


class MsfontsTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.fonts = self.folder / 'home/fonts/microsoft'
        self.enterContext(mock.patch.object(msfonts, 'FONTS', self.fonts))
        self.enterContext(mock.patch.object(msfonts, 'CACHE', self.folder / 'cache'))
        self.enterContext(mock.patch.object(msfonts, 'refresh'))
        self.enterContext(mock.patch.object(msfonts, 'tr', side_effect=lambda key, values=(): key))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def windows(self, root='Windows', fonts='Fonts'):
        folder = self.folder / 'disk' / root / fonts
        folder.mkdir(parents=True)
        for name in ('Arial.TTF', 'cambria.ttc', 'seguiemj.ttf', 'marlett.fon', 'desktop.ini'):
            (folder / name).write_text(name)
        return self.folder / 'disk'

    def installed(self):
        return sorted(path.name for path in self.fonts.iterdir())

    def test_a_fonts_folder_without_the_emoji_font(self):
        msfonts.install(self.windows() / 'Windows/Fonts')
        # Only font files, named in lower case, readable by the user whatever the source's mode.
        self.assertEqual(self.installed(), ['arial.ttf', 'cambria.ttc'])
        self.assertEqual((self.fonts / 'arial.ttf').stat().st_mode & 0o777, 0o644)
        msfonts.install(self.folder / 'disk/Windows/Fonts', emoji=True)
        self.assertEqual(self.installed(), ['arial.ttf', 'cambria.ttc', 'seguiemj.ttf'])

    def test_a_windows_partition_whatever_the_case_of_its_folders(self):
        msfonts.install(self.windows('WINDOWS', 'fonts'))
        self.assertEqual(self.installed(), ['arial.ttf', 'cambria.ttc'])

    def test_what_is_no_source_is_refused(self):
        (self.folder / 'notes.txt').write_text('')
        (self.folder / 'empty').mkdir()
        for source, error in (('missing', 'noSource'), ('notes.txt', 'unknownSource'), ('empty', 'unknownSource')):
            with self.assertRaisesRegex(ValueError, error):
                msfonts.install(self.folder / source)
        self.assertFalse(self.fonts.exists())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(msfonts.main(['install', str(self.folder / 'missing')]), 1)

    def test_remove_takes_only_the_fonts(self):
        msfonts.install(self.windows())
        (self.fonts / 'mine.txt').write_text('')
        msfonts.remove()
        self.assertEqual(self.installed(), ['mine.txt'])
        (self.fonts / 'mine.txt').unlink()
        msfonts.remove()
        self.assertFalse(self.fonts.exists())

    def test_an_image_with_several_editions_gives_the_fonts_of_the_first(self):
        asked = []

        def extract(archive, patterns, into):
            asked.append(patterns)
            into.mkdir(parents=True, exist_ok=True)
            if patterns[0].startswith('1/'):
                (into / 'calibri.ttf').write_text('')
            return sorted(into.iterdir())

        (self.folder / 'install.esd').write_text('')
        with mock.patch.object(msfonts, 'extract', side_effect=extract):
            msfonts.install(self.folder / 'install.esd')
        self.assertEqual(asked, [['1/Windows/Fonts/*.ttf', '1/Windows/Fonts/*.ttc', '1/Windows/Fonts/*.otf']])
        self.assertEqual(self.installed(), ['calibri.ttf'])
        # Nothing of the work is left in the cache.
        self.assertEqual(list((self.folder / 'cache').iterdir()), [])

    def test_an_iso_is_unpacked_only_with_room_for_its_image(self):
        iso = self.folder / 'Win11.iso'
        iso.write_text('')
        listing = subprocess.CompletedProcess([], 0, LISTING, '')
        with mock.patch.object(msfonts, 'seven_zip', return_value=listing):
            self.assertEqual(msfonts.image_in_iso(iso), ('sources/install.wim', 5 * msfonts.GIB))
            usage = mock.Mock(free=5 * msfonts.GIB)
            with mock.patch.object(msfonts.shutil, 'disk_usage', return_value=usage), mock.patch.object(msfonts, 'extract') as extract:
                with self.assertRaisesRegex(ValueError, 'noSpace'):
                    msfonts.install(iso)
                extract.assert_not_called()
        nothing = subprocess.CompletedProcess([], 0, LISTING.split('----------')[0] + '----------\n', '')
        with mock.patch.object(msfonts, 'seven_zip', return_value=nothing), self.assertRaisesRegex(ValueError, 'noImage'):
            msfonts.install(iso)

    @unittest.skipUnless(shutil.which('7z') or shutil.which('7zz'), '7z is not installed')
    def test_a_real_image_through_7z(self):
        # 7z writes a WIM with one edition, whose paths have no number: the second root.
        disk = self.windows()
        image = self.folder / 'install.wim'
        program = shutil.which('7z') or shutil.which('7zz')
        subprocess.run([program, 'a', '-twim', str(image), 'Windows'], cwd=disk, check=True, capture_output=True)
        msfonts.install(image)
        self.assertEqual(self.installed(), ['arial.ttf', 'cambria.ttc'])
        # The layout of a mounted ISO: the image under sources.
        (self.folder / 'mounted/Sources').mkdir(parents=True)
        shutil.move(image, self.folder / 'mounted/Sources/install.wim')
        msfonts.remove()
        msfonts.install(self.folder / 'mounted', emoji=True)
        self.assertEqual(self.installed(), ['arial.ttf', 'cambria.ttc', 'seguiemj.ttf'])


if __name__ == '__main__':
    unittest.main()
