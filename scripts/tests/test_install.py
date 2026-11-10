#!/usr/bin/env python3
"""install-desktop.py must preview without changing anything, repeat safely, and refuse what it does not know."""
import atexit
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'scripts/install'))
spec = importlib.util.spec_from_file_location('install_desktop', REPO / 'scripts/install-desktop.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
import fedora  # noqa: E402

# Never the real state: apply writes its record there.
SANDBOX = tempfile.TemporaryDirectory()
atexit.register(SANDBOX.cleanup)
installer.STATE = Path(SANDBOX.name)
installer.RECORD = installer.STATE / 'install.json'
installer.UNITS = installer.STATE / 'units'
installer.INTERFACE = installer.STATE / 'interface-before-theme.ini'

MANIFEST = tomllib.loads((REPO / 'scripts/install/manifest.toml').read_text(encoding='utf-8'))
PROFILE_KEYS = {'repos', 'packages', 'swaps', 'stow', 'exclude', 'login_shell', 'clones', 'firmware', 'services', 'user_services', 'disable', 'files', 'groups', 'flatpaks', 'firewall_zone', 'auth', 'notes', 'archives', 'default'}
TABLE = {
    'repos': {'one': {'kind': 'copr', 'name': 'a/b', 'needs': ['dnf5-plugins']}},
    'core': {'repos': ['one'], 'packages': ['a', 'b'], 'exclude': ['tour'], 'services': ['s.service'], 'user_services': ['u.service'],
             'disable': ['d.socket'], 'files': [{'path': '/etc/x', 'content': '\nx\n'}], 'groups': ['g'], 'notes': ['first'],
             'login_shell': '/usr/bin/zsh', 'clones': [{'repo': 'https://example.com/p.git', 'commit': 'c' * 40, 'path': '.local/p'}]},
    'plugins': {'packages': ['b', 'c', 'old'], 'swaps': [['old', 'new']], 'stow': ['extra'], 'flatpaks': ['org.example.App'], 'firewall_zone': 'Zone', 'auth': ['with-fingerprint', 'custom/desktop-tablet'],
                'notes': ['second']},
}


def reply(stdout='', returncode=0):
    return subprocess.CompletedProcess((), returncode, stdout, '')


def fake_distro(pending=True):
    distro = mock.Mock(ADMIN_GROUP='wheel', AUTH_PROFILE='custom/desktop-tablet', PROTECTED=('python3', 'git-core'), MANAGER='dnf',
                       BASE_TARGET='multi-user.target')
    distro.repo_missing.return_value = pending
    distro.upgrades_pending.return_value = pending
    # Still to do: every package is missing but the one a swap replaces. Done: that one is gone, the rest is there.
    distro.missing.side_effect = lambda packages: [package for package in packages if (package != 'old') == pending]
    distro.installed.side_effect = lambda package: package != 'old' or pending
    distro.file_differs.return_value = pending
    distro.auth_pending.return_value = ['with-fingerprint'] if pending else []
    distro.auth_base.return_value = 'local'
    distro.requirements.return_value = set()
    distro.packages_from.return_value = set()
    distro.candidates.return_value = {}
    return distro


def plan(distro, commands=(), profiles=('core', 'plugins')):
    return installer.Plan(distro, '45', TABLE, list(commands), profiles)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.fedora = MANIFEST['fedora']
        # Every unit: each profile, and each part as a table of its own.
        table = installer.flatten_parts(copy.deepcopy(self.fedora))
        self.profiles = [table[name] for name in installer.units(table)]

    def test_every_profile_exists_and_uses_known_keys(self):
        for profile in self.profiles:
            self.assertLessEqual(set(profile), PROFILE_KEYS)

    def test_repos_are_defined_and_all_used(self):
        used = {name for profile in self.profiles for name in profile.get('repos', ())}
        self.assertEqual(used, set(self.fedora['repos']))

    def test_no_package_is_named_twice(self):
        for profile in self.profiles:
            self.assertEqual(len(profile.get('packages', ())), len(set(profile.get('packages', ()))))

    def test_the_login_depends_on_these_being_named(self):
        for package in ('gdm', 'hyprland-uwsm', 'dbus-tools', 'accountsservice', 'qt6-qtsvg', 'quickshell', 'stow'):
            self.assertIn(package, self.fedora['core']['packages'])

    def test_names_that_are_wrong_on_fedora_stay_out(self):
        packages = {package for profile in self.profiles for package in profile.get('packages', ())}
        self.assertFalse(packages & {'power-profiles-daemon', 'f44-backgrounds-base', 'nlohmann-json-devel', 'sof-firmware'})

    def test_zsh_is_the_login_shell_of_the_default_install(self):
        self.assertEqual(self.fedora['core']['login_shell'], '/usr/bin/zsh')
        for package in ('zsh', 'zsh-autosuggestions', 'zsh-syntax-highlighting', 'git-core', 'fzf'):
            self.assertIn(package, self.fedora['core']['packages'])

    def test_clones_are_pinned_to_full_commits_in_the_home(self):
        for clone in (clone for profile in self.profiles for clone in profile.get('clones', ())):
            self.assertRegex(clone['commit'], '^[0-9a-f]{40}$')
            self.assertTrue(clone['repo'].startswith('https://'))
            self.assertFalse(clone['path'].startswith(('/', '~')) or '..' in clone['path'])

    def test_the_prompt_settings_are_not_reset_after_p10k_zsh(self):
        # `p10k configure` appends a source of the upstream style to .zshrc, which unsets every change in p10k.zsh.
        self.assertNotIn('p10k-lean-8colors', (REPO / 'zsh/.config/zsh/.zshrc').read_text())

    def test_the_zsh_files_name_the_clones(self):
        zshrc = (REPO / 'zsh/.config/zsh/.zshrc').read_text() + (REPO / 'zsh/.config/zsh/p10k.zsh').read_text()
        for clone in self.fedora['core']['clones']:
            self.assertIn(clone['path'].removeprefix('.local/share/'), zshrc.replace('${XDG_DATA_HOME:-$HOME/.local/share}/', '').replace('$plugins', 'zsh/plugins'))

    def test_firmware_entries_are_complete(self):
        for item in (item for profile in self.profiles for item in profile.get('firmware', ())):
            self.assertLessEqual({'product', 'purpose', 'source', 'target', 'sha256', 'size'}, set(item))
            self.assertRegex(item['sha256'], '^[0-9a-f]{64}$')
            self.assertTrue(item['target'].startswith('/usr/lib/firmware/'))

    def test_passwords_have_a_service_on_every_edition(self):
        # Nothing starts it on Server: no preset, and no D-Bus activation.
        self.assertIn('oo7-daemon', self.fedora['core']['packages'])
        self.assertIn('oo7-daemon.service', self.fedora['core']['user_services'])

    def test_personal_apps_are_opt_in(self):
        for profile in ('apps', 'utils', 'assistant', 'containers', 'radio', 'gaming'):
            self.assertNotIn(profile, installer.DEFAULT_PROFILES.split(','))

    def test_no_flatpak_is_installed_for_you(self):
        self.assertFalse([profile for profile in self.profiles if profile.get('flatpaks')])

    def test_optional_stow_packages_exist(self):
        for name in (name for profile in self.profiles for name in profile.get('stow', ())):
            self.assertTrue((REPO / name).is_dir(), name)

    def test_swaps_are_pairs(self):
        for pair in (pair for profile in self.profiles for pair in profile.get('swaps', ())):
            self.assertEqual(len(pair), 2)


class RefusalTests(unittest.TestCase):
    def assert_refused(self, release, words):
        with self.assertRaises(SystemExit) as caught:
            installer.load_plan(('core',), release)
        self.assertIn(words, str(caught.exception))

    def test_an_unknown_distribution(self):
        self.assert_refused({'ID': 'debian', 'VERSION_ID': '13'}, 'not verified')

    def test_the_verify_table_is_not_a_distribution(self):
        self.assert_refused({'ID': 'verify', 'VERSION_ID': '1'}, 'not verified')

    def test_an_older_fedora(self):
        self.assert_refused({'ID': 'fedora', 'VERSION_ID': '44'}, 'fedora 44 is not verified')

    def test_a_verified_release_loads_its_module(self):
        loaded = installer.load_plan(('core',), {'ID': 'fedora', 'VERSION_ID': '45'})
        self.assertIs(loaded.distro, fedora)

    def test_root(self):
        with mock.patch('os.geteuid', return_value=0), self.assertRaises(SystemExit) as caught:
            installer.main(['dry-run'])
        self.assertIn('desktop user', str(caught.exception))

    def assert_usage_error(self, profiles):
        with mock.patch('os.geteuid', return_value=1000), mock.patch.object(installer, 'load_plan') as load, \
                mock.patch('sys.stderr'), self.assertRaises(SystemExit) as caught:
            installer.main(['dry-run', '--profiles', profiles])
        self.assertEqual(caught.exception.code, 2)
        load.assert_not_called()

    def test_profiles_need_core(self):
        self.assert_usage_error('apps')

    def test_unknown_profiles(self):
        self.assert_usage_error('core,games')

    def test_a_user_outside_the_admin_group(self):
        with mock.patch.object(installer, 'member', return_value=False), self.assertRaises(SystemExit) as caught:
            installer.preflight(plan(fake_distro()))
        self.assertIn('wheel', str(caught.exception))

    def test_another_architecture(self):
        with mock.patch('platform.machine', return_value='aarch64'), self.assertRaises(SystemExit):
            installer.preflight(plan(fake_distro()))


class WarningTests(unittest.TestCase):
    def warnings(self, free, source='/dev/mapper/fedora-root', home='/home/angelo', base='local'):
        distro = fake_distro()
        distro.auth_base.return_value = base
        usage = mock.Mock(free=free)
        with mock.patch.object(installer, 'member', return_value=True), mock.patch('shutil.disk_usage', return_value=usage), \
                mock.patch.object(installer, 'query', return_value=reply(source)), \
                mock.patch.object(Path, 'home', return_value=Path(home)), mock.patch('builtins.print') as printed:
            installer.preflight(plan(distro))
        return ' '.join(call.args[0] for call in printed.call_args_list)

    def test_enough_room_says_nothing(self):
        self.assertEqual(self.warnings(40 * 2**30), '')

    def test_a_small_root_on_lvm_gets_the_command_that_grows_it(self):
        text = self.warnings(10 * 2**30)
        self.assertIn('Only 10 GiB', text)
        self.assertIn('lvextend -r -l +100%FREE /dev/mapper/fedora-root', text)

    def test_a_small_root_elsewhere_gets_no_lvm_command(self):
        self.assertNotIn('lvextend', self.warnings(10 * 2**30, '/dev/nvme0n1p3'))

    def test_another_home_says_nothing(self):
        self.assertEqual(self.warnings(40 * 2**30, home='/home/someone'), '')

    def test_an_unexpected_auth_profile(self):
        self.assertIn('sssd', self.warnings(40 * 2**30, base='sssd'))


class StepTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        base = Path(folder.name)
        self.autostart = base / 'autostart/finish.desktop'
        self.stamp = base / 'stamp.json'
        self.record = base / 'state/install.json'
        for target, value in (('AUTOSTART', self.autostart), ('STAMP', self.stamp), ('RECORD', self.record), ('STATE', base / 'state')):
            patcher = mock.patch.object(installer, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # Clones are created under the home: a temporary one, never the real home.
        (base / 'home').mkdir()
        home = mock.patch.object(Path, 'home', return_value=base / 'home')
        home.start()
        self.addCleanup(home.stop)
        self.calls = []
        for name, value in (('getpass.getuser', 'angelo'), ('shutil.which', '/usr/bin/tool'), ('builtins.print', None)):
            patcher = mock.patch(name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # No desktop from before: the real links in this home would make apply rebuild a record from the history.
        for name in ('plugin_guard', 'linked_files'):
            patcher = mock.patch.object(installer, name, return_value=[])
            patcher.start()
            self.addCleanup(patcher.stop)

    def system(self, pending, booted=True):
        """The answers of a machine with everything still to do, or with everything done."""
        def query(*command):
            self.calls.append(command)
            if command[:3] == ('systemctl', '--global', 'is-enabled'):
                return reply('disabled' if pending else 'enabled')
            if command[:2] == ('systemctl', 'is-enabled'):
                done = command[2] != 'd.socket'
                return reply(('enabled' if done else 'disabled') if not pending else ('disabled' if done else 'enabled'))
            if command[:2] == ('systemctl', 'get-default'):
                return reply('multi-user.target' if pending else 'graphical.target')
            if command[0] == 'busctl':
                return reply('s "other"' if pending else 'o "/user" s "hyprland-uwsm"')
            if command[0] == 'firewall-cmd':
                return reply('FedoraServer' if pending else 'Zone')
            if command[0] == 'flatpak':
                return reply('' if pending else 'org.example.App')
            if command[0] == 'git' and 'status' in command:
                return reply('', 128 if pending else 0)
            if command[0] == 'git':
                return reply('' if pending else 'c' * 40, 128 if pending else 0)
            return reply('LINK: a => b\n' if pending else 'WARNING: in simulation mode\n')
        group = mock.Mock(gr_mem=[] if pending else ['angelo'])
        patches = [mock.patch.object(installer, 'query', side_effect=query), mock.patch('grp.getgrnam', return_value=group),
                   mock.patch.object(installer, 'login_shell', return_value='/bin/bash' if pending else '/usr/bin/zsh'),
                   mock.patch.object(installer, 'booted', return_value=booted)]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_profiles_merge_in_order_without_repeats(self):
        self.assertEqual(installer.merged(plan(fake_distro()), 'packages'), ['a', 'b', 'c', 'old'])

    def test_a_tool_that_is_not_installed_yet_is_an_empty_answer(self):
        result = installer.query('this-command-does-not-exist-here')
        self.assertEqual((result.returncode, result.stdout), (127, ''))

    def test_a_preview_changes_nothing(self):
        self.system(True)
        distro = fake_distro()
        with mock.patch('subprocess.run') as run:
            done = installer.run_steps(plan(distro), True)
        # All but verify (its commands are found here), firmware (FirmwareTests covers it), aur (test_install_arch.py)
        # and archives (ArchiveTests).
        self.assertEqual(done, len(installer.STEPS) - 4)
        run.assert_not_called()
        for change in (distro.sudo, distro.add_repo, distro.upgrade, distro.install, distro.write_file, distro.auth_apply):
            change.assert_not_called()
        self.assertFalse(self.autostart.exists())

    def test_a_preview_never_asks_for_sudo(self):
        self.system(True)
        installer.run_steps(plan(fake_distro()), True)
        self.assertFalse([call for call in self.calls if 'sudo' in call])

    def test_a_second_run_does_nothing(self):
        self.system(False)
        distro = fake_distro(pending=False)
        self.stamp.write_text('{}')
        installer.save_record({'packages': ['a']})  # The first run's.
        with mock.patch('subprocess.run') as run:
            self.assertEqual(installer.run_steps(plan(distro), False), 0)
        run.assert_not_called()
        distro.sudo.assert_not_called()

    def test_stow_never_runs_under_sudo(self):
        distro = fake_distro()
        with mock.patch('subprocess.run') as run:
            installer.stow_apply(plan(distro, profiles=('core',)), ['LINK: a'])
        self.assertEqual(run.call_args.args[0], (str(REPO / 'scripts/stow.py'), 'apply'))
        distro.sudo.assert_not_called()

    def test_stow_links_the_optional_packages_of_the_profiles(self):
        with mock.patch('subprocess.run') as run:
            installer.stow_apply(plan(fake_distro(), profiles=('core', 'plugins')), ['LINK: a'])
        self.assertEqual(run.call_args.args[0], (str(REPO / 'scripts/stow.py'), 'apply', '--with', 'extra'))

    def test_a_swapped_package_is_replaced_never_installed(self):
        current = plan(fake_distro())
        self.assertEqual(installer.wanted_packages(current), ['a', 'b', 'c', 'new'])
        self.assertEqual(installer.swaps_pending(current), ['old -> new'])

    def test_a_swap_is_done_once_the_old_package_is_gone(self):
        self.assertEqual(installer.swaps_pending(plan(fake_distro(pending=False))), [])

    def test_swaps_come_before_the_packages(self):
        titles = [step.title for step in installer.STEPS]
        self.assertLess(titles.index('swaps'), titles.index('packages'))

    def test_the_install_keeps_the_excluded_packages_out(self):
        distro = fake_distro()
        installer.packages_apply(plan(distro), ['a'])
        distro.install.assert_called_once_with(['a'], ['tour'])

    def test_swaps_apply_what_is_pending(self):
        distro = fake_distro()
        installer.swaps_apply(plan(distro), ['old -> new'])
        distro.swap.assert_called_once_with('old', 'new')

    def test_the_login_shell_is_set_with_usermod(self):
        distro = fake_distro()
        current = installer.Plan(distro, '45', {'core': {'login_shell': '/usr/bin/zsh'}}, [], ('core',))
        with mock.patch.object(installer, 'login_shell', return_value='/bin/bash'):
            pending = installer.shell_pending(current)
        self.assertEqual(pending, ['/usr/bin/zsh'])
        with mock.patch('getpass.getuser', return_value='someone'):
            installer.shell_apply(current, pending)
        distro.sudo.assert_called_once_with('usermod', '--shell', '/usr/bin/zsh', 'someone')

    def test_the_login_shell_is_done_once_set(self):
        current = installer.Plan(fake_distro(), '45', {'core': {'login_shell': '/usr/bin/zsh'}}, [], ('core',))
        with mock.patch.object(installer, 'login_shell', return_value='/usr/bin/zsh'):
            self.assertEqual(installer.shell_pending(current), [])

    def clone_plan(self):
        clone = {'repo': 'https://example.com/p.git', 'commit': 'a' * 40, 'path': '.local/share/p'}
        return installer.Plan(fake_distro(), '45', {'core': {'clones': [clone]}}, [], ('core',)), clone

    def test_a_clone_is_pending_until_it_is_at_its_commit(self):
        current, clone = self.clone_plan()
        for head, expected in (('', ['.local/share/p']), ('b' * 40, ['.local/share/p']), ('a' * 40, [])):
            with mock.patch.object(installer, 'clone_head', return_value=head):
                self.assertEqual(installer.clones_pending(current), expected)

    def test_a_clone_fetches_only_its_commit_as_the_user(self):
        current, clone = self.clone_plan()
        with tempfile.TemporaryDirectory() as home, mock.patch.object(Path, 'home', return_value=Path(home)), \
                mock.patch('subprocess.run') as run:
            installer.clones_apply(current, ['.local/share/p'])
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[0][-2:], ('init', '-q'))
        self.assertIn(('fetch', '-q', '--depth', '1', clone['repo'], clone['commit']), [c[3:] for c in commands])
        self.assertEqual(commands[-1][-1], clone['commit'])
        self.assertFalse([c for c in commands if 'sudo' in c])

    def git(self, head, clean):
        def query(*command):
            if 'status' in command:
                return reply('' if clean else ' M file', 0)
            return reply(head, 0 if head else 128)
        return mock.patch.object(installer, 'query', side_effect=query)

    def test_a_folder_of_the_user_is_never_forced_to_the_clone(self):
        current, clone = self.clone_plan()
        with tempfile.TemporaryDirectory() as home, mock.patch.object(Path, 'home', return_value=Path(home)):
            (Path(home) / clone['path']).mkdir(parents=True)
            (Path(home) / clone['path'] / 'mine').write_text('mine')
            with self.git('', True):
                self.assertEqual(installer.clones_pending(current), [])
                self.assertEqual(installer.clones_kept(current), [clone['path']])
            (Path(home) / clone['path'] / '.git').mkdir()
            with self.git('b' * 40, False):
                self.assertEqual(installer.clones_pending(current), [])
            with self.git('b' * 40, True):
                self.assertEqual(installer.clones_pending(current), [clone['path']])
            # It was there before: apply does not note it, so uninstall never removes it.
            record = {}
            installer.clones_remember(current, [clone['path']], record)
            self.assertEqual(record['clones'], [])

    def test_only_an_unchanged_named_clone_is_undone(self):
        current, clone = self.clone_plan()
        with tempfile.TemporaryDirectory() as home, mock.patch.object(Path, 'home', return_value=Path(home)):
            (Path(home) / clone['path']).mkdir(parents=True)
            (Path(home) / 'other').mkdir()
            undo = current._replace(record={'clones': [clone['path'], '', 'other', '../x']})
            with self.git(clone['commit'], True):
                self.assertEqual(installer.clones_undoable(undo), ([clone['path']], []))
            with self.git(clone['commit'], False):
                self.assertEqual(installer.clones_undoable(undo), ([], [clone['path']]))
            with self.git('b' * 40, True):
                self.assertEqual(installer.unclones_pending(undo), [])

    def test_stow_is_pending_until_it_exists(self):
        with mock.patch('shutil.which', return_value=None):
            self.assertIn('not installed', installer.stow_pending(plan(fake_distro()))[0])

    def test_files_stow_would_back_up_are_pending_not_an_error(self):
        output = 'Will back up on apply: /home/u/.config/kitty/kitty.conf\nLINK: .config/kitty/kitty.conf => x\n'
        with mock.patch.object(installer, 'query', return_value=mock.Mock(returncode=0, stdout=output, stderr='')):
            self.assertEqual(installer.stow_pending(plan(fake_distro())),
                             ['Will back up on apply: /home/u/.config/kitty/kitty.conf', 'LINK: .config/kitty/kitty.conf => x'])

    def test_a_stow_error_stops_the_run(self):
        with mock.patch.object(installer, 'query', return_value=mock.Mock(returncode=2, stdout='', stderr='Parent must be a real directory')):
            with self.assertRaises(RuntimeError) as caught:
                installer.stow_pending(plan(fake_distro()))
        self.assertIn('real directory', str(caught.exception))

    def test_services_are_never_stopped_or_started_here(self):
        self.system(True)
        distro = fake_distro()
        installer.services_apply(plan(distro), installer.services_pending(plan(distro)))
        commands = [call.args for call in distro.sudo.call_args_list]
        self.assertEqual(commands, [('systemctl', 'enable', 's.service'), ('systemctl', 'disable', 'd.socket'),
                                    ('systemctl', 'enable', '--global', 'u.service')])

    def test_a_unit_that_is_not_there_needs_no_disabling(self):
        with mock.patch.object(installer, 'unit_state', return_value=''), mock.patch.object(installer, 'query', return_value=reply('enabled')):
            pending = installer.services_pending(plan(fake_distro()))
        self.assertEqual(pending, ['enable s.service'])

    def test_a_static_unit_needs_no_enabling(self):
        with mock.patch.object(installer, 'unit_state', return_value='static'), mock.patch.object(installer, 'query', return_value=reply('enabled')):
            self.assertEqual(installer.services_pending(plan(fake_distro())), [])

    def test_user_services_are_enabled_for_everyone(self):
        with mock.patch.object(installer, 'unit_state', return_value='enabled'), mock.patch.object(installer, 'query', return_value=reply('disabled')):
            self.assertEqual(installer.services_pending(plan(fake_distro())), ['disable d.socket', 'enable --global u.service'])

    def test_a_container_skips_what_needs_a_running_system(self):
        self.system(True, booted=False)
        current = plan(fake_distro())
        self.assertEqual(installer.firewall_pending(current), [])
        self.assertEqual(installer.flatpak_pending(current), [])
        self.assertNotIn(installer.BOOT_SESSION, installer.boot_pending(current))

    def test_files_lose_the_leading_newline_of_the_manifest(self):
        distro = fake_distro()
        installer.files_apply(plan(distro), ['/etc/x'])
        distro.write_file.assert_called_once_with('/etc/x', 'x\n', '0644')

    def test_a_file_from_the_repository_keeps_its_mode(self):
        table = {'core': {'files': [{'path': '/usr/local/libexec/x', 'source': 'scripts/privileged/root-broker', 'mode': '0755'}]}}
        installer.resolve_files(table)
        item = table['core']['files'][0]
        self.assertEqual(item['content'], (installer.REPO / 'scripts/privileged/root-broker').read_text())
        distro = fake_distro()
        installer.files_apply(installer.Plan(distro, '45', table, [], ('core',)), ['/usr/local/libexec/x'])
        distro.write_file.assert_called_once_with('/usr/local/libexec/x', item['content'], '0755')

    def test_a_mode_is_four_octal_digits(self):
        with self.assertRaises(SystemExit):
            installer.resolve_files({'core': {'files': [{'path': '/x', 'content': 'x', 'mode': '755'}]}})

    def test_verify_stops_before_the_boot_step(self):
        self.system(True)
        distro = fake_distro()
        with mock.patch('shutil.which', side_effect=lambda name: None if name == 'Hyprland' else '/usr/bin/' + name), \
                mock.patch('subprocess.run'), self.assertRaises(RuntimeError):
            installer.run_steps(plan(distro, ['Hyprland']), False)
        self.assertNotIn(mock.call('systemctl', 'set-default', 'graphical.target'), distro.sudo.call_args_list)
        self.assertFalse(self.autostart.exists())

    def test_the_guard_is_checked_only_once_the_packages_exist(self):
        distro = fake_distro()
        installer.verify_pending(plan(distro))
        installer.plugin_guard.assert_not_called()
        distro.missing.side_effect = lambda packages: []
        installer.verify_pending(plan(distro))
        installer.plugin_guard.assert_called_once()

    def test_boot_is_the_last_step_and_verify_comes_before_it(self):
        self.assertEqual([step.title for step in installer.STEPS][-2:], ['verify', 'boot'])

    def test_the_packages_come_before_what_needs_them(self):
        titles = [step.title for step in installer.STEPS]
        self.assertLess(titles.index('repos'), titles.index('packages'))
        for title in ('files', 'services', 'auth', 'stow'):
            self.assertLess(titles.index('packages'), titles.index(title))

    def test_the_boot_step_sets_up_the_login(self):
        self.system(True)
        distro = fake_distro()
        current = plan(distro)
        installer.boot_apply(current, installer.boot_pending(current))
        commands = [call.args for call in distro.sudo.call_args_list]
        self.assertIn(('systemctl', 'enable', 'gdm.service'), commands)
        self.assertIn(('systemctl', 'set-default', 'graphical.target'), commands)
        self.assertEqual(commands[0][-3:], ('SetSession', 's', 'hyprland-uwsm'))
        self.assertIn('post --profiles core,plugins', self.autostart.read_text(encoding='utf-8'))

    def test_no_autostart_when_the_plugins_are_built(self):
        self.system(True)
        self.stamp.write_text('{}')
        self.assertNotIn(installer.BOOT_AUTOSTART, installer.boot_pending(plan(fake_distro())))

    def test_no_autostart_without_the_plugins_profile(self):
        self.system(True)
        self.assertNotIn(installer.BOOT_AUTOSTART, installer.boot_pending(plan(fake_distro(), profiles=('core',))))


class RecordTests(unittest.TestCase):
    setUp = StepTests.setUp
    system = StepTests.system

    def saved(self):
        return json.loads(installer.RECORD.read_text())

    def test_apply_notes_what_it_changes_and_what_was_there(self):
        self.system(True)
        with mock.patch('subprocess.run'):
            installer.run_steps(plan(fake_distro()), False)
        record = self.saved()
        self.assertEqual(record['packages'], ['dnf5-plugins', 'a', 'b', 'c', 'new'])
        self.assertEqual(record['swaps'], [['old', 'new']])
        self.assertEqual(record['repos'], ['one'])
        self.assertEqual(record['files'], {'/etc/x': None})
        self.assertEqual(record['login_shell'], '/bin/bash')
        self.assertEqual(record['firewall_zone'], 'FedoraServer')
        self.assertEqual(record['services'], {'enabled': ['s.service'], 'disabled': ['d.socket'], 'global': ['u.service']})
        self.assertEqual(record['boot'], {'session': 'other', 'gdm': 'disabled', 'target': 'multi-user.target'})
        self.assertEqual((record['groups'], record['clones'], record['auth']), (['g'], ['.local/p'], ['with-fingerprint']))
        self.assertEqual(record['profiles'], ['core', 'plugins'])

    def test_what_was_there_first_wins(self):
        record = {'login_shell': '/bin/bash', 'files': {'/etc/x': None}}
        with mock.patch.object(installer, 'login_shell', return_value='/usr/bin/zsh'):
            installer.shell_remember(plan(fake_distro()), ['/usr/bin/zsh'], record)
        installer.files_remember(plan(fake_distro()), ['/etc/x'], record)
        self.assertEqual({key: record[key] for key in ('login_shell', 'files')}, {'login_shell': '/bin/bash', 'files': {'/etc/x': None}})
        # What apply writes now, so a later manifest change does not make it look edited.
        self.assertEqual(record['written'], {'/etc/x': installer.text_digest('x\n')})

    def test_a_file_from_an_older_manifest_is_still_ours(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'x'
            path.write_text('old content\n')
            table = {**TABLE, 'core': {**TABLE['core'], 'files': [{'path': str(path), 'content': 'new content\n'}]}}
            record = {'files': {str(path): None}, 'written': {str(path): installer.text_digest('old content\n')}}
            current = installer.Plan(fake_distro(), '45', table, [], ('core',), None, record)
            self.assertEqual(installer.changed_files(current), ([str(path)], []))
            path.write_text('edited by hand\n')
            self.assertEqual(installer.changed_files(current), ([], [str(path)]))

    def test_the_record_is_written_before_the_step_runs(self):
        self.system(True)
        seen = []
        failing = installer.Step('packages', lambda current: ['a'], lambda current, items: seen.append(self.saved()['packages']),
                                 installer.packages_remember)
        installer.run_steps(plan(fake_distro()), False, (failing,))
        self.assertEqual(seen, [['a']])

    def test_a_preview_writes_no_record(self):
        self.system(True)
        installer.run_steps(plan(fake_distro()), True)
        self.assertFalse(installer.RECORD.exists())


class UninstallTests(unittest.TestCase):
    setUp = StepTests.setUp
    system = StepTests.system

    def sandbox(self):
        # Uninstall deletes files: everything it may touch lives in a temporary home.
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        home = Path(folder.name)
        self.plugin_files = [home / 'bundles', home / 'stamp.json']
        for path in self.plugin_files:
            path.write_text('')
        patches = [mock.patch.object(Path, 'home', return_value=home), mock.patch.object(installer, 'plugin_paths', return_value=self.plugin_files),
                   mock.patch.object(installer.bundle, 'CACHE', home / 'cache'), mock.patch.object(installer, 'linked_files', return_value=[]),
                   mock.patch.object(installer, 'backups', return_value=[])]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        (home / '.local/p').mkdir(parents=True)
        self.file = home / 'etc-x'
        self.file.write_text('x\n')
        return home

    def removal(self, record):
        distro = fake_distro(pending=False)
        distro.installed_names.side_effect = lambda specs: [spec + '.x86_64' for spec in specs]
        distro.removal.side_effect = lambda names: names + ['dependency.x86_64', 'mine.x86_64'] if names else []
        distro.installed_by_hand.side_effect = lambda names: {'mine.x86_64'} & set(names)
        distro.installed.side_effect = lambda package: package == 'new'
        # The manifest writes the sandbox file, as it writes /etc/x.
        table = {**TABLE, 'core': {**TABLE['core'], 'files': [{'path': str(getattr(self, 'file', '/etc/x')), 'content': '\nx\n'}]}}
        return installer.Plan(distro, '45', table, [], ('core',), None, record)

    def full_record(self):
        return {'packages': ['a', 'python3', 'new'], 'swaps': [['old', 'new']], 'repos': ['one'], 'files': {str(self.file): None},
                'login_shell': '/bin/bash', 'firewall_zone': 'FedoraServer', 'groups': ['g'], 'clones': ['.local/p'],
                'services': {'enabled': ['s.service'], 'disabled': ['d.socket'], 'global': ['u.service']}, 'auth': ['with-fingerprint'],
                'boot': {'session': 'other', 'gdm': 'disabled', 'target': 'multi-user.target'}}

    def test_everything_recorded_is_undone(self):
        self.system(False)
        home = self.sandbox()
        current = self.removal(self.full_record())
        with mock.patch('subprocess.run'), mock.patch.object(installer, 'login_shell', return_value='/usr/bin/zsh'):
            installer.run_steps(current, False, installer.UNSTEPS)
        distro = current.distro
        commands = [call.args for call in distro.sudo.call_args_list]
        self.assertEqual(commands[0][-3:], ('SetSession', 's', 'other'))
        for command in (('systemctl', 'disable', 'gdm.service'), ('systemctl', 'set-default', 'multi-user.target'),
                        ('systemctl', 'disable', 's.service'), ('systemctl', 'enable', 'd.socket'), ('systemctl', 'disable', '--global', 'u.service'),
                        ('firewall-cmd', '--set-default-zone=FedoraServer'), ('usermod', '--shell', '/bin/bash', 'angelo'),
                        ('gpasswd', '-d', 'angelo', 'g'), ('rm', '-f', '--', str(self.file))):
            self.assertIn(command, commands)
        distro.auth_revert.assert_called_once_with(['with-fingerprint'], REPO / 'scripts/tablet-auth.sh')
        # python3 is a prerequisite and new goes back by swap: neither is removed.
        distro.remove.assert_called_once_with(['a.x86_64'])
        distro.swap.assert_called_once_with('new', 'old')
        distro.remove_repo.assert_called_once_with(TABLE['repos']['one'])
        self.assertFalse((home / '.local/p').exists())
        self.assertFalse([path for path in self.plugin_files if path.exists()])

    def test_the_preview_shows_what_dnf_would_take_and_changes_nothing(self):
        self.system(False)
        self.sandbox()
        current = self.removal(self.full_record())
        with mock.patch('subprocess.run') as run, mock.patch.object(installer, 'login_shell', return_value='/usr/bin/zsh'):
            installer.run_steps(current, True, installer.UNSTEPS)
            self.assertEqual(installer.unpackages_pending(current),
                             ['a.x86_64', 'dependency.x86_64', 'mine.x86_64  (installed by hand: it needs one of the others)'])
        run.assert_not_called()
        current.distro.sudo.assert_not_called()
        current.distro.remove.assert_not_called()
        self.assertTrue(self.file.exists())

    def test_a_file_that_was_there_gets_its_content_back(self):
        self.sandbox()
        current = self.removal({'files': {str(self.file): 'before\n'}})
        installer.unfiles_apply(current, installer.unfiles_pending(current))
        current.distro.write_file.assert_called_once_with(str(self.file), 'before\n')

    def test_a_file_edited_since_the_install_stays(self):
        self.system(False)
        self.sandbox()
        self.file.write_text('x\nmy browser\n')
        current = self.removal({'files': {str(self.file): None}})
        self.assertEqual(installer.unfiles_pending(current), [])
        self.assertIn(f'{self.file} changed since the install: it stays as it is.', installer.record_notes(current))

    def test_choices_made_since_the_install_stay(self):
        self.system(False)
        self.sandbox()
        current = self.removal({'login_shell': '/bin/bash', 'firewall_zone': 'FedoraServer'})
        with mock.patch.object(installer, 'login_shell', return_value='/usr/bin/fish'), \
                mock.patch.object(installer, 'default_zone_now', return_value='home'):
            self.assertEqual((installer.unshell_pending(current), installer.unfirewall_pending(current)), ([], []))
            notes = installer.record_notes(current)
        self.assertTrue(any('/usr/bin/fish' in note for note in notes))
        self.assertTrue(any('home' in note for note in notes))

    def test_a_package_installed_by_hand_keeps_what_it_needs(self):
        self.sandbox()
        current = self.removal({'packages': ['a', 'b']})
        current.distro.removal.side_effect = lambda names: names + (['mine.x86_64'] if 'a.x86_64' in names else [])
        current.distro.requirements.side_effect = lambda names: {'a.x86_64', 'glibc.x86_64'}
        self.assertEqual(installer.unpackages_pending(current), ['b.x86_64', 'keep a.x86_64  (a package installed by hand needs it)'])
        installer.unpackages_apply(current, [])
        current.distro.remove.assert_called_once_with(['b.x86_64'])

    def test_only_packages_to_keep_is_no_work(self):
        # An uninstall run again: what it kept for a package installed by hand is still there, and that is not work.
        self.sandbox()
        current = self.removal({'packages': ['a']})
        current.distro.removal.side_effect = lambda names: names + (['mine.x86_64'] if 'a.x86_64' in names else [])
        current.distro.requirements.side_effect = lambda names: {'a.x86_64', 'glibc.x86_64'}
        self.assertEqual(installer.unpackages_pending(current), [])

    def test_a_repository_packages_still_come_from_stays(self):
        self.sandbox()
        current = self.removal({'packages': ['a'], 'repos': ['one']})
        current.distro.repo_missing.return_value = False
        current.distro.packages_from.return_value = {'a.x86_64', 'akmod-nvidia.x86_64'}
        self.assertEqual(installer.unrepos_pending(current), [])
        self.assertIn('The one repository stays: it still provides akmod-nvidia.x86_64.', installer.record_notes(current))
        current.distro.packages_from.return_value = {'a.x86_64'}
        self.assertEqual(installer.unrepos_pending(current), ['one'])

    def test_the_recorded_profiles_are_a_list_or_nobody_can_tell(self):
        self.assertEqual(installer.recorded_profiles({'profiles': ['core', 'radio']}), ['core', 'radio'])
        for record in ({}, {'profiles': 'core'}, {'profiles': ['core'], 'uninstalled': True}):
            with self.subTest(record=record):
                self.assertIsNone(installer.recorded_profiles(record))

    def test_a_record_that_knows_only_the_profiles_is_rebuilt(self):
        installer.save_record({'profiles': ['core']})
        with mock.patch.object(installer, 'reconstruct', return_value={'reconstructed': True}) as rebuilt:
            current = installer.uninstall_plan(plan(fake_distro()))
        rebuilt.assert_called_once()
        self.assertEqual(current.record, {'reconstructed': True})

    def test_an_unreadable_record_is_set_aside_and_rebuilt(self):
        installer.RECORD.parent.mkdir(parents=True, exist_ok=True)
        installer.RECORD.write_text('{"packages": [')
        with mock.patch.object(installer, 'reconstruct', return_value={'reconstructed': True}), mock.patch('sys.stderr'):
            installer.uninstall_plan(plan(fake_distro()))
            self.assertTrue(installer.RECORD.exists())
            installer.uninstall_plan(plan(fake_distro()), preview=False)
        self.assertFalse(installer.RECORD.exists())
        self.assertEqual(installer.RECORD.with_name('install.json.unreadable').read_text(), '{"packages": [')

    def test_some_install_steps_still_set_aside_and_rebuild_the_record(self):
        # The Updates screen of the guided installer runs only the steps of the pins it moves.
        idle = installer.Step('clones', lambda current: [], None)
        other = installer.Step('packages', lambda current: [], None)
        installer.RECORD.parent.mkdir(parents=True, exist_ok=True)
        installer.RECORD.write_text('{"packages": [')
        with mock.patch.object(installer, 'reconstruct', return_value={'reconstructed': True, 'packages': ['a.x86_64']}) as rebuilt, \
                mock.patch.object(installer, 'desktop_present', return_value=True), \
                mock.patch.object(installer, 'STEPS', (other, idle)), mock.patch('sys.stderr'):
            installer.run_steps(plan(fake_distro()), False, (idle,))
        rebuilt.assert_called_once()
        self.assertEqual(installer.RECORD.with_name('install.json.unreadable').read_text(), '{"packages": [')
        saved = json.loads(installer.RECORD.read_text())
        self.assertEqual(saved['packages'], ['a.x86_64'])
        self.assertNotIn('profiles', saved, 'only a whole install records its profiles')

    def test_what_is_already_back_is_left_alone(self):
        self.system(True)
        self.sandbox()
        current = self.removal({'login_shell': '/bin/bash', 'firewall_zone': 'FedoraServer', 'groups': ['g'],
                                'boot': {'session': 'other', 'target': 'multi-user.target'}})
        with mock.patch.object(installer, 'login_shell', return_value='/bin/bash'):
            for step in (installer.unshell_pending, installer.unfirewall_pending, installer.ungroups_pending, installer.unboot_pending):
                self.assertEqual(step(current), [], step.__name__)

    def test_the_preview_counts_backups_behind_our_links(self):
        home = self.sandbox()
        folder = home / 'backups/1'
        for name in ('.zshrc', '.bashrc', '.profile'):
            (folder / name).parent.mkdir(parents=True, exist_ok=True)
            (folder / name).write_text('mine')
        (home / '.zshrc').symlink_to(home / 'etc-x')  # A Stow link, unlinked first.
        (home / '.bashrc').write_text('written since')  # A file of the user's: it stays.
        backups = [(folder, folder / name) for name in ('.zshrc', '.bashrc', '.profile')]
        with mock.patch.object(installer, 'linked_files', return_value=[home / '.zshrc']), \
                mock.patch.object(installer, 'backups', return_value=backups):
            items = installer.unstow_pending(self.removal({}))
        self.assertIn(f'put back 2 files Stow had moved to {installer.STATE / "backups"}', items)

    def test_the_plugin_cache_goes_whole_only_when_it_holds_nothing_else(self):
        home = self.sandbox()
        cache = home / 'cache'
        (cache / installer.bundle.REPOSITORY).mkdir(parents=True)
        (cache / 'headersRoot').mkdir()
        current = self.removal({})
        items = installer.unplugins_pending(current)
        installer.unplugins_apply(current, items)
        current.distro.sudo.assert_called_once_with('rm', '-rf', '--', str(cache))
        self.assertFalse([path for path in self.plugin_files if path.exists()])
        # A repository someone added by hand keeps the cache: only ours goes.
        (cache / 'someone-else').mkdir()
        current.distro.sudo.reset_mock()
        installer.unplugins_apply(current, [str(cache / installer.bundle.REPOSITORY)])
        current.distro.sudo.assert_called_once_with('rm', '-rf', '--', str(cache / installer.bundle.REPOSITORY))

    def test_saved_gnome_settings_go_back_and_the_file_goes(self):
        home = self.sandbox()
        saved = home / 'interface.ini'
        saved.write_text("org.gnome.desktop.interface color-scheme 'default'\norg.gnome.desktop.interface cursor-size 24\n")
        with mock.patch.object(installer, 'INTERFACE', saved), mock.patch('subprocess.run') as run:
            installer.unsettings_apply(self.removal({}), [])
        self.assertEqual([call.args[0] for call in run.call_args_list],
                         [('gsettings', 'set', 'org.gnome.desktop.interface', 'color-scheme', "'default'"),
                          ('gsettings', 'set', 'org.gnome.desktop.interface', 'cursor-size', '24')])
        self.assertFalse(saved.exists())

    def test_the_record_stays_marked_as_undone(self):
        current = self.removal({})
        installer.unstate_apply(current, installer.unstate_pending(current))
        self.assertEqual(installer.load_record(), {'uninstalled': True, 'version': 1})
        again = installer.uninstall_plan(installer.Plan(fake_distro(), '45', TABLE, [], ('core',)))
        self.assertEqual(installer.unstate_pending(again), [])
        current.distro.history.assert_not_called()

    def test_what_uninstall_left_stays_in_the_record_until_it_is_gone(self):
        current = self.removal({'packages': ['a', 'gone'], 'repos': ['one']})
        current.distro.installed.side_effect = lambda name: name == 'a'
        current.distro.repo_missing.return_value = False
        installer.unstate_apply(current, installer.unstate_pending(current))
        self.assertEqual(installer.load_record(), {'uninstalled': True, 'version': 1, 'packages': ['a'], 'repos': ['one']})
        again = current._replace(record=installer.load_record())
        self.assertEqual(installer.unstate_pending(again), [])  # Nothing changed: nothing to do.
        again.distro.installed.side_effect = lambda name: False  # Removed meanwhile by a second uninstall.
        self.assertTrue(installer.unstate_pending(again))
        installer.unstate_apply(again, [])
        self.assertEqual(installer.load_record(), {'uninstalled': True, 'version': 1, 'repos': ['one']})

    def test_an_apply_on_a_desktop_from_before_the_record_starts_from_the_history(self):
        self.system(False)
        installer.save_record({'profiles': ['core']})
        self.stamp.write_text('{}')
        with mock.patch.object(installer, 'reconstruct', return_value={'reconstructed': True, 'packages': ['a.x86_64']}), \
                mock.patch('subprocess.run'):
            installer.run_steps(plan(fake_distro(pending=False)), False)
        self.assertEqual(installer.load_record(), {'reconstructed': True, 'packages': ['a.x86_64'], 'profiles': ['core', 'plugins'],
                                                   'profiles_version': installer.bundle.PROFILES_VERSION})

    def test_a_new_install_after_an_uninstall_starts_a_new_record(self):
        self.system(True)
        installer.save_record({'uninstalled': True})
        with mock.patch('subprocess.run'):
            installer.run_steps(plan(fake_distro()), False)
        self.assertNotIn('uninstalled', installer.load_record())

    def test_the_order_keeps_the_system_usable(self):
        titles = [step.title for step in installer.UNSTEPS]
        # PAM and the login shell before the packages they point at; stow while it is installed.
        for title in ('auth', 'shell', 'stow', 'plugins', 'boot', 'services'):
            self.assertLess(titles.index(title), titles.index('packages'), title)
        self.assertLess(titles.index('packages'), titles.index('swaps'))
        self.assertLess(titles.index('swaps'), titles.index('repos'))
        self.assertEqual(titles[-1], 'record')

    def test_uninstall_waits_until_hyprland_is_gone(self):
        with mock.patch.object(installer, 'query', return_value=reply('1234')), self.assertRaises(SystemExit) as caught:
            installer.refuse_uninstall()
        self.assertIn('Ctrl+Alt+F3', str(caught.exception))
        with mock.patch.object(installer, 'query', return_value=reply('', 1)):
            installer.refuse_uninstall()

    def test_the_preview_is_allowed_inside_hyprland(self):
        with mock.patch('os.geteuid', return_value=1000), mock.patch.object(installer, 'load_plan', return_value=plan(fake_distro())), \
                mock.patch.object(installer, 'refuse'), mock.patch.object(installer, 'refuse_uninstall') as refused, \
                mock.patch.object(installer, 'uninstall_plan', side_effect=lambda current, preview: current._replace(record={})), \
                mock.patch.object(installer, 'run_steps', return_value=0) as steps, mock.patch('builtins.print'):
            installer.main(['dry-run', '--uninstall'])
            refused.assert_not_called()
            self.assertIs(steps.call_args.args[2], installer.UNSTEPS)
            installer.main(['apply', '--uninstall'])
            refused.assert_called_once()

    def test_uninstall_does_not_go_with_post(self):
        with mock.patch('sys.stderr'), self.assertRaises(SystemExit) as caught:
            installer.main(['post', '--uninstall'])
        self.assertEqual(caught.exception.code, 2)


# Three opt-in profiles over core: apps and gaming share a package and a repository.
PROFILE_TABLE = {
    'repos': {'one': {'kind': 'copr', 'name': 'a/b'}, 'two': {'kind': 'copr', 'name': 'c/d'}},
    'core': {'packages': ['a'], 'stow': []},
    'apps': {'repos': ['one', 'two'], 'packages': ['shared', 'apponly'], 'services': ['s.service'], 'groups': ['g'],
             'flatpaks': ['org.example.App'], 'files': [{'path': '/etc/apps', 'content': '\nx\n'}],
             'aur': [{'package': 'zen', 'version': '1'}]},
    'gaming': {'repos': ['one'], 'packages': ['shared', 'game'], 'swaps': [['old', 'new']], 'disable': ['d.socket'],
               'firewall_zone': 'Zone'},
    'gaming.steam-hidpi': {'stow': ['steam-hidpi']},
}


class FingerprintAuthTests(unittest.TestCase):
    """with-fingerprint comes with hardware.fingerprint; the tablet sign-in profile only with tablet."""
    TABLE = {'core': {}, 'hardware': {}, 'hardware.fingerprint': {'auth': ['with-fingerprint']},
             'tablet': {'auth': ['with-fingerprint', 'custom/desktop-tablet']}}

    def setUp(self):
        StepTests.setUp(self)

    def test_the_fingerprint_part_alone_asks_for_the_feature_only(self):
        distro = fake_distro()
        installer.auth_pending(installer.Plan(distro, '45', self.TABLE, [], ('core', 'hardware', 'hardware.fingerprint')))
        distro.auth_pending.assert_called_once_with(['with-fingerprint'])
        distro.auth_pending.reset_mock()
        self.assertEqual(installer.auth_pending(installer.Plan(distro, '45', self.TABLE, [], ('core', 'hardware'))), [])
        distro.auth_pending.assert_not_called()

    def test_removing_tablet_keeps_the_fingerprint_for_the_part_that_stays(self):
        record = {'profiles': ['core', 'hardware', 'hardware.fingerprint', 'tablet'], 'auth': ['with-fingerprint', 'custom/desktop-tablet']}
        installer.save_record(record)
        current = installer.Plan(fake_distro(), '45', self.TABLE, [], ('core',))
        self.assertEqual(installer.profile_record(current, record, ('tablet',))['auth'], ['custom/desktop-tablet'])
        both = installer.profile_record(current, record, ('tablet', 'hardware.fingerprint'))
        self.assertEqual(both['auth'], ['with-fingerprint', 'custom/desktop-tablet'])
        self.assertNotIn('auth', installer.profile_record(current, record, ('hardware.fingerprint',)))

    def test_the_fedora_manifest_splits_them(self):
        table = installer.flatten_parts(MANIFEST['fedora'])
        self.assertEqual(table['hardware.fingerprint']['auth'], ['with-fingerprint'])
        self.assertEqual(table['tablet']['auth'], ['with-fingerprint', 'custom/desktop-tablet'])


class NextStepsTests(unittest.TestCase):
    """What to do after an apply: a first install reboots, a change inside the desktop only when its steps need it."""

    def said(self, applied, running, profiles=('core',)):
        installer.APPLIED[:] = applied
        out = io.StringIO()
        with mock.patch.object(installer, 'hyprland_running', return_value=running), contextlib.redirect_stdout(out):
            installer.next_steps(installer.Plan(fake_distro(), '45', {}, [], profiles), len(applied))
        return out.getvalue().strip()

    def tearDown(self):
        installer.APPLIED.clear()

    def test_inside_the_desktop_only_what_the_steps_need(self):
        self.assertEqual(self.said(['packages', 'stow'], True), 'Done.')
        self.assertIn('Reboot', self.said(['packages', 'firmware'], True))
        self.assertIn('Log out and back in', self.said(['groups'], True))
        self.assertEqual(installer.restart_needed(), 'login')

    def test_a_first_install_reboots_to_the_login_screen(self):
        self.assertEqual(self.said(['packages', 'boot'], False), 'Done. Reboot to reach the login screen.')
        self.assertEqual(self.said([], True), 'Nothing to do.')

    def test_run_steps_remembers_what_it_applied(self):
        steps = (installer.Step('one', lambda plan: ['x'], lambda plan, items: None), installer.Step('two', lambda plan: [], None))
        current = installer.Plan(fake_distro(), '45', {}, [], ('core',))
        with mock.patch('builtins.print'):
            installer.run_steps(current, False, steps)
            self.assertEqual(installer.APPLIED, ['one'])
            installer.run_steps(current, True, steps)
        self.assertEqual(installer.APPLIED, [])


class ProfileRemovalTests(unittest.TestCase):
    setUp = StepTests.setUp
    system = StepTests.system

    def recorded(self, **changes):
        # The file apply wrote, as /etc/apps, in the temporary home.
        self.file = Path.home() / 'etc-apps'
        self.file.write_text('x\n')
        record = {'profiles': ['core', 'apps', 'gaming', 'gaming.steam-hidpi'], 'packages': ['a', 'shared', 'apponly', 'game', 'zen', 'new'],
                  'swaps': [['old', 'new']], 'repos': ['one', 'two'], 'files': {str(self.file): None},
                  'written': {str(self.file): installer.text_digest('x\n')},
                  'groups': ['g'], 'flatpaks': ['org.example.App'], 'firewall_zone': 'FedoraServer', 'login_shell': '/bin/bash',
                  'services': {'enabled': ['s.service'], 'disabled': ['d.socket'], 'global': []}}
        record.update(changes)
        installer.save_record(record)
        return record

    def plan(self, record, removed):
        distro = fake_distro(pending=False)
        distro.installed_names.side_effect = lambda specs: [spec + '.x86_64' for spec in specs]
        distro.removal.side_effect = lambda names: list(names)
        distro.installed_by_hand.return_value = set()
        removed_packages = set()
        distro.remove.side_effect = lambda names: removed_packages.update(name.rsplit('.', 1)[0] for name in names)
        distro.missing.side_effect = lambda packages: [package for package in packages if package in removed_packages]
        distro.sudo.side_effect = lambda *command: Path(command[-1]).unlink() if command[0] == 'rm' else None
        table = {**PROFILE_TABLE, 'apps': {**PROFILE_TABLE['apps'], 'files': [{'path': str(self.file), 'content': '\nx\n'}]}}
        current = installer.Plan(distro, '45', table, [], ('core',))
        return current._replace(record=installer.profile_record(current, record, removed))

    def test_only_what_no_profile_that_stays_names(self):
        narrowed = self.plan(self.recorded(), ('apps',)).record
        self.assertEqual(narrowed['removing'], ['apps'])
        # shared and the repository one stay for gaming.
        self.assertEqual((narrowed['packages'], narrowed['repos']), (['apponly', 'zen'], ['two']))
        self.assertEqual((narrowed['files'], narrowed['groups'], narrowed['flatpaks']), ({str(self.file): None}, ['g'], ['org.example.App']))
        self.assertEqual(narrowed['services'], {'enabled': ['s.service'], 'disabled': [], 'global': []})
        self.assertEqual(narrowed['swaps'], [])
        self.assertNotIn('firewall_zone', narrowed)
        self.assertNotIn('login_shell', narrowed)
        self.assertIn('shared', narrowed['staying'])

    def test_settings_and_swaps_go_with_the_last_profile_that_has_them(self):
        narrowed = self.plan(self.recorded(), ('gaming',)).record
        self.assertEqual((narrowed['packages'], narrowed['swaps']), (['game', 'new'], [['old', 'new']]))
        self.assertEqual((narrowed['firewall_zone'], narrowed['services']['disabled']), ('FedoraServer', ['d.socket']))
        self.assertEqual(narrowed['repos'], [])
        both = self.plan(self.recorded(), ('apps', 'gaming')).record
        self.assertEqual((sorted(both['packages']), both['repos']), (['apponly', 'game', 'new', 'shared', 'zen'], ['one', 'two']))

    def test_without_a_record_of_profiles_every_other_one_stays(self):
        self.assertEqual(installer.staying_profiles({}, ('apps',)), tuple(name for name in installer.manifest_units() if name != 'apps'))
        self.assertEqual(installer.staying_profiles({'profiles': ['core', 'apps', 'radio']}, ('apps',)), ('core', 'radio'))

    def test_core_is_not_a_profile_to_remove(self):
        self.assertFalse(installer.removable_profiles(('core',)))
        self.assertFalse(installer.removable_profiles(('apps', 'nope')))
        self.assertFalse(installer.removable_profiles(()))
        self.assertTrue(installer.removable_profiles(('apps', 'gaming')))
        with mock.patch('sys.stderr'), self.assertRaises(SystemExit) as caught:
            installer.main(['dry-run', '--remove', 'core'])
        self.assertEqual(caught.exception.code, 2)

    def test_removing_undoes_it_and_the_record_forgets_it(self):
        self.system(False)
        current = self.plan(self.recorded(), ('apps',))
        with mock.patch('subprocess.run'):
            installer.run_steps(current, False, installer.PROFILE_UNSTEPS)
        commands = [call.args for call in current.distro.sudo.call_args_list]
        self.assertFalse(self.file.exists())
        for command in (('systemctl', 'disable', 's.service'), ('gpasswd', '-d', 'angelo', 'g'), ('rm', '-f', '--', str(self.file)),
                        ('flatpak', 'uninstall', '-y', '--noninteractive', 'org.example.App')):
            self.assertIn(command, commands)
        self.assertNotIn(('systemctl', 'enable', 'd.socket'), commands)
        self.assertFalse([command for command in commands if command[0] == 'firewall-cmd'])
        current.distro.remove.assert_called_once_with(['apponly.x86_64', 'zen.x86_64'])
        current.distro.remove_repo.assert_called_once_with(PROFILE_TABLE['repos']['two'])
        current.distro.swap.assert_not_called()
        saved = json.loads(installer.RECORD.read_text())
        self.assertEqual(saved['profiles'], ['core', 'gaming', 'gaming.steam-hidpi'])
        self.assertEqual(saved['packages'], ['a', 'shared', 'game', 'new'])
        self.assertEqual((saved['files'], saved['written'], saved['services']['enabled']), ({}, {}, []))
        self.assertEqual(saved['firewall_zone'], 'FedoraServer')

    def test_packages_the_profiles_that_stay_need_stay(self):
        current = self.plan(self.recorded(), ('apps',))
        # dnf would take shared with apponly, as a dependent: shared stays, and so does what it needs.
        current.distro.removal.side_effect = lambda names: list(names) + ['shared.x86_64']
        current.distro.requirements.side_effect = lambda names: {'apponly.x86_64'} if 'shared.x86_64' in names else set()
        names, kept, _, _ = installer.removal_split(current)
        self.assertEqual((names, kept), (['zen.x86_64'], ['apponly.x86_64']))

    def test_the_profile_s_own_links_go_and_the_rest_stays(self):
        self.system(False)
        home = Path.home()
        source = next(path for path in sorted((REPO / 'steam-hidpi').rglob('*')) if path.is_file())
        mine = home / source.relative_to(REPO / 'steam-hidpi')
        core = home / '.config/hypr/hyprland.lua'
        for link, target in ((mine, source), (core, REPO / 'hypr/.config/hypr/hyprland.lua')):
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target)
        current = self.plan(self.recorded(), ('gaming.steam-hidpi',))
        with mock.patch.object(installer, 'backups', return_value=[]):
            self.assertEqual(installer.unprofile_stow_pending(current), [f'unlink {mine}'])
            installer.unprofile_stow_apply(current, [])
        self.assertFalse(mine.is_symlink())
        self.assertTrue(core.is_symlink())

    def test_the_plugin_builds_go_only_with_the_plugins_profile(self):
        current = self.plan(self.recorded(), ('apps',))
        with mock.patch.object(installer, 'unplugins_pending', return_value=['builds']):
            self.assertEqual(installer.unprofile_plugins_pending(current), [])
            self.assertEqual(installer.unprofile_plugins_pending(current._replace(record={**current.record, 'undone': ['plugins']})),
                             ['builds'])

    def test_the_plugins_profile_waits_until_hyprland_is_gone(self):
        with mock.patch('os.geteuid', return_value=1000), mock.patch.object(installer, 'load_plan', return_value=plan(fake_distro())), \
                mock.patch.object(installer, 'refuse'), mock.patch.object(installer, 'refuse_uninstall') as refused, \
                mock.patch.object(installer, 'removal_plan', side_effect=lambda current, removed, preview, keep: current._replace(record={})), \
                mock.patch.object(installer, 'record_notes', return_value=[]), \
                mock.patch.object(installer, 'run_steps', return_value=0) as steps, mock.patch('builtins.print'):
            installer.main(['apply', '--remove', 'apps'])
            refused.assert_not_called()
            self.assertIs(steps.call_args.args[2], installer.PROFILE_UNSTEPS)
            installer.main(['dry-run', '--remove', 'plugins'])
            refused.assert_not_called()
            installer.main(['apply', '--remove', 'plugins'])
            refused.assert_called_once()

    def test_a_profile_removed_already_has_nothing_left_to_undo(self):
        # gaming is no longer in the record: game, kept then because core needed it, is core's now.
        narrowed = self.plan(self.recorded(profiles=['core', 'apps']), ('gaming',)).record
        self.assertEqual((narrowed['removing'], narrowed['undone']), (['gaming'], []))
        self.assertEqual((narrowed['packages'], narrowed['swaps'], narrowed['services']['disabled']), ([], [], []))
        self.assertNotIn('firewall_zone', narrowed)

    def test_packages_that_only_stay_are_no_work(self):
        current = self.plan(self.recorded(), ('apps',))
        # shared needs apponly (and, first, zen too): dnf would take it with them.
        current.distro.removal.side_effect = lambda names: list(names) + (['shared.x86_64'] if set(names) & {'apponly.x86_64', 'zen.x86_64'} else [])
        current.distro.requirements.side_effect = lambda names: {'apponly.x86_64', 'zen.x86_64'} if 'shared.x86_64' in names else set()
        self.assertEqual(installer.unpackages_pending(current), [])
        current.distro.removal.side_effect = lambda names: list(names) + (['shared.x86_64'] if 'apponly.x86_64' in names else [])
        current.distro.requirements.side_effect = lambda names: {'apponly.x86_64'} if 'shared.x86_64' in names else set()
        self.assertEqual(installer.unpackages_pending(current), ['zen.x86_64', 'keep apponly.x86_64  (a package that stays needs it)'])

    def test_a_removal_records_what_is_there_without_a_record(self):
        # Herdr from its own installer: the record has no assistant, so the units file would hide the AI block.
        self.system(False)
        record = self.recorded()
        current = self.plan(record, ('apps',))
        current = current._replace(record=installer.profile_record(current, record, ('apps',), keep=('assistant', 'apps', 'core')))
        self.assertEqual(current.record['keeping'], ['assistant'])
        self.assertIn(f'note in {installer.RECORD} that assistant is installed, without a record so far',
                      installer.unprofile_record_pending(current))
        with mock.patch('subprocess.run'):
            installer.run_steps(current, False, installer.PROFILE_UNSTEPS)
        self.assertEqual(json.loads(installer.RECORD.read_text())['profiles'], ['core', 'gaming', 'gaming.steam-hidpi', 'assistant'])
        self.assertIn('assistant', installer.UNITS.read_text().split())

    def test_what_a_kept_unit_needs_stays(self):
        record = self.recorded()
        table = {**PROFILE_TABLE, 'assistant': {'packages': ['apponly']}}
        current = installer.Plan(fake_distro(pending=False), '45', table, [], ('core',))
        self.assertIn('apponly', installer.profile_record(current, record, ('apps',)).get('packages'))
        self.assertNotIn('apponly', installer.profile_record(current, record, ('apps',), keep=('assistant',))['packages'])

    def test_an_install_says_which_units_the_record_names_from_now_on(self):
        self.recorded()
        current = installer.Plan(fake_distro(pending=False), '45', PROFILE_TABLE, [], ('core', 'apps', 'gaming', 'gaming.steam-hidpi', 'radio'))
        self.assertEqual(installer.recording_notes(current), [f'{installer.RECORD} names radio from now on.'])
        installer.RECORD.unlink()
        self.assertEqual(installer.recording_notes(current), [])  # A first install: everything is new, nothing to say.

    def test_keep_goes_with_remove(self):
        for arguments in (['dry-run', '--keep', 'assistant'], ['dry-run', '--remove', 'apps', '--keep', 'nothing']):
            with mock.patch('sys.stderr'), self.assertRaises(SystemExit) as caught:
                installer.main(arguments)
            self.assertEqual(caught.exception.code, 2)

    def test_nothing_recorded_for_the_profile_is_nothing_to_do(self):
        self.recorded(profiles=['core', 'gaming'])
        current = self.plan(installer.load_record(), ('radio',))
        self.assertEqual(installer.unprofile_record_pending(current), [])


class ReconstructTests(unittest.TestCase):
    def reconstruct(self, base, installed, shell='/usr/bin/zsh', zone='Zone', session='s "hyprland-uwsm"', target='graphical.target'):
        distro = fake_distro(pending=False)
        distro.history.return_value = []
        distro.base_packages.return_value = set(base)
        distro.installed_names.side_effect = lambda specs: [spec + '.x86_64' for spec in specs if spec in installed]
        distro.installed.side_effect = lambda package: package in installed
        distro.default_zone.return_value = 'public'
        distro.owned.return_value = False
        distro.auth_reconstruct.return_value = []
        table = {**TABLE, 'core': {**TABLE['core'], 'packages': ['a', 'b', 'gdm']}}
        current = installer.Plan(distro, '45', table, [], ('core',))

        def query(*command):
            answers = {'firewall-cmd': zone, 'busctl': session, 'systemctl': target}
            return reply(answers.get(command[0], ''))
        with mock.patch.object(installer, 'PROFILES', ('core', 'plugins')), mock.patch.object(installer, 'query', side_effect=query), \
                mock.patch.object(installer, 'login_shell', return_value=shell), mock.patch.object(installer, 'booted', return_value=True), \
                mock.patch('shutil.which', return_value='/usr/bin/firewall-cmd'), mock.patch('grp.getgrnam', return_value=mock.Mock(gr_mem=[])):
            return installer.reconstruct(current)

    def test_only_what_came_after_the_system_install(self):
        record = self.reconstruct(base={'b.x86_64'}, installed={'a', 'b', 'gdm', 'c'})
        self.assertEqual(record['packages'], ['a.x86_64', 'gdm.x86_64', 'c.x86_64'])
        self.assertTrue(record['reconstructed'])

    def test_a_swap_only_when_the_old_package_came_with_the_system(self):
        self.assertEqual(self.reconstruct(base={'old.x86_64'}, installed={'new'})['swaps'], [['old', 'new']])
        record = self.reconstruct(base={'kernel.x86_64'}, installed={'new'})
        self.assertEqual(record['swaps'], [])
        self.assertIn('new.x86_64', record['packages'])

    def test_values_from_before_that_the_system_tells(self):
        record = self.reconstruct(base={'kernel.x86_64'}, installed={'gdm'})
        self.assertEqual(record['login_shell'], '/bin/bash')
        self.assertEqual(record['firewall_zone'], 'public')
        self.assertEqual(record['boot'], {'session': '', 'gdm': 'disabled', 'target': 'multi-user.target'})
        self.assertNotIn('services', record)

    def test_without_the_system_install_in_the_history_no_package_goes(self):
        record = self.reconstruct(base=set(), installed={'a', 'gdm', 'new'})
        self.assertEqual((record['packages'], record['swaps'], record['base_unknown']), ([], [], True))
        notes = installer.record_notes(plan(fake_distro())._replace(record={'base_unknown': True}))
        self.assertTrue(any('no package from before the record is removed' in note for note in notes))

    def test_a_display_manager_from_before_stays(self):
        record = self.reconstruct(base={'gdm.x86_64'}, installed={'gdm'}, shell='/bin/bash', zone='public')
        self.assertEqual(record['boot'], {'session': ''})
        self.assertNotIn('login_shell', record)
        self.assertNotIn('firewall_zone', record)


class FirmwareTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.base = Path(folder.name)
        self.blob = b'firmware bytes'
        self.vendor = self.base / 'softpaq/Driver/FWImage/blob_0207.bin'
        self.vendor.parent.mkdir(parents=True)
        self.vendor.write_bytes(self.blob)
        (self.base / 'softpaq/other.bin').write_bytes(b'x' * len(self.blob))
        self.target = self.base / 'lib/ish_lnlm.bin'
        import hashlib
        self.item = {'product': 'Laptop 14', 'purpose': 'Screen rotation', 'source': 'vendor package',
                     'target': str(self.target), 'sha256': hashlib.sha256(self.blob).hexdigest(), 'size': len(self.blob)}
        patcher = mock.patch.object(installer, 'dmi', return_value='Laptop 14')
        self.dmi = patcher.start()
        self.addCleanup(patcher.stop)

    def plan(self, firmware=None):
        return installer.Plan(fake_distro(), '45', {'hardware': {'firmware': [self.item]}}, [], ('hardware',), firmware)

    def test_only_the_blob_apply_put_there_is_removed(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.blob)
        current = self.plan()._replace(record={'firmware': {str(self.target): False, str(self.base / 'gone.bin'): False}})
        current.distro.owned.return_value = False
        self.assertEqual(installer.unfirmware_pending(current), [str(self.target)])
        current.distro.owned.return_value = True  # A package ships it now.
        self.assertEqual(installer.unfirmware_pending(current), [])
        current.distro.owned.return_value = False
        self.target.write_bytes(b'replaced since')
        self.assertEqual(installer.unfirmware_pending(current), [])

    def test_the_vendor_file_is_found_by_hash_whatever_its_name(self):
        self.assertEqual(installer.firmware_source(self.plan(str(self.base)), self.item), self.vendor)

    def test_without_a_directory_nothing_is_pending(self):
        self.assertEqual(installer.firmware_pending(self.plan()), [])

    def test_with_a_copy_it_is_pending_until_installed(self):
        self.assertEqual(installer.firmware_pending(self.plan(str(self.base))), [str(self.target)])
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.blob)
        self.assertEqual(installer.firmware_pending(self.plan(str(self.base))), [])

    def test_another_model_needs_nothing(self):
        self.dmi.return_value = 'Another laptop'
        self.assertEqual(installer.firmware_needed(self.plan(str(self.base))), [])

    def test_apply_installs_then_rebuilds_the_initramfs(self):
        current = self.plan(str(self.base))
        order = mock.Mock()
        current.distro.install_firmware = order.install
        current.distro.rebuild_initramfs = order.rebuild
        installer.firmware_apply(current, [str(self.target)])
        self.assertEqual(order.mock_calls, [mock.call.install(self.vendor, str(self.target)), mock.call.rebuild()])

    def warnings(self, firmware):
        current = self.plan(firmware)
        with mock.patch.object(installer, 'member', return_value=True), \
                mock.patch('shutil.disk_usage', return_value=mock.Mock(free=40 * 2**30)), mock.patch('builtins.print') as printed:
            installer.preflight(current)
        return ' '.join(call.args[0] for call in printed.call_args_list)

    def test_a_missing_blob_is_a_warning_that_names_the_option(self):
        text = self.warnings(None)
        self.assertIn('Screen rotation needs ish_lnlm.bin', text)
        self.assertIn('--firmware', text)

    def test_a_directory_without_the_blob_says_so(self):
        self.assertIn('has no copy of it', self.warnings(str(self.base / 'lib')))

    def test_the_firmware_comes_before_the_boot_step(self):
        titles = [step.title for step in installer.STEPS]
        self.assertLess(titles.index('packages'), titles.index('firmware'))
        self.assertLess(titles.index('firmware'), titles.index('boot'))


class PostTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.autostart = Path(folder.name) / 'finish.desktop'
        self.autostart.write_text('entry')
        patcher = mock.patch.object(installer, 'AUTOSTART', self.autostart)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch('builtins.print')
        self.print = patcher.start()
        self.addCleanup(patcher.stop)

    def post(self, session='abc', terminal=True, errors=''):
        environment = {'HYPRLAND_INSTANCE_SIGNATURE': session} if session else {}
        with mock.patch.dict('os.environ', environment, clear=True), mock.patch('sys.stdin.isatty', return_value=terminal), \
                mock.patch('subprocess.run') as self.run, mock.patch('subprocess.check_output', return_value=errors):
            installer.post(plan(fake_distro()))

    def test_success_removes_the_autostart_and_lists_the_manual_steps(self):
        self.post()
        self.assertFalse(self.autostart.exists())
        self.assertEqual(self.run.call_args_list[0].args[0], (str(REPO / 'scripts/install-hypr-plugins.py'),))
        printed = ' '.join(call.args[0] for call in self.print.call_args_list)
        self.assertIn('first', printed)
        self.assertIn('second', printed)

    def test_a_failed_build_keeps_the_autostart(self):
        failure = subprocess.CalledProcessError(1, 'hyprpm')
        with mock.patch.dict('os.environ', {'HYPRLAND_INSTANCE_SIGNATURE': 'abc'}), mock.patch('sys.stdin.isatty', return_value=True), \
                mock.patch('subprocess.run', side_effect=failure), self.assertRaises(subprocess.CalledProcessError):
            installer.post(plan(fake_distro()))
        self.assertTrue(self.autostart.exists())

    def test_config_errors_keep_the_autostart(self):
        with self.assertRaises(SystemExit):
            self.post(errors='line 3: bad')
        self.assertTrue(self.autostart.exists())

    def test_it_needs_the_session(self):
        with self.assertRaises(SystemExit):
            self.post(session='')
        self.assertTrue(self.autostart.exists())

    def test_it_needs_a_terminal(self):
        with self.assertRaises(SystemExit):
            self.post(terminal=False)
        self.assertTrue(self.autostart.exists())


class ReleaseTests(unittest.TestCase):
    def test_quotes_are_removed(self):
        with tempfile.NamedTemporaryFile('w', suffix='release') as file:
            file.write('ID=fedora\nVERSION_ID=45\nPRETTY_NAME="Fedora Linux 45 (Server Edition)"\n\n# note\n')
            file.flush()
            fields = installer.os_release(Path(file.name))
        self.assertEqual(fields['ID'], 'fedora')
        self.assertEqual(fields['VERSION_ID'], '45')
        self.assertEqual(fields['PRETTY_NAME'], 'Fedora Linux 45 (Server Edition)')


REFUSED = """Failed to resolve the transaction:
Problem 1: The operation would result in broken dependencies for the following protected packages: systemd-udev
Problem 2: installed package kmod-34.2-6.fc45.x86_64 requires /usr/bin/pkg-config, but none of the providers can be installed
  - installed package systemd-udev-262.1-1.fc45.x86_64 requires kmod >= 18-4, but none of the providers can be installed
  - conflicting requests
"""
REMOVED = """Package     Arch   Version         Repository      Size
Removing:
 udisks2     x86_64 0:2.11.2-1.fc45 fedora      3.0 MiB
Removing unused dependencies:
 libblockdev x86_64 0:3.5.0-5.fc45  fedora    385.2 KiB

Transaction Summary:
 Removing:           2 packages
Operation aborted by the user.
"""


class RemovalTests(unittest.TestCase):
    def answers(self, asked):
        def query(*command):
            asked.append(command)
            if command[:2] == ('dnf', 'remove'):
                if 'pkgconf-pkg-config.x86_64' in command:
                    return subprocess.CompletedProcess(command, 1, '', REFUSED)
                return reply(REMOVED, 1)
            if command[:3] == ('rpm', '-q', '--whatprovides'):
                names = {'/usr/bin/pkg-config': 'pkgconf-pkg-config.x86_64', 'kmod': 'kmod.x86_64'}
                return reply(''.join(names[capability] + '\n' for capability in command[5:]))
            return reply('')
        return query

    def test_what_a_package_that_stays_still_needs_stays_too(self):
        asked = []
        with mock.patch.object(fedora, 'query', side_effect=self.answers(asked)):
            names, rows = fedora.removable(['pkgconf-pkg-config.x86_64', 'udisks2.x86_64'])
        self.assertEqual(names, ['udisks2.x86_64'])
        self.assertEqual(rows, ['udisks2.x86_64', 'libblockdev.x86_64'])
        self.assertIn(('rpm', '-q', '--whatprovides', '--qf', '%{NAME}.%{ARCH}\n', '/usr/bin/pkg-config', 'kmod'), asked)

    def test_the_removal_only_takes_what_can_go(self):
        with mock.patch.object(fedora, 'query', side_effect=self.answers([])), mock.patch.object(fedora, 'sudo') as sudo:
            fedora.remove(['pkgconf-pkg-config.x86_64', 'udisks2.x86_64'])
        sudo.assert_called_once_with('dnf', 'remove', '-y', 'udisks2.x86_64')

    def test_a_refusal_it_cannot_explain_stops(self):
        with mock.patch.object(fedora, 'query', return_value=subprocess.CompletedProcess((), 1, '', 'Problem: something else')):
            with self.assertRaises(RuntimeError):
                fedora.removable(['a.x86_64'])

    def test_nothing_to_remove(self):
        with mock.patch.object(fedora, 'query', return_value=reply('Nothing to do.\n')):
            self.assertEqual(fedora.removable(['a.x86_64']), (['a.x86_64'], []))
        self.assertEqual(fedora.removable([]), ([], []))

    def test_history_names(self):
        self.assertEqual(fedora.nevra_name('libva-intel-media-driver-0:26.3.5-1.fc45.x86_64'), 'libva-intel-media-driver.x86_64')
        transactions = [{'id': 1, 'command_line': '', 'packages': [{'nevra': 'a-0:1-1.fc45.x86_64', 'action': 'Install'}]},
                        {'id': 2, 'command_line': 'dnf --installroot=/mnt/sysroot install b', 'packages': [{'nevra': 'b-0:1-1.fc45.noarch', 'action': 'Install'}]},
                        {'id': 3, 'command_line': 'dnf install -y c', 'packages': [{'nevra': 'c-0:1-1.fc45.x86_64', 'action': 'Install'}]}]
        self.assertEqual(fedora.base_packages(transactions), {'a.x86_64', 'b.noarch'})
        self.assertEqual(fedora.base_packages(transactions[2:]), set())
        # PackageKit leaves no command line either: it comes after the system install, and is not part of it.
        later = transactions + [{'id': 4, 'command_line': '', 'packages': [{'nevra': 'd-0:1-1.fc45.x86_64', 'action': 'Install'}]}]
        self.assertEqual(fedora.base_packages(later), {'a.x86_64', 'b.noarch'})


class ClonePinTests(unittest.TestCase):
    TAGS = '\n'.join((f'{"1" * 40}\trefs/tags/25.03.19', f'{"2" * 40}\trefs/tags/26.9.30', f'{"3" * 40}\trefs/tags/26.10.1',
                      f'{"9" * 40}\trefs/tags/26.10.1^{{}}')) + '\n'
    ITEM = {'repo': 'https://github.com/marlonrichert/zsh-autocomplete', 'commit': '2' * 40, 'path': '.local/share/zsh/plugins/zsh-autocomplete',
            'track': 'tags'}

    def test_versions_sort_by_their_numbers(self):
        self.assertEqual(max(['25.03.19', '26.9.30', '26.10.1'], key=installer.version_key), '26.10.1')
        self.assertEqual(max(['v1.9.0', 'v1.20.0'], key=installer.version_key), 'v1.20.0')

    def test_an_annotated_tag_stands_for_its_commit(self):
        with mock.patch.object(installer, 'query', return_value=reply(self.TAGS)):
            self.assertEqual(installer.remote_tags('x'), {'25.03.19': '1' * 40, '26.9.30': '2' * 40, '26.10.1': '9' * 40})

    def test_a_clone_that_follows_tags_moves_to_the_latest_release(self):
        with mock.patch.object(installer, 'query', return_value=reply(self.TAGS)):
            pin = installer.newer_pin('clones', self.ITEM)
        self.assertEqual((pin.name, pin.new, pin.label, pin.tag), ('zsh-autocomplete', '9' * 40, '26.9.30 -> 26.10.1', '26.10.1'))
        self.assertEqual(pin.url, f'https://github.com/marlonrichert/zsh-autocomplete/compare/{"2" * 40}...{"9" * 40}')
        with mock.patch.object(installer, 'query', return_value=reply(self.TAGS)):
            self.assertIsNone(installer.newer_pin('clones', {**self.ITEM, 'commit': '9' * 40}))
        with mock.patch.object(installer, 'query', return_value=reply('', 128)):
            self.assertIs(installer.newer_pin('clones', self.ITEM), False)

    def test_any_other_clone_follows_its_branch(self):
        item = {**self.ITEM, 'track': None, 'repo': 'https://github.com/romkatv/powerlevel10k', 'path': '.p/powerlevel10k'}
        with mock.patch.object(installer, 'query', return_value=reply(f'{"7" * 40}\tHEAD\n')) as query:
            pin = installer.newer_pin('clones', item)
        query.assert_called_once_with('git', 'ls-remote', 'https://github.com/romkatv/powerlevel10k', 'HEAD', timeout=installer.REMOTE_TIMEOUT)
        self.assertEqual((pin.label, pin.tag), (f'{"2" * 12} -> {"7" * 12}', ''))

    def test_a_remote_that_does_not_answer_in_time_is_a_failure(self):
        with mock.patch.object(installer.subprocess, 'run', side_effect=installer.subprocess.TimeoutExpired('git', 60)):
            result = installer.query('git', 'ls-remote', 'x', 'HEAD', timeout=60)
        self.assertEqual(result.returncode, 124)

    def test_one_failing_entry_does_not_end_the_pins_listing(self):
        entries = [('aur', {'package': 'one'}), ('clones', {**self.ITEM, 'path': '.p/two'})]
        answers = [OSError('HTTP Error 502'), None]
        with mock.patch.object(installer, 'pin_entries', return_value=entries), \
                mock.patch.object(installer, 'newer_pin', side_effect=answers) as newer, \
                mock.patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(installer.pins(False), 1)
        self.assertEqual(newer.call_count, 2)
        self.assertIn('one: HTTP Error 502', out.getvalue())

    def test_repin_rewrites_the_commit_and_the_release_it_is_at(self):
        text = f"[[fedora.core.clones]]\ncommit = '{'2' * 40}'  # 26.9.30\npath = 'p'\n\n[[arch.core.clones]]\ncommit = '{'2' * 40}'  # 26.9.30\n"
        moved = installer.repin(text, '2' * 40, '9' * 40, tag='26.10.1')
        self.assertEqual(moved, text.replace('2' * 40, '9' * 40).replace('# 26.9.30', '# 26.10.1'))
        # A clone that follows its branch loses a comment that no longer names its commit.
        self.assertEqual(installer.repin(text, '2' * 40, '9' * 40).count('#'), 0)

    def test_the_same_clone_on_two_distributions_is_one_pin(self):
        tables = [{'core': {'clones': [self.ITEM]}}, {'core': {'clones': [dict(self.ITEM)]}, 'apps': {'aur': [{'package': 'p', 'commit': 'c' * 40}]}}]
        self.assertEqual([kind for kind, _ in installer.pin_entries(tables)], ['clones', 'aur'])

    def test_the_manifest_clones_say_what_they_follow(self):
        tracks = {clone['path'].rsplit('/', 1)[-1]: clone.get('track') for clone in MANIFEST['fedora']['core']['clones']}
        self.assertEqual(tracks, {'powerlevel10k': None, 'zsh-autocomplete': 'tags'})


def tarball(members):
    # A release archive in memory: {name: (content, mode)}, folders as their files' parents.
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode='w:gz') as archive:
        for name, (content, mode) in members.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(content), mode
            archive.addfile(info, io.BytesIO(content))
    return data.getvalue()


class ArchiveTests(unittest.TestCase):
    APP = tarball({'herdr-app/herdr-app': (b'#!/bin/sh\n', 0o755), 'herdr-app/herdr-app.svg': (b'<svg/>', 0o644)})
    CORE = tarball({'herdr-core': (b'#!/bin/sh\n', 0o755), 'LICENSE': (b'Apache', 0o644)})

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)
        self.items = [dict(item) for item in MANIFEST['fedora']['assistant']['archives']]
        self.items[0]['sha256'] = {'x86_64': hashlib.sha256(self.CORE).hexdigest(), 'aarch64': '0' * 64}
        self.items[1]['sha256'] = {'x86_64': hashlib.sha256(self.APP).hexdigest(), 'aarch64': '0' * 64}
        self.plan = installer.Plan(fake_distro(), '45', {'assistant': {'archives': self.items}}, [], ('assistant',), record={})
        self.fetched = []
        for patcher in (mock.patch.object(installer.Path, 'home', return_value=self.home),
                        mock.patch.object(installer.platform, 'machine', return_value='x86_64'),
                        mock.patch.object(installer.urllib.request, 'urlopen', side_effect=self.urlopen)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def urlopen(self, request, timeout=None):
        self.assertEqual(request.get_header('User-agent'), 'install-desktop.py (dotfiles)')
        self.fetched.append(request.full_url)
        return io.BytesIO(self.CORE if '/core/' in request.full_url else self.APP)

    def apply(self):
        items = installer.archives_pending(self.plan)
        installer.archives_remember(self.plan, items, self.plan.record)
        installer.archives_apply(self.plan, items)

    def test_the_manifest_archives_are_complete(self):
        for distro in ('fedora', 'arch'):
            for item in MANIFEST[distro]['assistant']['archives']:
                self.assertEqual(sorted(item['sha256']), ['aarch64', 'x86_64'])
                for digest in item['sha256'].values():
                    self.assertRegex(digest, '^[0-9a-f]{64}$')
                self.assertTrue(item['url'].startswith('https://releases.herdr.dev/') and '{version}' in item['url'] and '{arch}' in item['url'])
                for path in installer.archive_paths(item) + list(item.get('links', {}).values()):
                    self.assertFalse(path.startswith(('/', '~')) or '..' in path, path)
        self.assertEqual(MANIFEST['fedora']['assistant'], MANIFEST['arch']['assistant'])

    def test_unpacked_where_the_herdr_installers_put_it(self):
        self.assertEqual(installer.archives_pending(self.plan), ['herdr-core 0.1.18', 'herdr-app 0.1.13'])
        self.apply()
        self.assertEqual(self.fetched, ['https://releases.herdr.dev/core/0.1.18/herdr-core-linux-x86_64.tar.gz',
                                        'https://releases.herdr.dev/app/0.1.13/herdr-app-linux-x86_64.tar.gz'])
        self.assertTrue((self.home / '.local/bin/herdr-core').stat().st_mode & 0o100)
        self.assertEqual((self.home / '.local/bin/hc').readlink(), self.home / '.local/bin/herdr-core')
        self.assertEqual((self.home / '.local/bin/herdr-app').resolve(), self.home / '.local/share/herdr-app/herdr-app')
        self.assertTrue((self.home / '.local/share/icons/hicolor/scalable/apps/herdr-app.svg').is_file())
        entry = (self.home / '.local/share/applications/herdr-app.desktop').read_text()
        self.assertTrue(entry.startswith('[Desktop Entry]\n'))
        self.assertIn(f'Exec={self.home}/.local/bin/herdr-app\n', entry)
        self.assertFalse(list(self.home.rglob('*.new')))
        # Installed: what it updates by itself is never taken back.
        self.assertEqual(installer.archives_pending(self.plan), [])

    def test_what_is_there_stays(self):
        (self.home / '.local/bin').mkdir(parents=True)
        (self.home / '.local/bin/hc').write_text('another hc')
        (self.home / '.local/share/herdr-app').mkdir(parents=True)
        self.assertEqual(installer.archives_pending(self.plan), ['herdr-core 0.1.18'])
        self.apply()
        self.assertEqual((self.home / '.local/bin/hc').read_text(), 'another hc')
        self.assertEqual(self.plan.record['archives'], ['.local/bin/herdr-core'])

    def test_a_download_that_does_not_match_installs_nothing(self):
        self.items[0]['sha256']['x86_64'] = '1' * 64
        with self.assertRaises(SystemExit):
            installer.archives_apply(self.plan, ['herdr-core 0.1.18'])
        self.assertFalse((self.home / '.local/bin').exists())

    def test_no_build_for_this_machine_is_a_warning(self):
        with mock.patch.object(installer.platform, 'machine', return_value='riscv64'):
            self.assertEqual(installer.archives_pending(self.plan), [])
            self.assertEqual(installer.archives_unsupported(self.plan), ['herdr-core', 'herdr-app'])

    def test_uninstall_removes_what_apply_made(self):
        (self.home / '.local/share/applications').mkdir(parents=True)
        (self.home / '.local/share/applications/herdr-app.desktop').write_text('my own')
        self.apply()
        made = self.plan.record['archives']
        self.assertNotIn('.local/share/applications/herdr-app.desktop', made)
        self.assertEqual(installer.unarchives_pending(self.plan), made)
        installer.unarchives_apply(self.plan, made)
        self.assertEqual(sorted(str(path.relative_to(self.home)) for path in self.home.rglob('*') if path.is_file()),
                         ['.local/share/applications/herdr-app.desktop'])
        self.assertEqual(installer.unarchives_pending(self.plan), [])

    def latest(self, version, arch_url=None):
        targets = {f'linux-{arch}': {'url': arch_url or f'https://releases.herdr.dev/app/{version}/herdr-app-linux-{arch}.tar.gz',
                                     'sha256': arch[0] * 64} for arch in ('x86_64', 'aarch64')}
        return io.BytesIO(json.dumps({'version': version, 'targets': targets}).encode())

    def test_a_newer_release_is_a_pin_with_its_hashes(self):
        item = MANIFEST['fedora']['assistant']['archives'][1]
        with mock.patch.object(installer.urllib.request, 'urlopen', return_value=self.latest('0.2.0')):
            pin = installer.newer_pin('archives', item)
        self.assertEqual((pin.name, pin.old, pin.new, pin.label), ('herdr-app', '0.1.13', '0.2.0', '0.1.13 -> 0.2.0'))
        self.assertEqual(pin.hashes, {'x86_64': 'x' * 64, 'aarch64': 'a' * 64})
        self.assertEqual(pin.url, 'https://github.com/herdrdev/herdr-app/releases')
        with mock.patch.object(installer.urllib.request, 'urlopen', return_value=self.latest('0.1.13')):
            self.assertIsNone(installer.newer_pin('archives', item))
        # A download moved elsewhere, or no answer: not a pin to write.
        with mock.patch.object(installer.urllib.request, 'urlopen', return_value=self.latest('0.2.0', 'https://elsewhere/x.tar.gz')):
            self.assertIs(installer.newer_pin('archives', item), False)
        with mock.patch.object(installer.urllib.request, 'urlopen', side_effect=OSError('offline')):
            self.assertIs(installer.newer_pin('archives', item), False)

    def test_repin_moves_the_archive_on_both_distributions(self):
        text = (REPO / 'scripts/install/manifest.toml').read_text(encoding='utf-8')
        pin = installer.Pin('archives', 'herdr-app', '0.1.13', '0.2.0', '', '', '', '', {'x86_64': 'e' * 64, 'aarch64': 'f' * 64})
        moved = tomllib.loads(installer.apply_pin(text, pin))
        for distro in ('fedora', 'arch'):
            core, app = moved[distro]['assistant']['archives']
            self.assertEqual((app['version'], app['sha256']), ('0.2.0', {'x86_64': 'e' * 64, 'aarch64': 'f' * 64}))
            self.assertEqual(app['entries'], MANIFEST[distro]['assistant']['archives'][1]['entries'])
            self.assertEqual(core, MANIFEST[distro]['assistant']['archives'][0])
        self.assertEqual(len(installer.pin_entries([table for table in MANIFEST.values() if isinstance(table, dict)])),
                         len(installer.pin_entries([MANIFEST['fedora']]))
                         + len([item for section in installer.flatten_parts(MANIFEST['arch']).values() if isinstance(section, dict) for item in section.get('aur', ())]))


class AutostartTests(unittest.TestCase):
    def test_exec_arguments_follow_the_desktop_entry_rules(self):
        self.assertEqual(installer.exec_argument('/home/a/.dotfiles/scripts/x.py'), '/home/a/.dotfiles/scripts/x.py')
        # Quoting escapes " ` $ \\ with a backslash, the string escaping doubles every backslash, % is doubled.
        self.assertEqual(installer.exec_argument('/my "dots" $x 100%\\'), '"/my \\\\"dots\\\\" \\\\$x 100%%\\\\\\\\"')

    def test_the_entry_names_the_repository(self):
        current = installer.Plan(fake_distro(), '45', TABLE, [], ('core', 'plugins'))
        self.assertIn(f'Exec=kitty --hold {installer.REPO}/scripts/install-desktop.py post --profiles core,plugins\n',
                      installer.autostart_entry(current))


class CompositorGuardTests(unittest.TestCase):
    def warnings(self, candidates, profiles=('core', 'plugins'), repos_missing=False):
        distro = fake_distro()
        distro.repo_missing.return_value = repos_missing
        distro.candidates.return_value = candidates
        with mock.patch('builtins.print') as shown:
            installer.compositor_guard(plan(distro, profiles=profiles), ['hyprland', 'hyprland-devel', 'kitty'])
        return [call.args[0] for call in shown.call_args_list]

    def test_an_unverified_build_is_named_before_the_install(self):
        verified = installer.bundle.VERIFIED[0]
        self.assertEqual(self.warnings({'hyprland': verified, 'hyprland-devel': verified}), [])
        shown = self.warnings({'hyprland': '9.9.9-1.fc45.x86_64', 'hyprland-devel': verified})
        self.assertEqual(len(shown), 1)
        self.assertIn('hyprland 9.9.9-1.fc45.x86_64', shown[0])

    def test_no_warning_without_plugins_or_before_the_repository(self):
        self.assertEqual(self.warnings({'hyprland': '9.9.9-1.fc45.x86_64'}, profiles=('core',)), [])
        self.assertEqual(self.warnings({'hyprland': '9.9.9-1.fc45.x86_64'}, repos_missing=True), [])


class FedoraTests(unittest.TestCase):
    def test_answers_are_kept_until_a_change(self):
        self.addCleanup(setattr, fedora, 'answers', None)
        fedora.remember_answers()
        with mock.patch.object(fedora, 'run_query', return_value=reply('x')) as run, mock.patch('subprocess.run'):
            fedora.query('dnf', 'repoquery', 'a')
            fedora.query('dnf', 'repoquery', 'a')
            fedora.query('systemctl', 'is-enabled', 'x')
            fedora.query('systemctl', 'is-enabled', 'x')
            self.assertEqual(run.call_count, 3)  # dnf once, systemctl each time
            fedora.sudo('dnf', 'remove', '-y', 'a')
            fedora.query('dnf', 'repoquery', 'a')
            self.assertEqual(run.call_count, 4)

    def test_only_packages_dnf_pulled_in_count_as_not_by_hand(self):
        rows = ('a.x86_64 User\nb.x86_64 Group\nc.x86_64 External User\nd.x86_64 None\n'
                'e.x86_64 Dependency\nf.x86_64 Weak Dependency\ng.x86_64 Clean\n')
        with mock.patch.object(fedora, 'query', return_value=reply(rows)):
            self.assertEqual(fedora.installed_by_hand(['a']), {'a.x86_64', 'b.x86_64', 'c.x86_64', 'd.x86_64'})
        self.assertEqual(fedora.installed_by_hand([]), set())

    def test_missing_reads_the_lines_rpm_prints(self):
        lines = 'hyprland-0.57.0-1.fc45.x86_64\nno package provides mesa-vulkan-drivers(x86-32)\nno package provides gdm\n'
        with mock.patch.object(fedora, 'query', return_value=reply(lines)):
            self.assertEqual(fedora.missing(['hyprland', 'mesa-vulkan-drivers(x86-32)', 'gdm']), ['mesa-vulkan-drivers(x86-32)', 'gdm'])

    def test_missing_also_takes_capabilities(self):
        with mock.patch.object(fedora, 'query', return_value=reply()) as query:
            fedora.missing(['mesa-vulkan-drivers(x86-32)'])
        query.assert_called_once_with('rpm', '-q', '--whatprovides', 'mesa-vulkan-drivers(x86-32)')

    def test_rpm_speaks_english_whatever_the_locale(self):
        with mock.patch.dict('os.environ', {'LANG': 'it_IT.UTF-8'}), mock.patch('subprocess.run', return_value=reply()) as run:
            fedora.query('rpm', '-q', 'x')
        self.assertEqual(run.call_args.kwargs['env']['LC_ALL'], 'C')

    def test_copr_repos_use_the_file_dnf_writes(self):
        self.assertEqual(fedora.repo_file({'kind': 'copr', 'name': 'lionheartp/Hyprland'}).name,
                         '_copr:copr.fedorainfracloud.org:lionheartp:Hyprland.repo')

    def test_a_copr_repo_is_enabled_and_removed_through_its_file(self):
        with mock.patch.object(fedora, 'install') as install, mock.patch.object(fedora, 'sudo') as sudo:
            fedora.add_repo({'kind': 'copr', 'name': 'a/b'}, '45')
            fedora.remove_repo({'kind': 'copr', 'name': 'a/b'})
        install.assert_not_called()
        self.assertEqual(sudo.call_args_list, [mock.call('dnf', 'copr', 'enable', '-y', 'a/b'),
                                               mock.call('rm', '-f', '/etc/yum.repos.d/_copr:copr.fedorainfracloud.org:a:b.repo')])

    def test_what_a_repository_needs_is_a_step_of_its_own_and_recorded(self):
        # dnf5-plugins for a copr, only while a repository that needs it is still to add, and before it.
        titles = [step.title for step in installer.STEPS]
        self.assertEqual(titles.index('repo tools') + 1, titles.index('repos'))
        self.assertEqual(installer.repo_tools_pending(plan(fake_distro())), ['dnf5-plugins'])
        self.assertEqual(installer.repo_tools_pending(plan(fake_distro(pending=False))), [])
        record = {}
        installer.repo_tools_remember(plan(fake_distro()), ['dnf5-plugins'], record)
        self.assertEqual(record, {'packages': ['dnf5-plugins']})
        for name, repo in MANIFEST['fedora']['repos'].items():
            if repo['kind'] == 'copr':
                self.assertIn('dnf5-plugins', repo.get('needs', ()), name)

    def test_release_packages_name_the_release(self):
        repo = {'kind': 'release', 'url': 'https://example.com/free-{release}.rpm'}
        with mock.patch.object(fedora, 'install') as install:
            fedora.add_repo(repo, '45')
        install.assert_called_once_with(['https://example.com/free-45.rpm'])

    def test_repo_files_lose_the_leading_newline_of_the_manifest(self):
        with mock.patch.object(fedora, 'write_file') as write:
            fedora.add_repo({'kind': 'file', 'file': 'x.repo', 'content': '\n[x]\n'}, '45')
        write.assert_called_once_with(fedora.REPOS / 'x.repo', '[x]\n')

    def test_excluded_packages_stay_out_of_the_install(self):
        with mock.patch.object(fedora, 'sudo') as sudo:
            fedora.install(['a'], ['tour', 'rygel'])
        sudo.assert_called_once_with('dnf', 'install', '-y', '--exclude=tour,rygel', 'a')

    def test_no_exclude_means_a_plain_install(self):
        with mock.patch.object(fedora, 'sudo') as sudo:
            fedora.install(['a'])
        sudo.assert_called_once_with('dnf', 'install', '-y', 'a')

    def test_an_excluded_package_is_never_also_wanted(self):
        fedora_table = MANIFEST['fedora']
        wanted = {package for name in installer.PROFILES for package in fedora_table[name].get('packages', ())}
        excluded = {package for name in installer.PROFILES for package in fedora_table[name].get('exclude', ())}
        self.assertFalse(wanted & excluded)

    def test_a_replaced_package_is_looked_up_by_name(self):
        # intel-media-driver provides libva-intel-media-driver: --whatprovides would call the swap still to do.
        with mock.patch.object(fedora, 'query', return_value=mock.Mock(returncode=1)) as query:
            self.assertFalse(fedora.installed('libva-intel-media-driver'))
        query.assert_called_once_with('rpm', '-q', 'libva-intel-media-driver')

    def test_a_swap_may_remove_what_conflicts(self):
        with mock.patch.object(fedora, 'sudo') as sudo:
            fedora.swap('ffmpeg-free', 'ffmpeg')
        sudo.assert_called_once_with('dnf', 'swap', '-y', '--allowerasing', 'ffmpeg-free', 'ffmpeg')

    def test_a_failed_check_is_not_a_clean_system(self):
        with mock.patch.object(fedora, 'query', return_value=mock.Mock(returncode=1, stderr='no network')):
            with self.assertRaises(RuntimeError):
                fedora.upgrades_pending()

    def test_upgrades_follow_the_exit_code_of_dnf(self):
        for code, expected in ((0, False), (100, True)):
            with mock.patch.object(fedora, 'query', return_value=mock.Mock(returncode=code)):
                self.assertIs(fedora.upgrades_pending(), expected)

    def test_a_file_that_cannot_be_read_differs(self):
        self.assertTrue(fedora.file_differs('/nonexistent/file', 'x'))

    def test_files_are_installed_as_root(self):
        with mock.patch.object(fedora, 'sudo') as sudo:
            fedora.write_file('/etc/x', 'y')
        command = sudo.call_args.args
        self.assertEqual(command[:7], ('install', '-D', '-o', 'root', '-g', 'root', '-m'))
        self.assertEqual(command[-1], '/etc/x')

    def test_auth_reports_what_is_left(self):
        for output, expected in (('local', [fedora.AUTH_FEATURE, fedora.AUTH_PROFILE]),
                                 ('local with-fingerprint', [fedora.AUTH_PROFILE]),
                                 ('custom/desktop-tablet with-fingerprint with-mdns4', []), ('', [fedora.AUTH_FEATURE, fedora.AUTH_PROFILE])):
            with mock.patch.object(fedora, 'query', return_value=reply(output)):
                self.assertEqual(fedora.auth_pending(), expected)

    def test_auth_reports_only_what_is_wanted(self):
        # hardware.fingerprint alone: the feature, not the tablet profile.
        for output, expected in (('local', [fedora.AUTH_FEATURE]), ('local with-fingerprint', [])):
            with mock.patch.object(fedora, 'query', return_value=reply(output)):
                self.assertEqual(fedora.auth_pending([fedora.AUTH_FEATURE]), expected)

    def test_firmware_keeps_the_selinux_label_and_reaches_every_initramfs(self):
        with mock.patch.object(fedora, 'sudo') as sudo:
            fedora.install_firmware(Path('/media/blob.bin'), '/usr/lib/firmware/x.bin')
            fedora.rebuild_initramfs()
        commands = [call.args for call in sudo.call_args_list]
        self.assertEqual(commands[0][:7], ('install', '-D', '-o', 'root', '-g', 'root', '-m'))
        self.assertEqual(commands[1], ('restorecon', '/usr/lib/firmware/x.bin'))
        self.assertEqual(commands[2], ('dracut', '--force', '--regenerate-all'))

    def test_the_feature_comes_before_the_tablet_profile(self):
        # tablet-auth.sh copies the current features.
        order = mock.Mock()
        with mock.patch.object(fedora, 'sudo', order.sudo), mock.patch('subprocess.run', order.run):
            fedora.auth_apply([fedora.AUTH_FEATURE, fedora.AUTH_PROFILE], Path('/repo/tablet-auth.sh'))
        self.assertEqual([call[0] for call in order.mock_calls], ['sudo', 'run'])
        self.assertEqual(order.run.call_args.args[0], ('/repo/tablet-auth.sh', 'install'))


class TouchHardwareTests(unittest.TestCase):
    """A 2-in-1 is told by /proc/bus/input/devices: a tablet mode switch or a touchscreen."""

    def found(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'devices'
            path.write_text(text)
            return installer.touch_hardware(path)

    def test_a_tablet_mode_switch(self):
        self.assertTrue(self.found('N: Name="Intel HID switches"\nB: PROP=0\nB: EV=21\nB: SW=22\n'))

    def test_a_touchscreen(self):
        self.assertTrue(self.found('N: Name="ELAN2513:00 04F3:4302"\nB: PROP=2\nB: EV=1b\nB: ABS=3273800000000003\n'))

    def test_a_laptop_lid_and_touchpad_are_not(self):
        lid = 'N: Name="Lid Switch"\nB: PROP=0\nB: EV=21\nB: SW=1\n'
        touchpad = 'N: Name="SYNA Touchpad"\nB: PROP=5\nB: EV=1b\nB: ABS=2e0800000000003\n'
        self.assertFalse(self.found(lid + '\n' + touchpad))

    def test_no_file(self):
        self.assertFalse(installer.touch_hardware(Path('/nonexistent/devices')))


class PartTests(unittest.TestCase):
    """Profiles in parts: each [<distro>.<profile>.parts.<part>] is the unit profile.part."""

    def test_both_distributions_have_the_same_units(self):
        fedora = installer.units(installer.flatten_parts(copy.deepcopy(MANIFEST['fedora'])))
        arch = installer.units(installer.flatten_parts(copy.deepcopy(MANIFEST['arch'])))
        self.assertEqual(fedora, arch)
        self.assertEqual(installer.manifest_units(), fedora)
        self.assertEqual([name for name in fedora if '.' not in name], list(installer.PROFILES))

    def test_every_part_says_whether_it_starts_checked(self):
        for distro in ('fedora', 'arch'):
            table = installer.flatten_parts(copy.deepcopy(MANIFEST[distro]))
            for name in installer.units(table):
                if '.' in name:
                    self.assertIn(table[name].get('default'), (True, False, *installer.DETECT), f'{distro} {name}')
                else:
                    self.assertNotIn('default', table[name], name)

    def test_a_part_brings_its_profile_and_a_profile_takes_its_parts(self):
        self.assertEqual(installer.normalized(('apps.zen', 'core')), ('core', 'apps', 'apps.zen'))
        self.assertEqual(installer.with_parts(('gaming',)), ('gaming', 'gaming.steam', 'gaming.steam-hidpi', 'gaming.gamescope'))
        self.assertEqual(installer.with_parts(('gaming.steam',)), ('gaming.steam',))

    def test_default_parts_by_detection(self):
        table = installer.flatten_parts(copy.deepcopy(MANIFEST['fedora']))
        for found in (True, False):
            with mock.patch.dict(installer.DETECT, {name: (lambda found=found: found) for name in installer.DETECT}):
                parts = installer.default_parts('hardware', table)
            expected = ['hardware.intel', 'hardware.audio', 'hardware.camera', 'hardware.fingerprint', 'hardware.firmware'] if found else ['hardware.firmware']
            self.assertEqual(list(parts), expected)
        self.assertEqual(installer.default_parts('apps', table), ('apps.zen', 'apps.loupe', 'apps.papers', 'apps.showtime'))
        self.assertEqual(installer.default_parts('utils', table), ('utils.neovim', 'utils.gcc', 'utils.xclip', 'utils.unrar', 'utils.fuse'))

    def test_defaults_bring_the_parts_of_the_default_profiles(self):
        table = installer.flatten_parts(copy.deepcopy(MANIFEST['fedora']))
        with mock.patch.object(installer, 'touch_hardware', return_value=False), \
                mock.patch.dict(installer.DETECT, {name: (lambda: False) for name in installer.DETECT}):
            self.assertEqual(installer.default_profiles(table), 'core,hardware,hardware.firmware,plugins,plugins.hyprspace,plugins.hyprglass,plugins.hyprcapture')

    def test_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cpuinfo = root / 'cpuinfo'
            cpuinfo.write_text('vendor_id\t: AuthenticAMD\n')
            self.assertFalse(installer.detect_intel(cpuinfo))
            cpuinfo.write_text('vendor_id\t: GenuineIntel\n')
            self.assertTrue(installer.detect_intel(cpuinfo))
            self.assertFalse(installer.detect_camera(root))
            self.assertFalse(installer.detect_fingerprint(root))

            def device(kind, name, **files):
                path = root / kind / name
                path.mkdir(parents=True)
                for key, value in files.items():
                    (path / key).write_text(value + '\n')
            device('bus/usb/devices', '1-1', idVendor='04f3', idProduct='2513')
            self.assertFalse(installer.detect_fingerprint(root))
            device('bus/usb/devices', '1-2', idVendor='04f3', idProduct='0c4b')
            self.assertTrue(installer.detect_fingerprint(root))
            device('bus/pci/devices', '0000:00:05.0', vendor='0x8086', **{'class': '0x048000'})
            self.assertTrue(installer.detect_camera(root))

    def test_load_plan_makes_each_part_a_table(self):
        current = installer.load_plan(('core', 'apps', 'apps.zen'), {'ID': 'fedora', 'VERSION_ID': '45'})
        self.assertIn('apps.zen', current.table)
        self.assertNotIn('parts', current.table['apps'])
        self.assertIn('zen-browser', installer.wanted_packages(current))
        self.assertNotIn('code', installer.wanted_packages(current))


class UnitsFileTests(unittest.TestCase):
    """The installed units for Hyprland and the shell, written with the record."""

    def test_written_with_the_record_and_gone_with_the_desktop(self):
        installer.save_record({'profiles': ['core', 'plugins', 'plugins.hyprspace']})
        self.assertEqual(installer.UNITS.read_text(), 'core\nplugins\nplugins.hyprspace\n')
        installer.save_record({'profiles': ['core'], 'uninstalled': True})
        self.assertFalse(installer.UNITS.exists())
        # A record without profiles yet: no file, so everything counts.
        installer.save_record({'packages': ['a']})
        self.assertFalse(installer.UNITS.exists())


if __name__ == '__main__':
    unittest.main()
