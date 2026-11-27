#!/usr/bin/env python3
"""theme_import.py: an Omarchy colors.toml as a palette and terminal colours, its id, where it goes, and what remove takes."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import theme_core  # noqa: E402
import theme_import  # noqa: E402
import theme_paths  # noqa: E402

TOKYO = '''mode = "dark"
accent = "#7aa2f7"
selection = "#292e42"
muted = "#414868"
background = "#1a1b26"
dark_background = "#13141c"
darker_background = "#0e0e14"
lighter_background = "#24283b"
foreground = "#a9b1d6"
dark_foreground = "#565f89"
light_foreground = "#b4bee6"
bright_foreground = "#c0caf5"
red = "#f7768e"
yellow = "#e0af68"
green = "#9ece6a"
cyan = "#449dab"
blue = "#7aa2f7"
magenta = "#ad8ee6"
bright_red = "#ff7a93"
bright_cyan = "#0db9d7"
'''


class ImportTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        for name, value in (('CONFIG', self.root / 'config'), ('STATE', self.root / 'state')):
            patcher = mock.patch.object(theme_paths, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        dirs = mock.patch.object(theme_paths, 'THEME_DIRS', (self.root / 'config/themes', REPO / 'shell/.local/share/desktop/themes'))
        dirs.start()
        self.addCleanup(dirs.stop)
        translate = mock.patch.object(theme_import, 'tr', side_effect=lambda key, args=(): ' '.join([key, *map(str, args)]))
        translate.start()
        self.addCleanup(translate.stop)

    def source(self, name='omarchy-tokyo-night-theme', text=TOKYO, backgrounds=()):
        folder = self.root / 'source' / name
        (folder / 'backgrounds').mkdir(parents=True, exist_ok=True)
        (folder / 'colors.toml').write_text(text)
        for image in backgrounds:
            (folder / 'backgrounds' / image).write_bytes(b'x')
        return folder

    def test_the_palette_and_terminal_colours(self):
        import tomllib
        theme = theme_import.convert(tomllib.loads(TOKYO), 'Tokyo Night')
        palette = theme['palette']
        self.assertEqual((palette['bg'], palette['base'], palette['raised'], palette['fg']), ('#1a1b26', '#13141c', '#24283b', '#c0caf5'))
        self.assertEqual((palette['muted'], palette['dim'], palette['accent']), ('#b4bee6', '#565f89', '#7aa2f7'))
        self.assertEqual((palette['danger'], palette['success'], palette['warning'], palette['link']), ('#f7768e', '#9ece6a', '#e0af68', '#0db9d7'))
        # The darkest background reads best on the blue accent.
        self.assertEqual(palette['accentFg'], '#0e0e14')
        self.assertEqual(len(theme['ansi']), 16)
        self.assertEqual(theme['ansi'][:2], ['#292e42', '#f7768e'])
        # A bright colour the theme leaves out is its normal one.
        self.assertEqual(theme['ansi'][10], '#9ece6a')
        self.assertEqual(set(theme_core.REQUIRED) - set(palette), set())

    def test_a_light_theme(self):
        import tomllib
        light = TOKYO.replace('mode = "dark"', 'mode = "light"').replace('#1a1b26', '#f5f5f5')
        theme = theme_import.convert(tomllib.loads(light), 'Day')
        self.assertEqual((theme['mode'], theme['system']['gtkTheme']), ('light', 'adw-gtk3'))

    def test_without_its_basic_colours_no_theme(self):
        with self.assertRaisesRegex(ValueError, 'theme.errors.importColors'):
            theme_import.convert({'accent': '#123456'}, 'Broken')

    def test_ids_from_folder_and_repository_names(self):
        self.assertEqual(theme_import.identity('/x/omarchy-tokyo-night-theme'), 'tokyo-night')
        self.assertEqual(theme_import.identity('https://github.com/someone/omarchy-nord-theme.git'), 'nord')
        self.assertEqual(theme_import.identity('/x/Rose Pine/'), 'rose-pine')

    def test_an_import_with_its_backgrounds_loads_and_can_be_removed(self):
        theme_id = theme_import.install(self.source(backgrounds=('1-a.jpg', 'notes.txt')))
        self.assertEqual(theme_id, 'tokyo-night')
        target = self.root / 'config/themes/tokyo-night'
        theme = json.loads((target / 'theme.json').read_text())
        self.assertEqual(theme['wallpaperDirectories'], [str(target / 'backgrounds')])
        self.assertEqual(sorted(path.name for path in (target / 'backgrounds').iterdir()), ['1-a.jpg'])
        self.assertEqual(theme_core.load('tokyo-night')['name'], 'Tokyo Night')
        # Imported again: the earlier import is replaced.
        self.assertEqual(theme_import.install(self.source()), 'tokyo-night')
        theme_import.remove('tokyo-night')
        self.assertFalse(target.exists())

    def test_a_theme_of_your_own_is_neither_replaced_nor_removed(self):
        own = self.root / 'config/themes/tokyo-night'
        own.mkdir(parents=True)
        (own / 'theme.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'importExists'):
            theme_import.install(self.source())
        with self.assertRaisesRegex(ValueError, 'importNotImported'):
            theme_import.remove('tokyo-night')
        self.assertTrue(own.exists())

    def test_only_https_repositories(self):
        for url in ('git@github.com:a/b.git', 'https://example.com/a b', 'file:///etc'):
            with self.assertRaises(ValueError):
                theme_import.fetch(url, self.root / 'clone')


if __name__ == '__main__':
    unittest.main()
