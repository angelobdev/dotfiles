#!/usr/bin/env python3
"""install-desktop.py must preview without changing anything, repeat safely, and refuse what it does not know."""
import importlib.util
from pathlib import Path
import subprocess
import sys
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

MANIFEST = tomllib.loads((REPO / 'scripts/install/manifest.toml').read_text(encoding='utf-8'))
PROFILE_KEYS = {'repos', 'packages', 'services', 'user_services', 'disable', 'files', 'groups', 'flatpaks', 'firewall_zone', 'auth', 'notes'}
TABLE = {
    'repos': {'one': {'kind': 'copr', 'name': 'a/b'}},
    'core': {'repos': ['one'], 'packages': ['a', 'b'], 'services': ['s.service'], 'user_services': ['u.service'],
             'disable': ['d.socket'], 'files': [{'path': '/etc/x', 'content': '\nx\n'}], 'groups': ['g'], 'notes': ['first']},
    'plugins': {'packages': ['b', 'c'], 'flatpaks': ['org.example.App'], 'firewall_zone': 'Zone', 'auth': True,
                'notes': ['second']},
}


def reply(stdout='', returncode=0):
    return subprocess.CompletedProcess((), returncode, stdout, '')


def fake_distro(pending=True):
    distro = mock.Mock(ADMIN_GROUP='wheel', AUTH_PROFILE='custom/desktop-tablet')
    distro.repo_missing.return_value = pending
    distro.upgrades_pending.return_value = pending
    distro.missing.return_value = ['a'] if pending else []
    distro.file_differs.return_value = pending
    distro.auth_pending.return_value = ['with-fingerprint'] if pending else []
    distro.auth_base.return_value = 'local'
    return distro


def plan(distro, commands=(), profiles=('core', 'plugins')):
    return installer.Plan(distro, '45', TABLE, list(commands), profiles)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.fedora = MANIFEST['fedora']
        self.profiles = [self.fedora[name] for name in installer.PROFILES]

    def test_every_profile_exists_and_uses_known_keys(self):
        for profile in self.profiles:
            self.assertLessEqual(set(profile), PROFILE_KEYS)

    def test_repos_are_defined_and_all_used(self):
        used = {name for profile in self.profiles for name in profile.get('repos', ())}
        self.assertEqual(used, set(self.fedora['repos']))

    def test_no_package_is_named_twice(self):
        for profile in self.profiles:
            self.assertEqual(len(profile['packages']), len(set(profile['packages'])))

    def test_the_login_depends_on_these_being_named(self):
        for package in ('gdm', 'hyprland-uwsm', 'dbus-tools', 'accountsservice', 'qt6-qtsvg', 'quickshell', 'stow'):
            self.assertIn(package, self.fedora['core']['packages'])

    def test_names_that_are_wrong_on_fedora_stay_out(self):
        packages = {package for profile in self.profiles for package in profile['packages']}
        self.assertFalse(packages & {'power-profiles-daemon', 'f44-backgrounds-base', 'nlohmann-json-devel', 'sof-firmware'})

    def test_passwords_have_a_service_on_every_edition(self):
        # Nothing starts it on Server: no preset, and no D-Bus activation.
        self.assertIn('oo7-daemon', self.fedora['core']['packages'])
        self.assertIn('oo7-daemon.service', self.fedora['core']['user_services'])

    def test_personal_apps_are_opt_in(self):
        self.assertNotIn('apps', installer.DEFAULT_PROFILES.split(','))


class RefusalTests(unittest.TestCase):
    def assert_refused(self, release, words):
        with self.assertRaises(SystemExit) as caught:
            installer.load_plan(('core',), release)
        self.assertIn(words, str(caught.exception))

    def test_an_unknown_distribution(self):
        self.assert_refused({'ID': 'debian', 'VERSION_ID': '13'}, 'not verified')

    def test_the_verify_table_is_not_a_distribution(self):
        self.assert_refused({'ID': 'verify', 'VERSION_ID': '1'}, 'not verified')

    def test_this_fedora_44_laptop(self):
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

    def test_another_home(self):
        self.assertIn('/home/angelo', self.warnings(40 * 2**30, home='/home/someone'))

    def test_an_unexpected_auth_profile(self):
        self.assertIn('sssd', self.warnings(40 * 2**30, base='sssd'))


class StepTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        base = Path(folder.name)
        self.autostart = base / 'autostart/finish.desktop'
        self.stamp = base / 'stamp.json'
        for target, value in (('AUTOSTART', self.autostart), ('STAMP', self.stamp)):
            patcher = mock.patch.object(installer, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.calls = []
        for name, value in (('getpass.getuser', 'angelo'), ('shutil.which', '/usr/bin/tool'), ('builtins.print', None)):
            patcher = mock.patch(name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(installer, 'plugin_guard')
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
            return reply('LINK: a => b\n' if pending else 'WARNING: in simulation mode\n')
        group = mock.Mock(gr_mem=[] if pending else ['angelo'])
        patches = [mock.patch.object(installer, 'query', side_effect=query), mock.patch('grp.getgrnam', return_value=group),
                   mock.patch.object(installer, 'booted', return_value=booted)]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_profiles_merge_in_order_without_repeats(self):
        self.assertEqual(installer.merged(plan(fake_distro()), 'packages'), ['a', 'b', 'c'])

    def test_a_tool_that_is_not_installed_yet_is_an_empty_answer(self):
        result = installer.query('this-command-does-not-exist-here')
        self.assertEqual((result.returncode, result.stdout), (127, ''))

    def test_a_preview_changes_nothing(self):
        self.system(True)
        distro = fake_distro()
        with mock.patch('subprocess.run') as run:
            done = installer.run_steps(plan(distro), True)
        self.assertEqual(done, len(installer.STEPS) - 1)  # All but verify: its commands are found here.
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
        with mock.patch('subprocess.run') as run:
            self.assertEqual(installer.run_steps(plan(distro), False), 0)
        run.assert_not_called()
        distro.sudo.assert_not_called()

    def test_stow_never_runs_under_sudo(self):
        distro = fake_distro()
        with mock.patch('subprocess.run') as run:
            installer.stow_apply(plan(distro), ['LINK: a'])
        self.assertEqual(run.call_args.args[0], (str(REPO / 'scripts/stow.py'), 'apply'))
        distro.sudo.assert_not_called()

    def test_stow_is_pending_until_it_exists(self):
        with mock.patch('shutil.which', return_value=None):
            self.assertIn('not installed', installer.stow_pending(plan(fake_distro()))[0])

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
        distro.write_file.assert_called_once_with('/etc/x', 'x\n')

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
        distro.missing.return_value = []
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


class FedoraTests(unittest.TestCase):
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

    def test_a_copr_repo_brings_the_command_it_needs(self):
        with mock.patch.object(fedora, 'missing', return_value=['dnf5-plugins']), mock.patch.object(fedora, 'install') as install, \
                mock.patch.object(fedora, 'sudo') as sudo:
            fedora.add_repo({'kind': 'copr', 'name': 'a/b'}, '45')
        install.assert_called_once_with(['dnf5-plugins'])
        sudo.assert_called_once_with('dnf', 'copr', 'enable', '-y', 'a/b')

    def test_release_packages_name_the_release(self):
        repo = {'kind': 'release', 'url': 'https://example.com/free-{release}.rpm'}
        with mock.patch.object(fedora, 'install') as install:
            fedora.add_repo(repo, '45')
        install.assert_called_once_with(['https://example.com/free-45.rpm'])

    def test_repo_files_lose_the_leading_newline_of_the_manifest(self):
        with mock.patch.object(fedora, 'write_file') as write:
            fedora.add_repo({'kind': 'file', 'file': 'x.repo', 'content': '\n[x]\n'}, '45')
        write.assert_called_once_with(fedora.REPOS / 'x.repo', '[x]\n')

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

    def test_the_feature_comes_before_the_tablet_profile(self):
        # tablet-auth.sh copies the current features.
        order = mock.Mock()
        with mock.patch.object(fedora, 'sudo', order.sudo), mock.patch('subprocess.run', order.run):
            fedora.auth_apply([fedora.AUTH_FEATURE, fedora.AUTH_PROFILE], Path('/repo/tablet-auth.sh'))
        self.assertEqual([call[0] for call in order.mock_calls], ['sudo', 'run'])
        self.assertEqual(order.run.call_args.args[0], ('/repo/tablet-auth.sh', 'install'))


if __name__ == '__main__':
    unittest.main()
