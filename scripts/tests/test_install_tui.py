#!/usr/bin/env python3
"""install-tui.py: the choices it offers map onto install-desktop.py, and nothing runs before the plan is confirmed."""
import atexit
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('install_tui', REPO / 'scripts/install-tui.py')
tui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tui)
installer = tui.installer
# Never the real state: apply writes its record there.
SANDBOX = tempfile.TemporaryDirectory()
atexit.register(SANDBOX.cleanup)
installer.STATE = Path(SANDBOX.name)
installer.RECORD = installer.STATE / 'install.json'

TABLE = {
    'core': {'packages': ['a', 'b'], 'repos': ['one'], 'services': ['s.service']},
    'plugins': {'packages': ['c'], 'swaps': [['old', 'new']]},
    'steam-hidpi': {'stow': ['steam-hidpi']},
}
FIRMWARE = {'product': 'Model', 'purpose': 'Rotation', 'source': 'Vendor pack', 'target': '/usr/lib/firmware/x.bin', 'sha256': '0' * 64, 'size': 1}


def plan(profiles=('core', 'plugins'), firmware=None):
    return installer.Plan(mock.Mock(), '45', TABLE, [], profiles, firmware)


class ChoiceTests(unittest.TestCase):
    def test_every_profile_is_described(self):
        self.assertEqual(set(tui.DESCRIPTIONS), set(installer.PROFILES))

    def test_core_cannot_be_turned_off(self):
        self.assertEqual(tui.toggled(('core', 'apps'), 'core'), ('core', 'apps'))

    def test_toggling_keeps_the_order_of_the_profiles(self):
        self.assertEqual(tui.toggled(('core', 'gaming'), 'apps'), ('core', 'apps', 'gaming'))
        self.assertEqual(tui.toggled(('core', 'apps', 'gaming'), 'apps'), ('core', 'gaming'))

    def test_the_summary_comes_from_the_manifest(self):
        self.assertEqual(tui.summary(TABLE, 'core'), '2 packages; repositories: one; services: s.service.')
        self.assertEqual(tui.summary(TABLE, 'plugins'), '1 packages; replaces old with new.')
        self.assertEqual(tui.summary(TABLE, 'steam-hidpi'), 'links: steam-hidpi.')
        self.assertEqual(tui.summary(TABLE, 'media'), '')

    def test_the_same_command_without_the_interface(self):
        self.assertEqual(tui.command(plan()), './scripts/install-desktop.py apply --profiles core,plugins')
        self.assertEqual(tui.command(plan(firmware='~/HP pack')), "./scripts/install-desktop.py apply --profiles core,plugins --firmware '~/HP pack'")

    def test_every_plugin_state_is_described(self):
        states = {value for name, value in vars(tui.bundle).items() if name.isupper() and name not in ('FILES', 'REPOSITORY', 'VERIFIED', 'CACHE', 'STAMP', 'PACKAGING', 'PLUGINS')}
        self.assertEqual(set(tui.PLUGIN_STATES), states)

    def test_finish_only_while_the_first_login_has_not(self):
        with tempfile.TemporaryDirectory() as folder, mock.patch.dict('os.environ', {'HYPRLAND_INSTANCE_SIGNATURE': 'sig'}):
            autostart = Path(folder) / 'desktop-finish-install.desktop'
            with mock.patch.object(installer, 'AUTOSTART', autostart):
                self.assertFalse(tui.post_pending())
                autostart.write_text('')
                self.assertTrue(tui.post_pending())
                with mock.patch.dict('os.environ', {'HYPRLAND_INSTANCE_SIGNATURE': ''}):
                    self.assertFalse(tui.post_pending())

    def test_the_removal_command(self):
        self.assertEqual(tui.command(plan()._replace(record={})), './scripts/install-desktop.py apply --uninstall')

    def test_long_descriptions_are_cut_visibly(self):
        self.assertEqual(tui.clip('abcdefgh', 6), 'abc...')
        self.assertEqual(tui.clip('abc', 6), 'abc')


class ReviewTests(unittest.TestCase):
    def test_what_a_check_prints_is_kept_off_the_screen(self):
        def noisy(_plan):
            print('Warning: this Hyprland build is not verified')
            return ['item']
        review = tui.review_step(plan(), installer.Step('verify', noisy, None))
        self.assertEqual(review, tui.Review('verify', ['item'], '', 'Warning: this Hyprland build is not verified'))

    def test_a_failed_check_is_shown_not_raised(self):
        def failing(_plan):
            raise RuntimeError('dnf check-upgrade failed: no network')
        review = tui.review_step(plan(), installer.Step('upgrade', failing, None))
        self.assertEqual((review.items, review.error), ([], 'dnf check-upgrade failed: no network'))

    def test_printed_warnings_join_the_preflight_ones(self):
        reviews = [tui.Review('verify', [], '', 'Warning: not verified')]
        with mock.patch.object(installer, 'preflight_warnings', return_value=['Only 10 GiB free on /.']):
            self.assertEqual(tui.review_warnings(plan(), reviews), ['Only 10 GiB free on /.', 'not verified'])

    def test_rows_fold_and_unfold_by_step(self):
        reviews = [tui.Review('repos', [], '', ''), tui.Review('packages', ['a', 'b'], '', ''), tui.Review('stow', [], 'failed', '')]
        folded = tui.review_rows(reviews, set())
        self.assertEqual([text for _, text, _ in folded], ['  repos      nothing to do', '+ packages   2 to do', '+ stow       check failed'])
        unfolded = tui.review_rows(reviews, {1, 2})
        self.assertEqual([owner for owner, _, _ in unfolded], [0, 1, 1, 1, 2, 2])
        self.assertEqual(unfolded[-1][2], 'error')

    def test_the_cursor_starts_on_the_first_step_with_work(self):
        reviews = [tui.Review('repos', [], '', ''), tui.Review('packages', ['a'], '', '')]
        self.assertEqual(tui.first_work(reviews), 1)
        self.assertEqual(tui.first_work(reviews[:1]), 0)


class CompletionTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        for name in ('firmware', 'files', '.hidden', 'single'):
            (self.root / name).mkdir()
        (self.root / 'fake.bin').write_text('')

    def test_one_match_completes_the_directory(self):
        self.assertEqual(tui.complete(f'{self.root}/si'), f'{self.root}/single/')

    def test_several_matches_complete_what_they_share(self):
        self.assertEqual(tui.complete(f'{self.root}/f'), f'{self.root}/fi')

    def test_hidden_directories_only_when_asked(self):
        self.assertEqual(tui.complete(f'{self.root}/'), f'{self.root}/')
        self.assertEqual(tui.complete(f'{self.root}/.h'), f'{self.root}/.hidden/')

    def test_an_empty_field_starts_at_home(self):
        self.assertEqual(tui.complete(''), '~/')
        self.assertEqual(tui.complete('~'), '~/')

    def test_nothing_to_complete_changes_nothing(self):
        self.assertEqual(tui.complete(f'{self.root}/zz'), f'{self.root}/zz')
        self.assertEqual(tui.complete('/no/such/place/x'), '/no/such/place/x')


ALL = {name: tui.Status([], 2) for name in installer.PROFILES}
FRESH = {name: tui.Status(['a', 'b'], 2) for name in installer.PROFILES}


class StatusTests(unittest.TestCase):
    def status(self, missing, swapped=False, name='plugins'):
        distro = mock.Mock()
        distro.missing.side_effect = lambda packages: [package for package in packages if package in missing]
        distro.installed.side_effect = lambda package: package == 'old' and not swapped
        return tui.profile_status(installer.Plan(distro, '45', TABLE, [], ('core',)), name)

    def test_a_profile_counts_its_packages_and_swaps(self):
        self.assertEqual(self.status([], swapped=True), tui.Status([], 3))
        self.assertEqual(self.status(['c']), tui.Status(['c', 'old -> new'], 3))

    def test_aur_packages_count_until_they_are_at_their_pinned_version(self):
        table = {**TABLE, 'apps': {'packages': ['base-devel'], 'aur': [{'package': 'zen', 'commit': 'c' * 40, 'version': '2-1'}]}}
        distro = mock.Mock()
        distro.missing.return_value = []
        for installed, missing in (('', ['zen']), ('1-1', ['zen']), ('2-1', [])):
            distro.version.return_value = installed
            self.assertEqual(tui.profile_status(installer.Plan(distro, 'rolling', table, [], ('core',)), 'apps'), tui.Status(missing, 2))
        self.assertEqual(tui.summary(table, 'apps'), '1 packages; from the AUR: zen.')

    def test_stow_links_count_once_they_point_into_the_repository(self):
        with tempfile.TemporaryDirectory() as home, mock.patch.object(Path, 'home', return_value=Path(home)):
            files = tui.stow_files('steam-hidpi')
            self.assertTrue(files)
            self.assertEqual(self.status([], name='steam-hidpi').total, len(files))
            self.assertEqual(len(self.status([], name='steam-hidpi').missing), len(files))
            for path in files:
                target = Path(home) / path.relative_to(REPO / 'steam-hidpi')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(path)
            self.assertEqual(self.status([], name='steam-hidpi').missing, [])

    def test_a_plain_file_is_not_a_link(self):
        with tempfile.TemporaryDirectory() as home, mock.patch.object(Path, 'home', return_value=Path(home)):
            path = tui.stow_files('steam-hidpi')[0]
            target = Path(home) / path.relative_to(REPO / 'steam-hidpi')
            target.parent.mkdir(parents=True)
            target.write_text(path.read_text())
            self.assertFalse(tui.linked('steam-hidpi', path))

    def test_labels(self):
        self.assertEqual(tui.status_label(tui.Status([], 3)), 'installed')
        self.assertEqual(tui.status_label(tui.Status(['a'], 3)), '2/3')
        self.assertEqual(tui.status_label(tui.Status(['a', 'b', 'c'], 3)), '')
        self.assertEqual(tui.status_label(tui.Status([], 0)), '')

    def test_an_installed_desktop_starts_from_what_it_has(self):
        statuses = {**FRESH, 'core': tui.Status([], 2), 'apps': tui.Status([], 2), 'gaming': tui.Status(['x'], 2)}
        self.assertEqual(tui.preselected(statuses), ('core', 'apps'))
        self.assertEqual(tui.preselected(ALL), installer.PROFILES)

    def test_a_fresh_system_starts_from_the_defaults(self):
        self.assertEqual(tui.preselected({**FRESH, 'apps': tui.Status([], 2)}), tuple(installer.DEFAULT_PROFILES.split(',')))

    def test_a_partial_profile_names_what_is_missing(self):
        self.assertEqual(tui.status_text(tui.Status(['a', 'b'], 5)), 'Partly installed (3/5); missing: a, b.')
        self.assertIn('removes nothing', tui.status_text(tui.Status([], 5)))


class FlowTests(unittest.TestCase):
    def run_interface(self, profiles, firmware_needed, review='apply', firmware=('next', '~/pack')):
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', return_value='install'), \
                mock.patch.object(tui, 'detect', return_value=FRESH), \
                mock.patch.object(tui, 'choose_profiles', return_value=('next', profiles)), \
                mock.patch.object(tui, 'choose_firmware', return_value=firmware) as asked, \
                mock.patch.object(tui, 'firmware_items', side_effect=lambda chosen: [FIRMWARE] if firmware_needed and 'hardware' in chosen.profiles else []), \
                mock.patch.object(tui, 'review', return_value=review):
            return tui.interface(None, plan(firmware='~/old')), asked

    def test_the_firmware_screen_only_when_this_model_needs_it(self):
        (action, chosen), asked = self.run_interface(('core', 'hardware'), True)
        self.assertEqual((action, chosen.profiles, chosen.firmware), ('apply', ('core', 'hardware'), '~/pack'))
        asked.assert_called_once()

    def test_without_the_firmware_screen_no_directory_is_passed(self):
        (action, chosen), asked = self.run_interface(('core',), True)
        self.assertEqual((action, chosen.firmware), ('apply', None))
        asked.assert_not_called()

    def test_quitting_the_review_runs_nothing(self):
        self.assertIsNone(self.run_interface(('core',), False, review='quit')[0])

    def first_choice(self, statuses, preset):
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', return_value='install'), \
                mock.patch.object(tui, 'detect', return_value=statuses) as detected, \
                mock.patch.object(tui, 'choose_profiles', return_value=('quit', ())) as chosen:
            tui.interface(None, plan(('core', 'media')), preset)
        detected.assert_called_once()
        return chosen.call_args.args[1].profiles

    def test_the_installed_profiles_start_on(self):
        self.assertEqual(self.first_choice(ALL, False), installer.PROFILES)

    def test_given_profiles_win_over_what_is_found(self):
        self.assertEqual(self.first_choice(ALL, True), ('core', 'media'))

    def test_the_system_is_looked_at_once(self):
        answers = iter([('back', ('core',)), ('quit', ('core',))])
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', return_value='install'), \
                mock.patch.object(tui, 'detect', return_value=ALL) as detected, \
                mock.patch.object(tui, 'choose_profiles', side_effect=lambda *_: next(answers)):
            tui.interface(None, plan())
        detected.assert_called_once()

    def removal_flow(self, running, outcome='apply'):
        menus = iter(['uninstall', 'quit'])
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', side_effect=lambda ui: next(menus)), \
                mock.patch.object(installer, 'hyprland_running', return_value=running), \
                mock.patch.object(installer, 'uninstall_plan', side_effect=lambda chosen: chosen._replace(record={'packages': []})), \
                mock.patch.object(tui, 'notice') as noticed, mock.patch.object(tui, 'review', return_value=outcome) as reviewed, \
                mock.patch.object(tui, 'detect') as detected:
            result = tui.interface(None, plan())
        detected.assert_not_called()
        return result, noticed, reviewed

    def test_removal_is_refused_while_hyprland_runs(self):
        result, noticed, reviewed = self.removal_flow(running=True)
        self.assertIsNone(result)
        noticed.assert_called_once()
        reviewed.assert_not_called()

    def test_a_confirmed_removal_comes_back_with_its_record(self):
        (action, chosen), noticed, _ = self.removal_flow(running=False)
        self.assertEqual((action, chosen.record), ('uninstall', {'packages': []}))
        noticed.assert_not_called()

    def test_leaving_the_removal_review_goes_back_to_the_menu(self):
        self.assertIsNone(self.removal_flow(running=False, outcome='back')[0])

    def test_post_skips_the_review(self):
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', return_value='post'), \
                mock.patch.object(tui, 'detect', return_value=ALL), \
                mock.patch.object(tui, 'choose_profiles', return_value=('next', ('core', 'plugins'))), \
                mock.patch.object(tui, 'review') as reviewed:
            action, chosen = tui.interface(None, plan())
        self.assertEqual((action, chosen.profiles), ('post', ('core', 'plugins')))
        reviewed.assert_not_called()


class ApplyTests(unittest.TestCase):
    def apply(self, done, answer, booted=True):
        calls = []
        with mock.patch('subprocess.run', side_effect=lambda command, **_: calls.append(command)), \
                mock.patch.object(installer, 'run_steps', side_effect=lambda *_: calls.append('steps') or done) as steps, \
                mock.patch.object(installer, 'next_steps'), mock.patch.object(installer, 'booted', return_value=booted), \
                mock.patch.object(tui, 'keep_sudo'), mock.patch('builtins.input', return_value=answer), mock.patch('builtins.print'):
            self.assertEqual(tui.apply(plan()), 0)
        steps.assert_called_once_with(mock.ANY, False, installer.STEPS)
        return calls

    def test_a_removal_runs_the_uninstall_steps_after_checking_for_hyprland(self):
        removal = plan()._replace(record={'packages': ['a']})
        with mock.patch('subprocess.run'), mock.patch.object(installer, 'run_steps', return_value=0) as steps, \
                mock.patch.object(installer, 'refuse_uninstall') as refused, mock.patch.object(installer, 'after_uninstall') as after, \
                mock.patch.object(tui, 'keep_sudo'), mock.patch('builtins.print'):
            tui.apply(removal)
        refused.assert_called_once()
        steps.assert_called_once_with(removal, False, installer.UNSTEPS)
        after.assert_called_once_with(removal, 0)

    def test_sudo_asks_once_before_the_first_step(self):
        self.assertEqual(self.apply(3, 'n')[:2], [('sudo', '-v'), 'steps'])

    def test_a_reboot_only_when_asked(self):
        self.assertEqual(self.apply(3, 'y')[-1], ('sudo', 'systemctl', 'reboot'))
        self.assertNotIn(('sudo', 'systemctl', 'reboot'), self.apply(3, ''))

    def test_no_reboot_question_when_nothing_changed_or_in_a_container(self):
        self.assertNotIn(('sudo', 'systemctl', 'reboot'), self.apply(0, 'y'))
        self.assertNotIn(('sudo', 'systemctl', 'reboot'), self.apply(3, 'y', booted=False))

    def test_the_sudo_refresh_never_prompts(self):
        stop = mock.Mock()
        stop.wait.side_effect = [False, True]
        with mock.patch('subprocess.run') as run:
            tui.keep_sudo(stop)
        run.assert_called_once_with(('sudo', '-n', '-v'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class RefusalTests(unittest.TestCase):
    def test_root(self):
        with mock.patch('os.geteuid', return_value=0), self.assertRaises(SystemExit) as caught:
            tui.main([])
        self.assertIn('desktop user', str(caught.exception))

    def test_no_terminal(self):
        with mock.patch('os.geteuid', return_value=1000), mock.patch('sys.stdin') as stdin, self.assertRaises(SystemExit) as caught:
            stdin.isatty.return_value = False
            tui.main([])
        self.assertIn('install-desktop.py', str(caught.exception))

    def test_profiles_need_core(self):
        with mock.patch('sys.stderr'), self.assertRaises(SystemExit) as caught:
            tui.main(['--profiles', 'apps'])
        self.assertEqual(caught.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
