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
        self.assertEqual(set(tui.DESCRIPTIONS), set(installer.manifest_units()))

    def test_core_cannot_be_turned_off(self):
        self.assertEqual(tui.toggled(('core', 'apps'), 'core'), ('core', 'apps'))

    def test_toggling_keeps_the_order_of_the_profiles(self):
        # A profile comes with its default parts, and goes with all of them.
        self.assertEqual(tui.toggled(('core', 'gaming'), 'apps'), ('core', 'apps', 'apps.zen', 'apps.loupe', 'apps.papers', 'apps.showtime', 'gaming'))
        self.assertEqual(tui.toggled(('core', 'apps', 'apps.zen', 'apps.vscode', 'gaming'), 'apps'), ('core', 'gaming'))

    def test_a_part_comes_with_its_profile_and_goes_alone(self):
        self.assertEqual(tui.toggled(('core',), 'apps.vscode'), ('core', 'apps', 'apps.vscode'))
        self.assertEqual(tui.toggled(('core', 'apps', 'apps.zen', 'apps.vscode'), 'apps.zen'), ('core', 'apps', 'apps.vscode'))

    def test_the_accordion_shows_the_parts_of_open_profiles(self):
        names = installer.manifest_units()
        self.assertNotIn('apps.zen', tui.visible_units(names, set()))
        rows = tui.visible_units(names, {'apps'})
        self.assertEqual(rows[rows.index('apps') + 1], 'apps.zen')
        cursor, opened = tui.move_in_accordion(tui.RIGHT[0], names, rows.index('apps'), set())
        self.assertEqual(opened, {'apps'})
        # Left from a part closes its profile and goes back to it.
        rows = tui.visible_units(names, opened)
        cursor, opened = tui.move_in_accordion(tui.LEFT[0], names, rows.index('apps.papers'), opened)
        self.assertEqual((opened, tui.visible_units(names, opened)[cursor]), (set(), 'apps'))
        self.assertEqual(tui.unit_row('apps.zen', '[x]', {'apps'}), '    [x] zen')
        self.assertEqual(tui.unit_row('apps', '[ ]', {'apps'}), 'v [ ] apps')
        self.assertEqual(tui.unit_row('radio', '[ ]', set()), '  [ ] radio')

    def test_the_summary_comes_from_the_manifest(self):
        self.assertEqual(tui.summary(TABLE, 'core'), '2 packages; repositories: one; services: s.service.')
        self.assertEqual(tui.summary(TABLE, 'plugins'), '1 packages; replaces old with new.')
        self.assertEqual(tui.summary(TABLE, 'steam-hidpi'), 'links: steam-hidpi.')
        self.assertEqual(tui.summary(TABLE, 'media'), '')

    def test_the_same_command_without_the_interface(self):
        self.assertEqual(tui.command(plan()), './scripts/install-desktop.py apply --profiles core,plugins')
        self.assertEqual(tui.command(plan(firmware='~/HP pack')), "./scripts/install-desktop.py apply --profiles core,plugins --firmware '~/HP pack'")

    def test_every_plugin_state_is_described(self):
        states = {value for name, value in vars(tui.bundle).items() if name.isupper() and name not in ('FILES', 'REPOSITORY', 'VERIFIED', 'CACHE', 'STAMP', 'PACKAGING', 'PLUGINS', 'RECORD', 'PROFILE_OF', 'PROFILES_VERSION', 'UNITS_OF_V2')}
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


ALL = {name: tui.Status([], 2) for name in installer.manifest_units()}
FRESH = {name: tui.Status(['a', 'b'], 2) for name in installer.manifest_units()}


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
        statuses = {**FRESH, 'core': tui.Status([], 2), 'apps': tui.Status([], 0), 'apps.zen': tui.Status([], 2), 'gaming': tui.Status(['x'], 2)}
        self.assertEqual(tui.preselected(statuses), ('core', 'apps', 'apps.zen'))
        # A profile with parts but none of them there is not.
        self.assertEqual(tui.preselected({**statuses, 'apps.zen': tui.Status(['zen-browser'], 1)}), ('core',))
        self.assertEqual(tui.preselected(ALL), installer.manifest_units())

    def test_a_fresh_system_starts_from_the_defaults(self):
        # Without the hardware the parts detect, hardware brings only its firmware updates.
        with mock.patch.dict(installer.DETECT, {name: (lambda: False) for name in installer.DETECT}):
            with mock.patch.object(installer, 'touch_hardware', return_value=False):
                self.assertEqual(tui.preselected({**FRESH, 'apps': tui.Status([], 2)}), ('core', 'hardware', 'hardware.firmware', 'plugins'))
            with mock.patch.object(installer, 'touch_hardware', return_value=True):
                self.assertEqual(tui.preselected(FRESH), ('core', 'hardware', 'hardware.firmware', 'tablet', 'plugins'))

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
            tui.interface(None, plan(('core', 'radio')), preset)
        detected.assert_called_once()
        return chosen.call_args.args[1].profiles

    def test_the_installed_profiles_start_on(self):
        self.assertEqual(self.first_choice(ALL, False), installer.manifest_units())

    def test_given_profiles_win_over_what_is_found(self):
        self.assertEqual(self.first_choice(ALL, True), ('core', 'radio'))

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

    def profile_removal(self, running, start='menu', removal=(), chooser=('next', ('gaming',))):
        menus = iter(['remove', 'quit'])
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', side_effect=lambda ui: next(menus)), \
                mock.patch.object(installer, 'hyprland_running', return_value=running), \
                mock.patch.object(installer, 'removal_plan', side_effect=lambda chosen, removed: chosen._replace(record={'removing': list(removed)})), \
                mock.patch.object(tui, 'notice') as noticed, mock.patch.object(tui, 'review', return_value='apply') as reviewed, \
                mock.patch.object(tui, 'detect', return_value=ALL), mock.patch.object(tui, 'choose_removal', return_value=chooser) as chose:
            result = tui.interface(None, plan(), False, start, (), removal)
        return result, noticed, reviewed, chose

    def test_profiles_chosen_from_the_menu_come_back_as_their_removal(self):
        (action, chosen), noticed, _, chose = self.profile_removal(running=True)
        self.assertEqual((action, chosen.record), ('uninstall', {'removing': ['gaming']}))
        chose.assert_called_once()
        noticed.assert_not_called()

    def test_remove_starts_on_the_review(self):
        (action, chosen), _, _, chose = self.profile_removal(running=False, start='removal', removal=('media',))
        self.assertEqual(chosen.record, {'removing': ['media']})
        chose.assert_not_called()

    def test_the_plugins_profile_is_refused_while_hyprland_runs(self):
        result, noticed, reviewed, _ = self.profile_removal(running=True, start='removal', removal=('plugins',), chooser=('quit', ()))
        self.assertIsNone(result)
        noticed.assert_called_once()
        reviewed.assert_not_called()

    def test_add_checks_the_profile_on_top_of_the_installed_ones(self):
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'detect', return_value=ALL), \
                mock.patch.object(tui, 'choose_profiles', return_value=('quit', ())) as chose:
            tui.interface(None, plan(), False, 'profiles', ('assistant',))
        self.assertIn('assistant', chose.call_args.args[1].profiles)
        self.assertTrue(set(tui.preselected(ALL)) <= set(chose.call_args.args[1].profiles))

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

    def test_removing_profiles_runs_their_steps_and_needs_a_console_only_for_plugins(self):
        for removed, console in ((['gaming'], False), (['gaming', 'plugins'], True)):
            removal = plan()._replace(record={'removing': removed, 'packages': ['steam']})
            with mock.patch('subprocess.run'), mock.patch.object(installer, 'run_steps', return_value=2) as steps, \
                    mock.patch.object(installer, 'refuse_uninstall') as refused, mock.patch.object(installer, 'after_uninstall') as after, \
                    mock.patch.object(installer, 'load_record') as record, mock.patch.object(tui, 'keep_sudo'), \
                    mock.patch('builtins.print'), mock.patch('builtins.input') as asked:
                self.assertEqual(tui.apply(removal), 0)
            self.assertEqual(refused.called, console)
            steps.assert_called_once_with(removal, False, installer.PROFILE_UNSTEPS)
            after.assert_not_called()
            record.assert_not_called()
            asked.assert_not_called()
            self.assertEqual(tui.command(removal), './scripts/install-desktop.py apply --remove ' + ','.join(removed))

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


def reply(stdout='', returncode=0, stderr=''):
    return subprocess.CompletedProcess((), returncode, stdout, stderr)


PIN = installer.Pin('clones', 'zsh-autocomplete', 'a' * 40, 'b' * 40, '26.08.04 -> 26.09.01', 'https://x/compare', '', '26.09.01')


def source(key, selectable=True, pins=()):
    return tui.Source(key, key.title(), 'summary', ['detail'], 'note', selectable, pins)


class UpdateSourceTests(unittest.TestCase):
    def test_everything_to_apply_is_checked_but_the_repository(self):
        sources = [source('system'), source('flatpak', False), source('repository'), source('plugins', False)]
        self.assertEqual(tui.default_choice(sources), {'system'})

    def test_the_repository_goes_alone(self):
        sources = [source('system'), source('clones'), source('repository')]
        self.assertEqual(tui.picked_sources(sources, {'system', 'repository'}), ('pull', [sources[2]]))
        self.assertEqual(tui.picked_sources(sources, {'system', 'clones'}), ('apply', sources[:2]))
        self.assertEqual(tui.picked_sources(sources, {'flatpak'}), ('apply', []))

    def test_rows_show_what_can_be_checked_and_fold(self):
        sources = [source('system'), source('plugins', False)]
        rows = tui.update_rows(sources, {'system'}, set())
        self.assertEqual([text for _, text, _ in rows], ['+ [x] System            summary', '+     Plugins           summary'])
        self.assertEqual(tui.update_rows(sources, set(), {0})[0][1], '- [ ] System            summary')
        self.assertEqual(tui.update_rows(sources, set(), {0})[1], (0, '        detail', 'dim'))

    def test_counts_read_well(self):
        self.assertEqual((tui.counted(1, 'update'), tui.counted(3, 'step')), ('1 update', '3 steps'))

    def test_system_packages_come_from_the_bar_s_own_check(self):
        updates = mock.Mock(COMPOSITOR=('hyprland',))
        updates.system_updates.return_value = ([{'name': 'hyprland', 'version': '0.58.0-1', 'repo': ''}], None)
        current = installer.Plan(mock.Mock(MANAGER='dnf'), '45', TABLE, [], ('core',))
        found = tui.package_source(current, updates)
        self.assertEqual((found.summary, found.details, found.selectable), ('1 update (dnf)', ['hyprland 0.58.0-1'], True))
        self.assertIn('plugins rebuild', found.note)
        updates.system_updates.return_value = (None, 'offline')
        self.assertEqual(tui.package_source(current, updates).error, 'offline')

    def test_flatpak_apps(self):
        updates = mock.Mock()
        updates.flatpak_listing.return_value = ([], None)
        self.assertEqual(tui.flatpak_source(updates).summary, 'up to date')
        self.assertFalse(tui.flatpak_source(updates).selectable)

    def pins(self, newer, ours=True):
        table = {**TABLE, 'core': {**TABLE['core'], 'clones': [{'repo': 'https://github.com/a/b', 'commit': 'a' * 40, 'path': '.p/zsh-autocomplete'}]}}
        with mock.patch.object(installer, 'newer_pin', return_value=newer), mock.patch.object(installer, 'clone_ours', return_value=ours):
            return tui.pin_source(installer.Plan(mock.Mock(), '45', table, [], ('core',)), 'clones', 'zsh plugins')

    def test_a_newer_pin_can_be_applied(self):
        found = self.pins(PIN)
        self.assertEqual((found.summary, found.pins, found.selectable), ('zsh-autocomplete 26.08.04 -> 26.09.01', (PIN,), True))

    def test_a_changed_clone_holds_its_pin(self):
        found = self.pins(PIN, ours=False)
        self.assertFalse(found.selectable)
        self.assertEqual(found.summary, 'zsh-autocomplete: newer, but changed here')
        self.assertIn('has local changes', found.details[0])

    def test_a_remote_that_does_not_answer_is_an_error(self):
        found = self.pins(False)
        self.assertEqual((found.summary, found.selectable), ('check failed', False))
        self.assertIn('did not answer', found.error)
        self.assertEqual(self.pins(None).summary, 'at their latest commits')

    def test_no_pins_no_line(self):
        self.assertIsNone(tui.pin_source(plan(), 'aur', 'AUR packages'))

    def repository(self, behind='3', ahead='0', dirty='', upstream=reply('origin/main\n'), fetch=reply()):
        answers = {'rev-parse': upstream, 'fetch': fetch, 'status': reply(dirty), 'log': reply('abc1234 docs: x\n')}

        def git(*arguments):
            if arguments[0] == 'rev-list':
                return reply(behind if arguments[-1] == 'HEAD..@{u}' else ahead)
            return answers[arguments[0]]
        with mock.patch.object(tui, 'git', side_effect=git):
            return tui.repository_source()

    def test_a_clean_tree_behind_its_upstream_can_fast_forward(self):
        found = self.repository()
        self.assertEqual((found.summary, found.details, found.selectable), ('3 commits behind origin/main', ['abc1234 docs: x'], True))

    def test_local_changes_or_commits_stop_the_fast_forward(self):
        self.assertFalse(self.repository(dirty=' M x').selectable)
        self.assertIn('local changes', self.repository(dirty=' M x').summary)
        self.assertFalse(self.repository(ahead='1').selectable)
        self.assertIn('merge it by hand', self.repository(ahead='1').summary)

    def test_up_to_date_or_nothing_to_compare_with(self):
        self.assertEqual(self.repository(behind='0').summary, 'up to date with origin/main')
        self.assertEqual(self.repository(upstream=reply('', 128)).summary, 'no upstream branch to compare with')
        self.assertIn('git fetch failed', self.repository(fetch=reply('', 128, 'Permission denied')).error)

    def test_git_never_prompts(self):
        with mock.patch.dict('os.environ', {}, clear=False), mock.patch.object(installer, 'query', return_value=reply('')), \
                mock.patch('subprocess.run', return_value=reply()) as run:
            tui.os.environ.pop('GIT_SSH_COMMAND', None)
            tui.git('fetch', '--quiet', 'origin')
        environment = run.call_args.kwargs['env']
        self.assertEqual((environment['GIT_TERMINAL_PROMPT'], environment['GIT_SSH_COMMAND']), ('0', 'ssh -o BatchMode=yes'))

    def test_a_check_that_fails_is_a_line_not_a_crash(self):
        ui = mock.Mock()
        ui.frame.return_value = None
        with mock.patch.object(tui, 'shell_helper'), mock.patch.object(tui, 'package_source', side_effect=RuntimeError('no network')), \
                mock.patch.object(tui, 'flatpak_source', return_value=None), mock.patch.object(tui, 'pin_source', return_value=None), \
                mock.patch.object(tui, 'repository_source', return_value=None), mock.patch.object(tui, 'desktop_source', return_value=None), \
                mock.patch.object(tui, 'plugins_source', return_value=None), mock.patch.object(tui, 'maintainer', return_value=True):
            found = tui.check_updates(ui, plan())
        self.assertEqual([(entry.key, entry.error) for entry in found], [('system', 'no network')])

    def test_the_pins_only_for_the_maintainer(self):
        ui = mock.Mock()
        ui.frame.return_value = None
        for maintainer, kinds in ((True, ['aur', 'clones', 'archives']), (False, [])):
            line = lambda _plan, kind, title: tui.Source(kind, title, 'newer', [], '', True)
            with mock.patch.object(tui, 'shell_helper'), mock.patch.object(tui, 'package_source', return_value=None), \
                    mock.patch.object(tui, 'flatpak_source', return_value=None), mock.patch.object(tui, 'pin_source', side_effect=line), \
                    mock.patch.object(tui, 'repository_source', return_value=None), mock.patch.object(tui, 'desktop_source', return_value=None), \
                    mock.patch.object(tui, 'plugins_source', return_value=None), mock.patch.object(tui, 'maintainer', return_value=maintainer):
                found = tui.check_updates(ui, plan())
            self.assertEqual([entry.key for entry in found], kinds)

    def test_the_maintainer_is_named_in_the_repository_s_git_config(self):
        for answer, expected in (('true\n', True), ('false\n', False), ('', False)):
            with mock.patch.object(tui, 'git', return_value=reply(answer)) as git:
                self.assertEqual(tui.maintainer(), expected)
            git.assert_called_once_with('config', '--bool', 'desktop.maintainer')

    def test_the_shell_helpers_never_hide_the_standard_library(self):
        updates = tui.shell_helper('updates')
        self.assertEqual(sys.path[-1], str(tui.HELPERS))
        import calendar
        self.assertNotEqual(Path(calendar.__file__).parent, tui.HELPERS)
        self.assertTrue(callable(updates.flatpak_listing))

    def test_updates_are_offered_once_the_desktop_is_there(self):
        for present in (True, False):
            with mock.patch.object(installer, 'desktop_present', return_value=present), mock.patch.object(tui, 'post_pending', return_value=False):
                self.assertEqual('updates' in [key for key, _, _ in tui.menu_entries()], present)


class UpdateFlowTests(unittest.TestCase):
    def interface(self, outcome, recorded=('core', 'gaming'), present=True, statuses=ALL, start='menu'):
        menus = iter(['updates', 'quit'])
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', side_effect=lambda ui: next(menus)), \
                mock.patch.object(installer, 'desktop_present', return_value=present), \
                mock.patch.object(tui, 'recorded_profiles', return_value=recorded), \
                mock.patch.object(tui, 'detect', return_value=statuses) as detected, mock.patch.object(tui, 'notice') as noticed, \
                mock.patch.object(tui, 'updates_screen', return_value=outcome) as screen:
            return tui.interface(None, plan(('core', 'media')), True, start), noticed, screen, detected

    def test_updates_cover_the_recorded_profiles_whatever_was_given(self):
        (action, chosen, picked), _, screen, detected = self.interface(('apply', ['s']))
        self.assertEqual((action, chosen.profiles, picked), ('updates', ('core', 'gaming'), ['s']))
        detected.assert_not_called()

    def test_without_a_record_the_installed_profiles(self):
        (_, chosen, _), _, _, detected = self.interface(('apply', ['s']), recorded=(), statuses={**FRESH, 'radio': tui.Status([], 2)})
        self.assertEqual(chosen.profiles, ('core', 'radio'))
        detected.assert_called_once()

    def test_the_repository_comes_back_as_a_pull(self):
        self.assertEqual(self.interface(('pull', ['r']))[0][0], 'pull')

    def test_without_a_desktop_there_is_nothing_to_update(self):
        result, noticed, screen, _ = self.interface(('apply', ['s']), present=False)
        self.assertIsNone(result)
        noticed.assert_called_once()
        screen.assert_not_called()

    def test_updates_can_be_the_first_screen_and_go_back_to_the_menu(self):
        with mock.patch.object(tui, 'Screen'), mock.patch.object(tui, 'menu', return_value='quit') as shown, \
                mock.patch.object(installer, 'desktop_present', return_value=True), mock.patch.object(tui, 'recorded_profiles', return_value=('core',)), \
                mock.patch.object(tui, 'updates_screen', return_value=('back', None)):
            self.assertIsNone(tui.interface(None, plan(), False, 'updates'))
        shown.assert_called_once()

    def test_the_record_names_the_profiles_unless_the_desktop_was_removed(self):
        for record, expected in (({'profiles': ['gaming', 'core', 'apps']}, ('core', 'apps', 'gaming')), ({'profiles': ['radio']}, ('core', 'radio')),
                                 ({}, ()), ({'profiles': ['core'], 'uninstalled': True}, ())):
            with mock.patch.object(installer, 'load_record', return_value=record):
                self.assertEqual(tui.recorded_profiles(), expected)

    def test_the_flag_opens_the_updates_screen(self):
        with mock.patch('os.geteuid', return_value=1000), mock.patch('sys.stdin'), mock.patch('sys.stdout'), \
                mock.patch.object(installer, 'load_plan', return_value=plan()), mock.patch.object(installer, 'refuse'), \
                mock.patch('curses.wrapper', return_value=None) as wrapper, mock.patch('builtins.print'):
            tui.main(['--updates'])
            self.assertEqual(wrapper.call_args.args[3], 'updates')
            # A profile added comes with its default parts; one removed goes with all of them.
            tui.main(['--add', 'gaming'])
            self.assertEqual(wrapper.call_args.args[3:], ('profiles', ('gaming', 'gaming.steam', 'gaming.steam-hidpi', 'gaming.gamescope'), ()))
            tui.main(['--remove', 'gaming,radio'])
            self.assertEqual(wrapper.call_args.args[3:], ('removal', (), ('radio', 'gaming', 'gaming.steam', 'gaming.steam-hidpi', 'gaming.gamescope')))
        for arguments in (['--remove', 'core'], ['--add', 'gaming', '--remove', 'radio'], ['--updates', '--add', 'gaming'],
                          ['--profiles', 'core', '--add', 'gaming']):
            with mock.patch('sys.stderr'), self.assertRaises(SystemExit) as caught:
                tui.main(arguments)
            self.assertEqual(caught.exception.code, 2, arguments)


class ApplyUpdatesTests(unittest.TestCase):
    MANIFEST = "[[fedora.core.clones]]\nrepo = 'https://github.com/a/zsh-autocomplete'\ncommit = '" + 'a' * 40 + "'  # 26.08.04\n"

    def apply(self, picked):
        calls = []
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / 'manifest.toml'
            manifest.write_text(self.MANIFEST)
            with mock.patch.object(tui, 'MANIFEST', manifest), mock.patch.object(tui, 'REPO', Path(folder)), \
                    mock.patch('subprocess.run', side_effect=lambda command, **_: calls.append(command)), \
                    mock.patch.object(installer, 'query', return_value=reply('')), \
                    mock.patch.object(installer, 'load_plan', side_effect=lambda profiles, firmware=None: plan(profiles)) as loaded, \
                    mock.patch.object(installer, 'run_steps', side_effect=lambda current, preview, steps: calls.append([step.title for step in steps])), \
                    mock.patch.object(tui, 'keep_sudo'), mock.patch.object(tui, 'refresh_bar', side_effect=lambda: calls.append('bar')), \
                    mock.patch.object(bundle_module(), 'status', return_value='current'), mock.patch('builtins.print'):
                self.assertEqual(tui.apply_updates(plan(), picked), 0)
            return calls, manifest.read_text(), loaded

    def test_pins_go_into_the_manifest_and_their_steps_run_in_order(self):
        calls, text, loaded = self.apply([source('clones', pins=(PIN,)), source('system')])
        self.assertEqual(calls[0], ('sudo', '-v'))
        self.assertIn(f"commit = '{'b' * 40}'  # 26.09.01", text)
        loaded.assert_called_once()
        self.assertIn(['upgrade', 'clones'], calls)
        self.assertEqual(calls[-1], 'bar')

    def test_flatpak_alone_runs_no_installer_step(self):
        calls, text, loaded = self.apply([source('flatpak')])
        self.assertEqual(calls[1], ('sudo', 'flatpak', 'update', '--system', '-y', '--noninteractive'))
        self.assertFalse([call for call in calls if isinstance(call, list)])
        loaded.assert_not_called()
        self.assertEqual(text, self.MANIFEST)

    def test_no_bar_refresh_for_pins_alone(self):
        calls, _, _ = self.apply([source('clones', pins=(PIN,))])
        self.assertNotIn('bar', calls)

    def test_a_pull_fast_forwards_and_starts_again_on_the_updates_screen(self):
        with mock.patch('subprocess.run') as run, mock.patch('os.execv') as execv, mock.patch('builtins.print'), \
                mock.patch.object(tui, 'git', return_value=reply('abc\n')), mock.patch.object(tui, 'after_pull') as after, \
                mock.patch.object(tui, 'refresh_bar') as bar:
            tui.pull(plan())
        run.assert_called_once_with(('git', '-C', str(tui.REPO), 'merge', '--ff-only', '@{u}'), check=True)
        self.assertEqual(after.call_args.args[1], 'abc')
        # The bar no longer lists the commits just pulled.
        bar.assert_called_once_with('repository')
        self.assertEqual(execv.call_args.args[1][-2:], [str(tui.REPO / 'scripts/install-tui.py'), '--updates'])

    def after_pull(self, changed, session):
        environment = {'HYPRLAND_INSTANCE_SIGNATURE': 'sig'} if session else {}
        with mock.patch('subprocess.run') as run, mock.patch('builtins.print'), mock.patch('shutil.which', return_value='/usr/bin/stow'), \
                mock.patch.object(tui, 'git', return_value=reply('\n'.join(changed))), mock.patch.dict('os.environ', environment, clear=True):
            tui.after_pull(plan(), 'abc')
        return [call.args[0] for call in run.call_args_list]

    def test_a_pull_links_new_files_then_reloads_what_changed(self):
        calls = self.after_pull(['hypr/.config/hypr/config/new.lua', 'quickshell/.config/quickshell/desktop/New.qml'], True)
        self.assertEqual(calls[0], installer.stow_command(plan(), 'apply'))
        self.assertEqual(calls[1], ('hyprctl', 'reload'))
        self.assertEqual(calls[2][:2], ('hyprctl', 'eval'))
        self.assertIn('desktop-shell restart', calls[2][2])

    def test_a_pull_of_docs_only_links_and_restarts_nothing(self):
        self.assertEqual(self.after_pull(['docs/README.md'], True), [installer.stow_command(plan(), 'apply')])

    def test_outside_the_session_a_pull_only_links(self):
        self.assertEqual(self.after_pull(['quickshell/x.qml'], False), [installer.stow_command(plan(), 'apply')])

    def test_a_pull_that_brought_nothing_does_nothing(self):
        self.assertEqual(self.after_pull([], True), [])


def bundle_module():
    return tui.bundle


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


class LocaleTests(unittest.TestCase):
    def test_a_missing_locale_falls_back_to_the_character_set(self):
        calls = []

        def setlocale(category, name):
            calls.append((category, name))
            if category == tui.locale.LC_ALL:
                raise tui.locale.Error('unsupported locale setting')
        with mock.patch.object(tui.locale, 'setlocale', side_effect=setlocale):
            tui.set_locale()
        self.assertEqual(calls, [(tui.locale.LC_ALL, ''), (tui.locale.LC_CTYPE, '')])

    def test_c_utf8_when_nothing_else_is_installed(self):
        calls = []

        def setlocale(category, name):
            calls.append((category, name))
            if name == '':
                raise tui.locale.Error('unsupported locale setting')
        with mock.patch.object(tui.locale, 'setlocale', side_effect=setlocale):
            tui.set_locale()
        self.assertEqual(calls[-1], (tui.locale.LC_CTYPE, 'C.UTF-8'))

    def test_the_real_environment_never_raises(self):
        with mock.patch.dict('os.environ', {'LC_ALL': '', 'LC_MESSAGES': 'xx_XX.UTF-8'}):
            saved = tui.locale.setlocale(tui.locale.LC_ALL)
            try:
                tui.set_locale()
            finally:
                tui.locale.setlocale(tui.locale.LC_ALL, saved)


class HeadlessTests(unittest.TestCase):
    """--apply-updates: what Settings applies, without the screen."""

    def run_headless(self, keys, pullable=True):
        source = tui.Source('repository', 'Repository', '2 commits behind origin/main', [], '', pullable)
        with mock.patch.object(tui, 'recorded_profiles', return_value=('core',)), \
                mock.patch.object(installer, 'load_plan', return_value=plan(('core',))), mock.patch.object(installer, 'refuse'), \
                mock.patch.object(tui, 'repository_source', return_value=source), \
                mock.patch.object(tui, 'git', return_value=subprocess.CompletedProcess([], 0, 'abc\n', '')), \
                mock.patch('subprocess.run') as run, mock.patch.object(tui, 'after_pull') as after, \
                mock.patch.object(tui, 'refresh_bar'), mock.patch.object(tui.os, 'execv') as execv, \
                mock.patch.object(tui, 'apply_updates', return_value=0) as applied:
            status = tui.apply_headless(keys)
        return status, run, after, execv, applied

    def test_system_and_flatpak_are_the_screens_apply(self):
        status, run, _, execv, applied = self.run_headless(('flatpak', 'system'))
        self.assertEqual(status, 0)
        self.assertEqual([source.key for source in applied.call_args.args[1]], ['system', 'flatpak'])
        run.assert_not_called()
        execv.assert_not_called()

    def test_the_repository_goes_first_and_its_new_version_applies_the_rest(self):
        _, run, after, execv, applied = self.run_headless(('system', 'repository'))
        self.assertEqual(run.call_args.args[0][-2:], ('--ff-only', '@{u}'))
        after.assert_called_once()
        self.assertEqual(execv.call_args.args[1][-2:], ['--apply-updates', 'system'])
        applied.assert_not_called()

    def test_a_repository_that_cannot_fast_forward_is_refused(self):
        with self.assertRaises(SystemExit):
            self.run_headless(('repository',), pullable=False)

    def test_only_known_keys(self):
        with self.assertRaises(SystemExit):
            tui.apply_headless(('aur',))


if __name__ == '__main__':
    unittest.main()
