#!/usr/bin/env python3
"""profiles.py: the profiles as Settings shows them, and the guided installer it opens to add or remove one."""
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


def screens(statuses, recorded=('core', 'gaming'), exit_code=None):
    # install-tui.py as the helper uses it: the plan, the record and the state of each profile.
    tui = mock.Mock()
    tui.installer.PROFILES = tuple(statuses)
    tui.installer.default_profiles.return_value = 'core,hardware'
    if exit_code is not None:
        tui.installer.load_plan.side_effect = SystemExit(exit_code)
    tui.recorded_profiles.return_value = recorded
    tui.profile_status.side_effect = lambda plan, name: statuses[name]
    tui.installed.side_effect = lambda status: bool(status.total) and not status.missing
    return tui


class ProfilesTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('profiles.tr', side_effect=lambda key, arguments=None: key + (':' + ','.join(arguments) if arguments else ''))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_every_profile_with_what_is_there(self):
        Status = namedtuple('Status', 'missing total')
        statuses = {'core': Status([], 3), 'hardware': Status(['fwupd'], 2), 'gaming': Status([], 1), 'media': Status(['a', 'b'], 2)}
        with mock.patch.object(profiles, 'installer_screens', return_value=screens(statuses)):
            listed = profiles.listing()
        self.assertEqual(listed['error'], '')
        self.assertEqual([(row['name'], row['installed'], row['done'], row['total'], row['recorded'], row['default']) for row in listed['profiles']],
                         [('core', True, 3, 3, True, True), ('hardware', False, 1, 2, False, True), ('gaming', True, 1, 1, True, False),
                          ('media', False, 0, 2, False, False)])

    def test_an_unsupported_system_is_an_error_not_a_crash(self):
        with mock.patch.object(profiles, 'installer_screens', return_value=screens({}, exit_code='debian is not verified yet')):
            self.assertEqual(profiles.listing(), {'profiles': [], 'error': 'debian is not verified yet'})
        out = io.StringIO()
        with mock.patch.object(profiles, 'installer_screens', side_effect=OSError('gone')), contextlib.redirect_stdout(out):
            profiles.main(['list'])
        self.assertEqual(json.loads(out.getvalue()), {'profiles': [], 'error': 'gone'})

    def plan(self, action, name, recorded=('core', 'gaming'), running=False):
        tui = profiles.installer_screens()
        with mock.patch.object(tui, 'recorded_profiles', return_value=recorded), \
                mock.patch.object(tui.installer, 'hyprland_running', return_value=running), \
                mock.patch.object(profiles, 'installer_screens', return_value=tui):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                profiles.main(['plan', action, name])
        return json.loads(out.getvalue())

    def test_install_keeps_the_recorded_profiles_and_adds_one(self):
        value = self.plan('install', 'media')
        script = str(profiles.REPO / 'scripts/install-desktop.py')
        self.assertEqual(value['preview'][1:], [script, 'dry-run', '--profiles', 'core,media,gaming'])
        self.assertEqual(value['apply'][1:], [script, 'apply', '--profiles', 'core,media,gaming'])
        self.assertEqual(value['blocked'], '')

    def test_remove_undoes_one_profile(self):
        value = self.plan('remove', 'steam-hidpi')
        self.assertEqual(value['preview'][-3:], ['dry-run', '--remove', 'steam-hidpi'])
        self.assertEqual(value['apply'][-3:], ['apply', '--remove', 'steam-hidpi'])

    def test_removing_plugins_waits_for_a_session_without_hyprland(self):
        self.assertNotEqual(self.plan('remove', 'plugins', running=True)['blocked'], '')
        self.assertEqual(self.plan('remove', 'plugins', running=False)['blocked'], '')

    def test_only_profile_names_are_planned(self):
        for action, name in (('remove', 'gaming; rm -rf ~'), ('remove', '$(id)'), ('remove', ''), ('install', 'nothing'),
                             ('remove', 'core')):
            with self.assertRaises(ValueError), contextlib.redirect_stdout(io.StringIO()):
                profiles.main(['plan', action, name])

    def test_the_real_installer_loads(self):
        # The helper reads install-tui.py from the repository it is linked from.
        tui = profiles.installer_screens()
        self.assertIn('herdr', tui.installer.PROFILES)
        self.assertTrue(callable(tui.profile_status))


if __name__ == '__main__':
    unittest.main()
