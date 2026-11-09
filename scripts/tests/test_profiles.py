#!/usr/bin/env python3
"""profiles.py: the profiles and their parts as Settings shows them, and the installer commands it plans."""
from collections import namedtuple
import contextlib
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import profiles  # noqa: E402
import tomllib  # noqa: E402

MANIFEST = tomllib.loads((REPO / 'scripts/install/manifest.toml').read_text())


Status = namedtuple('Status', 'missing total')
TUI = profiles.installer_screens()


def screens(statuses, recorded=('core', 'gaming'), exit_code=None):
    # install-tui.py as the helper uses it, with the Fedora manifest: the record and the state of each unit (what is
    # not named is not there at all).
    tui = TUI
    current = TUI.installer.load_plan(('core',), {'ID': 'fedora', 'VERSION_ID': '45'})
    patches = [mock.patch.object(tui, 'recorded_profiles', return_value=recorded),
               mock.patch.object(tui, 'profile_status', side_effect=lambda plan, name: statuses.get(name, Status(['x'], 1))),
               mock.patch.object(tui.installer, 'load_plan', side_effect=SystemExit(exit_code) if exit_code else None, return_value=current),
               mock.patch.object(tui.installer, 'touch_hardware', return_value=False),
               mock.patch.dict(tui.installer.DETECT, {name: (lambda: False) for name in tui.installer.DETECT})]
    return tui, patches


class ProfilesTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('profiles.tr', side_effect=lambda key, arguments=None: key + (':' + ','.join(arguments) if arguments else ''))
        patcher.start()
        self.addCleanup(patcher.stop)
        # Nothing of this system's own: each test says what is there.
        self.present = mock.patch.object(profiles, 'present_units', return_value=set())
        self.present.start()
        self.addCleanup(self.present.stop)

    def listing(self, statuses, **kwargs):
        tui, patches = screens(statuses, **kwargs)
        with contextlib.ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(mock.patch.object(profiles, 'installer_screens', return_value=tui))
            return profiles.listing()

    def test_every_profile_with_what_is_there_and_its_parts(self):
        statuses = {'core': Status([], 3), 'hardware': Status([], 0), 'hardware.intel': Status([], 4), 'hardware.audio': Status(['alsa-ucm'], 2),
                    'gaming': Status([], 1), 'gaming.steam': Status([], 2)}
        listed = self.listing(statuses, recorded=('core', 'gaming', 'gaming.steam'))
        self.assertEqual(listed['error'], '')
        rows = {row['name']: row for row in listed['profiles']}
        self.assertEqual(list(rows), list(TUI.installer.PROFILES))
        self.assertEqual((rows['core']['installed'], rows['core']['recorded'], rows['core']['default'], rows['core']['parts']), (True, True, True, []))
        # A profile with parts is there when its own setup (none for hardware) and one of its parts are.
        self.assertTrue(rows['hardware']['installed'])
        parts = {part['part']: part for part in rows['hardware']['parts']}
        self.assertEqual((parts['intel']['installed'], parts['audio']['installed'], parts['audio']['done']), (True, False, 1))
        # Without the hardware, only the firmware updates start checked.
        self.assertEqual([part['part'] for part in rows['hardware']['parts'] if part['default']], ['firmware'])
        gaming = {part['part']: part for part in rows['gaming']['parts']}
        self.assertEqual((gaming['steam']['recorded'], gaming['gamescope']['recorded']), (True, False))
        self.assertFalse(rows['apps']['installed'])

    def test_an_unsupported_system_is_an_error_not_a_crash(self):
        self.assertEqual(self.listing({}, exit_code='debian is not verified yet'), {'profiles': [], 'error': 'debian is not verified yet'})
        out = io.StringIO()
        with mock.patch.object(profiles, 'installer_screens', side_effect=OSError('gone')), contextlib.redirect_stdout(out):
            profiles.main(['list'])
        self.assertEqual(json.loads(out.getvalue()), {'profiles': [], 'error': 'gone'})

    def plan(self, action, *names, recorded=('core', 'gaming'), running=False):
        tui = TUI
        with mock.patch.object(tui, 'recorded_profiles', return_value=recorded), \
                mock.patch.object(tui.installer, 'hyprland_running', return_value=running), \
                mock.patch.object(profiles, 'installer_screens', return_value=tui), \
                mock.patch.object(tui.installer, 'distro_table', return_value=tui.installer.flatten_parts(MANIFEST['fedora'])), \
                mock.patch.dict(tui.installer.DETECT, {name: (lambda: False) for name in tui.installer.DETECT}):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                profiles.main(['plan', action, *names])
        return json.loads(out.getvalue())

    def test_install_keeps_the_recorded_units_and_adds_a_profile_with_its_default_parts(self):
        value = self.plan('install', 'apps', recorded=('core', 'gaming', 'gaming.steam'))
        script = str(profiles.REPO / 'scripts/install-desktop.py')
        units = 'core,apps,apps.zen,apps.loupe,apps.papers,apps.showtime,gaming,gaming.steam'
        self.assertEqual(value['preview'][1:], [script, 'dry-run', '--profiles', units])
        self.assertEqual(value['apply'][1:], [script, 'apply', '--profiles', units])
        self.assertEqual(value['blocked'], '')
        # A part alone: with its profile, and nothing else of it.
        self.assertEqual(self.plan('install', 'apps.vscode')['apply'][-1], 'core,apps,apps.vscode,gaming')

    def test_an_install_keeps_what_is_there_without_a_record(self):
        # Herdr from its own installer: an install from here records it, so the units file keeps the assistant.
        with mock.patch.object(profiles, 'present_units', return_value={'assistant'}):
            self.assertEqual(self.plan('install', 'radio', recorded=('core',))['apply'][-1], 'core,assistant,radio')

    def test_remove_undoes_a_profile_or_a_part(self):
        value = self.plan('remove', 'gaming.steam-hidpi')
        self.assertEqual(value['preview'][-3:], ['dry-run', '--remove', 'gaming.steam-hidpi'])
        self.assertEqual(value['apply'][-3:], ['apply', '--remove', 'gaming.steam-hidpi'])

    def test_a_change_adds_then_removes(self):
        value = self.plan('change', 'apps.vscode', 'gaming.steam')
        self.assertEqual(value['apply'][1:], [str(Path(profiles.__file__).resolve()), 'run', 'apply', 'apps.vscode', 'gaming.steam'])
        self.assertEqual(value['preview'][-3:], ['dry-run', 'apps.vscode', 'gaming.steam'])
        calls = []
        with mock.patch.object(profiles, 'installer_screens', return_value=TUI), mock.patch.object(TUI, 'recorded_profiles', return_value=('core',)), \
                mock.patch('subprocess.run', side_effect=lambda command: calls.append(command) or mock.Mock(returncode=0)):
            self.assertEqual(profiles.run('apply', 'apps.vscode', 'gaming.steam'), 0)
        self.assertEqual([command[2:] for command in calls], [['apply', '--profiles', 'core,apps,apps.vscode'], ['apply', '--remove', 'gaming.steam']])

    def test_removing_plugins_waits_for_a_session_without_hyprland(self):
        self.assertNotEqual(self.plan('remove', 'plugins', running=True)['blocked'], '')
        self.assertEqual(self.plan('remove', 'plugins', running=False)['blocked'], '')

    def test_only_units_are_planned(self):
        for arguments in (['remove', 'gaming; rm -rf ~'], ['remove', '$(id)'], ['remove', ''], ['install', 'nothing'],
                          ['remove', 'core'], ['change', '-', '-'], ['change', 'apps.nothing', '-']):
            with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
                profiles.main(['plan', *arguments])

    def test_the_real_installer_loads(self):
        # The helper reads install-tui.py from the repository it is linked from.
        tui = profiles.installer_screens()
        self.assertIn('assistant', tui.installer.PROFILES)
        self.assertTrue(callable(tui.profile_status))

if __name__ == '__main__':
    unittest.main()
