#!/usr/bin/env python3
"""globalmenu.py: menu entries as the bar draws them, the Electron apps found, and the VS Code settings it needs,
set and put back."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import globalmenu  # noqa: E402
import globalmenu_reader  # noqa: E402
import electron  # noqa: E402


class EntryTests(unittest.TestCase):
    def test_labels_lose_their_mnemonic(self):
        self.assertEqual(globalmenu.label('_File'), 'File')
        self.assertEqual(globalmenu.label('Editor Playgrou_nd'), 'Editor Playground')
        self.assertEqual(globalmenu.label('Save __As'), 'Save _As')
        self.assertEqual(globalmenu.label(None), '')

    def test_shortcuts(self):
        self.assertEqual(globalmenu.shortcut([['Control', 'Shift', 'p']]), 'Ctrl+Shift+P')
        self.assertEqual(globalmenu.shortcut([['Alt', 'Return']]), 'Alt+Enter')
        self.assertEqual(globalmenu.shortcut([]), '')
        self.assertEqual(globalmenu.shortcut(None), '')

    def test_entries_fold_separators_and_drop_hidden_ones(self):
        children = [
            (1, {'type': 'separator'}, []),
            (2, {'label': '_New', 'shortcut': [['Control', 'n']]}, []),
            (3, {'type': 'separator'}, []),
            (4, {'type': 'separator'}, []),
            (5, {'label': 'Hidden', 'visible': False}, []),
            (6, {'label': 'Open _Recent', 'children-display': 'submenu'}, []),
            (7, {'label': 'Word Wrap', 'toggle-type': 'checkmark', 'toggle-state': 1, 'enabled': False}, []),
            (8, {'type': 'separator'}, []),
        ]
        self.assertEqual(globalmenu.entries(children), [
            {'id': 2, 'label': 'New', 'enabled': True, 'shortcut': 'Ctrl+N'},
            {'id': 3, 'kind': 'separator'},
            {'id': 6, 'label': 'Open Recent', 'enabled': True, 'submenu': True},
            {'id': 7, 'label': 'Word Wrap', 'enabled': False, 'checked': True},
        ])


class ReaderTests(unittest.TestCase):
    def test_accessibility_shortcuts(self):
        self.assertEqual(globalmenu_reader.shortcut_text('<Control>n'), 'Ctrl+N')
        self.assertEqual(globalmenu_reader.shortcut_text('n;<Control><Shift>n'), 'Ctrl+Shift+N')
        self.assertEqual(globalmenu_reader.shortcut_text('<Primary>q'), 'Ctrl+Q')
        self.assertEqual(globalmenu_reader.shortcut_text('Ctrl+O'), 'Ctrl+O')
        # Firefox gives the way by access keys, which is no shortcut.
        self.assertEqual(globalmenu_reader.shortcut_text('Alt+V:T'), '')
        self.assertEqual(globalmenu_reader.shortcut_text(''), '')

    def test_labels_lose_mnemonics_and_appended_shortcuts(self):
        self.assertEqual(globalmenu_reader.item_label('_Open\tCtrl+O'), 'Open')
        self.assertEqual(globalmenu_reader.item_label(None), '')

    def test_gtk_menus_inline_their_sections(self):
        source = globalmenu_reader.GtkMenus.__new__(globalmenu_reader.GtkMenus)
        source.menus = {
            (0, 0): [{'label': '_File', ':submenu': (0, 1)}, {'label': '_Help', ':submenu': (0, 2)}],
            (0, 1): [{':section': (0, 3)}, {':section': (0, 4)}],
            (0, 3): [{'label': '_New', 'action': 'app.new', 'accel': '<Control>n'}],
            (0, 4): [{'label': '_Quit', 'action': 'app.quit'}, {'label': 'Disabled'}],
            (0, 2): [],
        }
        source.actions = []
        source.load = lambda groups: None
        self.assertEqual(source.menu(), [{'id': 'g:0:1', 'label': 'File'}, {'id': 'g:0:2', 'label': 'Help'}])
        self.assertEqual(source.open('g:0:1'), [
            {'id': 'ga:0', 'label': 'New', 'enabled': True, 'shortcut': 'Ctrl+N'},
            {'id': 'gs', 'kind': 'separator'},
            {'id': 'ga:1', 'label': 'Quit', 'enabled': True},
            {'id': 'ga:2', 'label': 'Disabled', 'enabled': False},
        ])
        self.assertEqual(source.actions[0], ('app.new', None))


class CandidateTests(unittest.TestCase):
    def test_electron_apps_are_found_once_and_browsers_left_out(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apps = root / 'share/applications'
            apps.mkdir(parents=True)
            electron_app = root / 'opt/code'
            (electron_app / 'resources/app').mkdir(parents=True)
            (electron_app / 'code').write_text('')
            browser = root / 'opt/chrome'
            browser.mkdir(parents=True)
            (browser / 'chrome').write_text('')
            (apps / 'code.desktop').write_text(f'[Desktop Entry]\nName=Code\nExec={electron_app}/code %F\n')
            (apps / 'zz-code-again.desktop').write_text(f'[Desktop Entry]\nName=Code again\nExec=env A=1 {electron_app}/code\n')
            (apps / 'chrome.desktop').write_text(f'[Desktop Entry]\nName=Chrome\nExec={browser}/chrome\n')
            (apps / 'hidden.desktop').write_text(f'[Desktop Entry]\nName=Hidden\nNoDisplay=true\nExec={electron_app}/code\n')
            with mock.patch.object(globalmenu, 'data_dirs', return_value=[root / 'share']):
                self.assertEqual(globalmenu.candidates(), [{'id': 'code', 'name': 'Code'}])


class SettingsTests(unittest.TestCase):
    SAMPLES = ('{ "workbench.colorTheme": "Omarchy",\n    "editor.fontSize": 13,\n}\n',
               '{\n    // mine\n    "a": "x"\n}\n', '{}', '{\n    "window.titleBarStyle": "custom"\n}\n')

    def test_jsonc_reads_what_vscode_reads(self):
        self.assertEqual(globalmenu.jsonc('{\n  // c\n  "a": "//not", /* b */ "b": [1, 2,],\n}'), {'a': '//not', 'b': [1, 2]})

    def test_a_set_and_a_drop_give_the_file_back(self):
        for text in self.SAMPLES[:3]:
            with self.subTest(text=text):
                changed = globalmenu.set_setting(globalmenu.set_setting(text, 'window.titleBarStyle', 'native'), 'window.menuBarVisibility', 'toggle')
                self.assertEqual(globalmenu.jsonc(changed)['window.titleBarStyle'], 'native')
                back = globalmenu.drop_setting(globalmenu.drop_setting(changed, 'window.titleBarStyle'), 'window.menuBarVisibility')
                self.assertEqual(back, text)

    def test_apply_sets_the_settings_and_puts_them_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / 'settings.json'
            settings.write_text(self.SAMPLES[3])
            state = root / 'state/globalmenu.json'
            app_settings = {'com.microsoft.VSCode': (settings, {'window.titleBarStyle': 'native', 'window.menuBarVisibility': 'toggle'})}
            with mock.patch.object(globalmenu, 'APP_SETTINGS', app_settings), mock.patch.object(globalmenu, 'STATE', state), \
                    mock.patch.object(electron, 'main', return_value=0):
                with mock.patch.object(electron, 'x11_apps', return_value={'com.microsoft.VSCode'}):
                    globalmenu.apply()
                    # Applied again, the values from before are not overwritten by its own.
                    globalmenu.apply()
                self.assertEqual(globalmenu.jsonc(settings.read_text()),
                                 {'window.titleBarStyle': 'native', 'window.menuBarVisibility': 'toggle'})
                self.assertEqual(json.loads(state.read_text())['com.microsoft.VSCode'],
                                 {'window.titleBarStyle': 'custom', 'window.menuBarVisibility': None})
                with mock.patch.object(electron, 'x11_apps', return_value=set()):
                    globalmenu.apply()
                self.assertEqual(settings.read_text(), self.SAMPLES[3])
                self.assertEqual(json.loads(state.read_text()), {})

    def test_a_setting_added_later_is_set_and_saved_too(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / 'settings.json'
            settings.write_text('{\n    "window.titleBarStyle": "native",\n    "window.menuStyle": "custom"\n}\n')
            state = root / 'state.json'
            state.write_text('{"com.microsoft.VSCode": {"window.titleBarStyle": "custom"}}')
            values = {'window.titleBarStyle': 'native', 'window.menuStyle': 'native'}
            with mock.patch.object(globalmenu, 'APP_SETTINGS', {'com.microsoft.VSCode': (settings, values)}), \
                    mock.patch.object(globalmenu, 'STATE', state), mock.patch.object(electron, 'main', return_value=0):
                with mock.patch.object(electron, 'x11_apps', return_value={'com.microsoft.VSCode'}):
                    globalmenu.apply()
                self.assertEqual(globalmenu.jsonc(settings.read_text())['window.menuStyle'], 'native')
                self.assertEqual(json.loads(state.read_text())['com.microsoft.VSCode'],
                                 {'window.titleBarStyle': 'custom', 'window.menuStyle': 'custom'})
                with mock.patch.object(electron, 'x11_apps', return_value=set()):
                    globalmenu.apply()
                self.assertEqual(globalmenu.jsonc(settings.read_text()), {'window.titleBarStyle': 'custom', 'window.menuStyle': 'custom'})

    def test_a_file_vscode_cannot_read_is_left_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / 'settings.json'
            settings.write_text('{ broken')
            with mock.patch.object(globalmenu, 'APP_SETTINGS', {'com.microsoft.VSCode': (settings, {'window.titleBarStyle': 'native'})}), \
                    mock.patch.object(globalmenu, 'STATE', Path(directory) / 'state.json'), \
                    mock.patch.object(electron, 'main', return_value=0), \
                    mock.patch.object(electron, 'x11_apps', return_value={'com.microsoft.VSCode'}):
                globalmenu.apply()
            self.assertEqual(settings.read_text(), '{ broken')


if __name__ == '__main__':
    unittest.main()
