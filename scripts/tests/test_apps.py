#!/usr/bin/env python3
"""apps.py: desktop entries by id, the choice of Settings → Apps over the default, an app that is not installed giving way
to the first of its kind, and how each is started."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import apps  # noqa: E402


def entry(name, categories='', extra=''):
    return f'[Desktop Entry]\nType=Application\nName={name}\nExec={name.lower()}\nCategories={categories}\n{extra}'


class AppsTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        self.user, self.system = root / 'user/applications', root / 'system/applications'
        for directory in (self.user, self.system):
            directory.mkdir(parents=True)
        (self.system / 'kitty.desktop').write_text(entry('kitty', 'System;TerminalEmulator;'), encoding='utf-8')
        (self.system / 'zen-browser.desktop').write_text(entry('Zen Browser', 'Network;WebBrowser;'), encoding='utf-8')
        (self.system / 'brave.desktop').write_text(entry('Brave', 'Network;WebBrowser;'), encoding='utf-8')
        (self.system / 'hidden.desktop').write_text(entry('Hidden', 'WebBrowser;', 'Hidden=true'), encoding='utf-8')
        (self.system / 'org.gnome.Nautilus.desktop').write_text(entry('Files', 'Utility;FileManager;'), encoding='utf-8')
        # The user's own entry of an id wins over the system's.
        (self.user / 'kitty.desktop').write_text(entry('My kitty', 'TerminalEmulator;'), encoding='utf-8')
        self.config = root / 'shell.json'
        self.known = apps.entries([self.user, self.system])

    def choose(self, value):
        self.config.write_text(json.dumps({'defaultApps': value}), encoding='utf-8')

    def test_entries_by_id_the_first_directory_wins(self):
        self.assertEqual(self.known['kitty.desktop']['name'], 'My kitty')
        self.assertNotIn('hidden.desktop', self.known)

    def test_the_default_without_a_choice(self):
        self.assertEqual(apps.resolve('terminal', self.known, self.config), 'kitty.desktop')
        self.assertEqual(apps.resolve('files', self.known, self.config), 'org.gnome.Nautilus.desktop')

    def test_a_missing_default_gives_way_to_the_first_of_its_kind(self):
        # No Firefox here: Brave comes before Zen by name.
        self.assertEqual(apps.resolve('browser', self.known, self.config), 'brave.desktop')

    def test_the_choice_wins_and_a_missing_one_falls_back(self):
        self.choose({'browser': 'zen-browser.desktop'})
        self.assertEqual(apps.resolve('browser', self.known, self.config), 'zen-browser.desktop')
        self.choose({'browser': 'gone.desktop', 'terminal': ''})
        self.assertEqual(apps.resolve('browser', self.known, self.config), 'brave.desktop')
        self.assertEqual(apps.resolve('terminal', self.known, self.config), 'kitty.desktop')

    def test_a_command_choice_needs_its_program(self):
        with mock.patch('shutil.which', side_effect=lambda name: '/usr/bin/' + name if name == 'foot' else None):
            self.choose({'terminal': 'foot --server'})
            self.assertEqual(apps.resolve('terminal', self.known, self.config), 'foot --server')
            self.choose({'terminal': 'alacritty'})
            self.assertEqual(apps.resolve('terminal', self.known, self.config), 'kitty.desktop')
            # 1Password is not installed and no password manager is known here.
            self.assertIsNone(apps.resolve('passwords', self.known, self.config))

    def test_how_each_is_started(self):
        self.assertEqual(apps.command('kitty.desktop', self.known), ['gio', 'launch', str(self.user / 'kitty.desktop')])
        self.assertEqual(apps.command('1password --quick-access', self.known), ['1password', '--quick-access'])

    def test_window_classes_of_an_app(self):
        (self.system / 'zen.desktop').write_text(entry('Zen', 'WebBrowser;', 'StartupWMClass=zen-alpha'), encoding='utf-8')
        known = apps.entries([self.user, self.system])
        self.assertEqual(apps.window_classes('zen.desktop', known), {'zen', 'zen-alpha'})
        self.assertEqual(apps.window_classes('org.gnome.Nautilus.desktop', known), {'org.gnome.nautilus'})
        self.assertEqual(apps.window_classes('1password --quick-access', known), {'1password'})

    def test_the_most_recently_focused_window_comes_forward(self):
        clients = [{'class': 'firefox', 'address': '0x1', 'focusHistoryID': 3},
                   {'class': 'org.gnome.Nautilus', 'address': '0x2', 'focusHistoryID': 5},
                   {'class': 'org.gnome.Nautilus', 'address': '0x3', 'focusHistoryID': 1},
                   {'class': '1Password', 'address': '0x4', 'focusHistoryID': 0, 'mapped': False}]
        self.assertEqual(apps.open_window({'org.gnome.nautilus'}, clients), '0x3')
        self.assertIsNone(apps.open_window({'1password'}, clients))
        self.assertIsNone(apps.open_window({'kitty'}, None))

    def test_no_folder_without_a_terminal(self):
        self.assertIsNone(apps.terminal_folder(None))
        self.assertIsNone(apps.terminal_folder({'pid': -1}))

    def test_an_unreadable_settings_file_keeps_the_defaults(self):
        self.config.write_text('not json', encoding='utf-8')
        self.assertEqual(apps.chosen('terminal', self.config), 'kitty.desktop')


if __name__ == '__main__':
    unittest.main()
