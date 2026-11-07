#!/usr/bin/env python3
"""Arch Linux in install-desktop.py: the manifest table, the pacman module, the AUR step and its pins."""
import atexit
import importlib.util
import io
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
import arch  # noqa: E402
sys.path.insert(0, str(REPO / 'scripts/hyprpm'))
import build  # noqa: E402
import bundle  # noqa: E402

# Never the real state: apply writes its record there.
SANDBOX = tempfile.TemporaryDirectory()
atexit.register(SANDBOX.cleanup)
installer.STATE = Path(SANDBOX.name)
installer.RECORD = installer.STATE / 'install.json'

MANIFEST = tomllib.loads((REPO / 'scripts/install/manifest.toml').read_text(encoding='utf-8'))
PROFILE_KEYS = {'repos', 'packages', 'services', 'user_services', 'disable', 'files', 'groups', 'stow', 'flatpaks',
                'login_shell', 'clones', 'firmware', 'aur', 'notes', 'archives'}
# The default pacman.conf of Arch, around its repositories.
PACMAN_CONF = '''[options]
HoldPkg     = pacman glibc

#[core-testing]
#Include = /etc/pacman.d/mirrorlist

[core]
Include = /etc/pacman.d/mirrorlist

#[multilib-testing]
#Include = /etc/pacman.d/mirrorlist

#[multilib]
#Include = /etc/pacman.d/mirrorlist

# An example of a custom package repository.
#[custom]
#SigLevel = Optional TrustAll
#Server = file:///home/custompkgs
'''
QI = '''Name            : gdm
Version         : 51.1.1-1
Architecture    : x86_64
Provides        : None
Depends On      : gnome-shell  libgdm=51.1.1
Install Reason  : Explicitly installed

Name            : gnome-shell
Version         : 51.1-1
Architecture    : x86_64
Provides        : None
Depends On      : glib2  libgtk-3.so=0-64
Install Reason  : Installed as a dependency for another package

Name            : libgdm
Version         : 51.1.1-1
Architecture    : x86_64
Provides        : None
Depends On      : glib2
Install Reason  : Installed as a dependency for another package

Name            : gtk3
Version         : 1:3.24.51-1
Architecture    : x86_64
Provides        : gtk3-print-backends  libgtk-3.so=0-64
Depends On      : glib2
Install Reason  : Installed as a dependency for another package

Name            : glib2
Version         : 2.88.0-1
Architecture    : x86_64
Provides        : None
Depends On      : None
Install Reason  : Installed as a dependency for another package

Name            : webkitgtk-6.0
Version         : 2.52.0-1
Architecture    : x86_64
Provides        : None
Depends On      : gtk3
                  glib2
Install Reason  : Explicitly installed
'''


def reply(stdout='', returncode=0, stderr=''):
    return subprocess.CompletedProcess((), returncode, stdout, stderr)


class Answers:
    """A fake query: replies by the start of the command, and the commands asked."""

    def __init__(self, replies):
        self.replies, self.asked = replies, []

    def __call__(self, *command):
        self.asked.append(command)
        for start, answer in self.replies.items():
            if command[:len(start)] == start:
                return answer
        return reply('', 1)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.arch = MANIFEST['arch']
        self.profiles = {name: self.arch[name] for name in installer.PROFILES}
        self.packages = {package for profile in self.profiles.values() for package in profile.get('packages', ())}

    def test_every_profile_exists_and_uses_known_keys(self):
        for profile in self.profiles.values():
            self.assertLessEqual(set(profile), PROFILE_KEYS)

    def test_arch_is_a_rolling_release(self):
        self.assertEqual(self.arch['versions'], ['rolling'])

    def test_repos_are_defined_and_all_used(self):
        used = {name for profile in self.profiles.values() for name in profile.get('repos', ())}
        self.assertEqual(used, set(self.arch['repos']))
        for repo in self.arch['repos'].values():
            self.assertEqual(repo['kind'], 'pacman')

    def test_no_package_is_named_twice(self):
        for profile in self.profiles.values():
            self.assertEqual(len(profile.get('packages', ())), len(set(profile.get('packages', ()))))

    def test_the_login_depends_on_these_being_named(self):
        for package in ('gdm', 'accountsservice', 'hyprland', 'hyprpm', 'uwsm', 'quickshell', 'qt6-svg', 'stow', 'oo7'):
            self.assertIn(package, self.arch['core']['packages'])

    def test_fedora_names_stay_out(self):
        fedora = {'hyprland-devel', 'hyprland-uwsm', 'dbus-tools', 'python3', 'git-core', 'fd-find', 'ImageMagick',
                  'NetworkManager', 'xorg-x11-server-Xwayland', 'ffmpeg-free', 'cldr-emoji-annotation'}
        self.assertFalse(self.packages & fedora)

    def test_no_second_sound_server_or_power_daemon(self):
        # pacman would pick jack2 for ffmpeg; tuned-ppd conflicts with power-profiles-daemon.
        self.assertIn('pipewire-jack', self.arch['core']['packages'])
        self.assertFalse(self.packages & {'jack2', 'power-profiles-daemon', 'pulseaudio'})

    def test_the_same_shell_as_on_fedora(self):
        self.assertEqual(self.arch['core']['login_shell'], '/usr/bin/zsh')
        self.assertEqual(self.arch['core']['clones'], MANIFEST['fedora']['core']['clones'])
        for package in ('zsh', 'zsh-autosuggestions', 'zsh-syntax-highlighting', 'git', 'fzf'):
            self.assertIn(package, self.arch['core']['packages'])

    def test_the_update_check_has_what_it_needs(self):
        # checkupdates, for the installer and the update icon, needs fakeroot.
        self.assertLessEqual({'pacman-contrib', 'fakeroot'}, set(self.arch['core']['packages']))

    def test_the_installer_prerequisites_are_protected(self):
        self.assertEqual(arch.PROTECTED, ('python', 'git'))

    def test_keys_pacman_has_no_use_for_stay_out(self):
        # No weak dependencies, no swaps, no firewall by default, and tablet sign-in is not ported.
        for profile in self.profiles.values():
            self.assertFalse(set(profile) & {'exclude', 'swaps', 'firewall_zone', 'auth'})

    def test_aur_packages_are_pinned(self):
        entries = [item for profile in self.profiles.values() for item in profile.get('aur', ())]
        self.assertEqual({item['package'] for item in entries}, {'zen-browser-bin', '1password', 'visual-studio-code-bin'})
        for item in entries:
            self.assertRegex(item['package'], r'^[a-z0-9@._+-]+$')
            self.assertRegex(item['commit'], '^[0-9a-f]{40}$')
            self.assertRegex(item['version'], r'^(\d+:)?[A-Za-z0-9._+]+-\d+(\.\d+)?$')
            self.assertTrue(item.get('key', 'https://').startswith('https://'))

    def test_makepkg_has_what_it_needs_where_the_aur_is_used(self):
        for profile in self.profiles.values():
            if profile.get('aur'):
                self.assertIn('base-devel', profile['packages'])

    def test_personal_apps_are_opt_in(self):
        for profile in ('apps', 'herdr', 'containers', 'media', 'gaming', 'steam-hidpi', 'codecs'):
            self.assertNotIn(profile, installer.DEFAULT_PROFILES.split(','))

    def test_the_firmware_is_fedora_s(self):
        self.assertEqual(self.arch['tablet']['firmware'], MANIFEST['fedora']['tablet']['firmware'])


class ReleaseTests(unittest.TestCase):
    def test_arch_loads_its_module(self):
        loaded = installer.load_plan(('core',), {'ID': 'arch', 'BUILD_ID': 'rolling'})
        self.assertIs(loaded.distro, arch)
        self.assertEqual(loaded.release, 'rolling')

    def test_the_container_image_is_still_rolling(self):
        # The archlinux image adds a VERSION_ID: the date it was built.
        loaded = installer.load_plan(('core',), {'ID': 'arch', 'BUILD_ID': 'rolling', 'VERSION_ID': '20261101.0.620205'})
        self.assertEqual(loaded.release, 'rolling')

    def test_a_derivative_is_not_arch(self):
        with mock.patch('builtins.print'), self.assertRaises(SystemExit) as caught:
            installer.load_plan(('core',), {'ID': 'endeavouros', 'ID_LIKE': 'arch', 'BUILD_ID': 'rolling'})
        self.assertIn('not verified', str(caught.exception))


class PacmanTests(unittest.TestCase):
    def answers(self, replies):
        fake = Answers(replies)
        patcher = mock.patch.object(arch, 'query', side_effect=fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        return fake

    def test_missing_is_what_pacman_t_prints(self):
        fake = self.answers({('pacman', '-T'): reply('pulseaudio\nnosuch\n', 127)})
        self.assertEqual(arch.missing(['gdm', 'pulseaudio', 'nosuch']), ['pulseaudio', 'nosuch'])
        self.assertEqual(fake.asked, [('pacman', '-T', '--', 'gdm', 'pulseaudio', 'nosuch')])
        self.assertEqual(arch.missing([]), [])

    def test_installed_is_by_name_not_by_what_a_package_provides(self):
        self.answers({('pacman', '-Q', '--', 'sh'): reply('bash 5.3.20-1\n'), ('pacman', '-Q', '--', 'bash'): reply('bash 5.3.20-1\n')})
        self.assertFalse(arch.installed('sh'))
        self.assertTrue(arch.installed('bash'))
        self.assertEqual(arch.version('bash'), '5.3.20-1')
        self.assertEqual(arch.version('nosuch'), '')

    def test_candidates_take_the_first_repository(self):
        self.answers({('pacman', '-Si'): reply('Repository : core-testing\nName : hyprland\nVersion : 0.58.0-1\n\n'
                                               'Repository : extra\nName : hyprland\nVersion : 0.57.1-1\n')})
        self.assertEqual(arch.candidates(['hyprland']), {'hyprland': '0.58.0-1'})

    def test_the_install_is_a_full_upgrade(self):
        with mock.patch.object(arch, 'sudo') as sudo:
            arch.install(['a', 'b'], ['ignored'])
        sudo.assert_called_once_with('pacman', '-Syu', '--needed', '--noconfirm', '--', 'a', 'b')

    def test_a_swap_lets_pacman_remove_what_conflicts(self):
        with mock.patch.object(arch, 'sudo') as sudo:
            arch.swap('pulseaudio', 'pipewire-pulse')
        sudo.assert_called_once_with('pacman', '-Syu', '--needed', '--noconfirm', '--ask=4', '--', 'pipewire-pulse')

    def test_upgrades_follow_the_exit_code_of_checkupdates(self):
        with mock.patch('shutil.which', return_value='/usr/bin/checkupdates'):
            for code, expected in ((0, True), (2, False)):
                with mock.patch.object(arch, 'query', return_value=reply('', code)):
                    self.assertIs(arch.upgrades_pending(), expected)
            with mock.patch.object(arch, 'query', return_value=reply('', 1, 'Cannot fetch updates')), self.assertRaises(RuntimeError):
                arch.upgrades_pending()

    def test_without_checkupdates_the_upgrade_is_pending(self):
        for tools in (set(), {'checkupdates'}):
            with mock.patch('shutil.which', side_effect=lambda name: name if name in tools else None), \
                    mock.patch.object(arch, 'query') as query:
                self.assertTrue(arch.upgrades_pending())
            query.assert_not_called()

    def test_answers_are_kept_until_a_change(self):
        self.addCleanup(setattr, arch, 'answers', None)
        arch.remember_answers()
        with mock.patch.object(arch, 'run_query', return_value=reply('x')) as run, mock.patch('subprocess.run'):
            arch.query('pacman', '-Qi')
            arch.query('pacman', '-Qi')
            arch.query('systemctl', 'is-enabled', 'x')
            self.assertEqual(run.call_count, 2)
            arch.sudo('pacman', '-Rsc', '--noconfirm', 'a')
            arch.query('pacman', '-Qi')
            self.assertEqual(run.call_count, 3)
            arch.build_package(Path('/tmp/p'))
            arch.query('pacman', '-Qi')
            self.assertEqual(run.call_count, 4)

    def test_pacman_speaks_english_whatever_the_locale(self):
        with mock.patch('subprocess.run') as run:
            arch.run_query(('pacman', '-Qi'))
        self.assertEqual(run.call_args.kwargs['env']['LC_ALL'], 'C')

    def test_makepkg_runs_as_the_user_and_installs_what_it_built(self):
        with mock.patch('subprocess.run') as run:
            arch.build_package(Path('/cache/p'))
        command = run.call_args.args[0]
        self.assertEqual(command[0], 'makepkg')
        self.assertLessEqual({'--syncdeps', '--install', '--rmdeps', '--noconfirm'}, set(command))
        self.assertEqual(run.call_args.kwargs['cwd'], Path('/cache/p'))


class RepositoryTests(unittest.TestCase):
    def test_multilib_is_uncommented_where_the_default_file_has_it(self):
        enabled = arch.with_section(PACMAN_CONF, 'multilib', '/etc/pacman.d/mirrorlist')
        self.assertIn('\n[multilib]\nInclude = /etc/pacman.d/mirrorlist\n', enabled)
        self.assertIn('#[multilib-testing]', enabled)
        self.assertEqual(enabled.count('[multilib]'), 1)

    def test_enabling_twice_changes_nothing(self):
        enabled = arch.with_section(PACMAN_CONF, 'multilib', '/etc/pacman.d/mirrorlist')
        self.assertEqual(arch.with_section(enabled, 'multilib', '/etc/pacman.d/mirrorlist'), enabled)

    def test_a_file_without_the_section_gets_it_at_the_end_and_back(self):
        # The archlinux container image has such a file.
        original = '[options]\n\n[core]\nInclude = /etc/pacman.d/mirrorlist\n\nNoExtract = etc/pacman.conf\n'
        enabled = arch.with_section(original, 'multilib', '/etc/pacman.d/mirrorlist')
        self.assertTrue(enabled.endswith(f'\n\n{arch.MARK}\n[multilib]\nInclude = /etc/pacman.d/mirrorlist\n'))
        self.assertEqual(arch.without_section(enabled, 'multilib'), original)

    def test_line_ends_and_trailing_lines_stay_as_they_were(self):
        original = PACMAN_CONF.replace('\n', '\r\n') + '\n\n'
        enabled = arch.with_section(original, 'multilib', '/etc/pacman.d/mirrorlist')
        self.assertIn('[multilib]\r\nInclude = /etc/pacman.d/mirrorlist\r\n', enabled)
        self.assertEqual(arch.without_section(enabled, 'multilib'), original)

    def test_disabling_gives_the_default_file_back(self):
        enabled = arch.with_section(PACMAN_CONF, 'multilib', '/etc/pacman.d/mirrorlist')
        self.assertEqual(arch.without_section(enabled, 'multilib'), PACMAN_CONF)
        self.assertEqual(arch.without_section(PACMAN_CONF, 'multilib'), PACMAN_CONF)

    def test_settings_under_the_section_go_with_it(self):
        text = '[multilib]\nSigLevel = Required\nInclude = /etc/pacman.d/mirrorlist\n\n[extra]\nInclude = x\n'
        self.assertEqual(arch.without_section(text, 'multilib'),
                         '#[multilib]\n#SigLevel = Required\n#Include = /etc/pacman.d/mirrorlist\n\n[extra]\nInclude = x\n')

    def test_a_repository_is_missing_until_pacman_lists_it(self):
        with mock.patch.object(arch, 'query', return_value=reply('core\nextra\n')):
            self.assertTrue(arch.repo_missing({'name': 'multilib'}))
        with mock.patch.object(arch, 'query', return_value=reply('core\nextra\nmultilib\n')):
            self.assertFalse(arch.repo_missing({'name': 'multilib'}))

    def test_add_and_remove_write_pacman_conf_as_root(self):
        with tempfile.TemporaryDirectory() as folder:
            conf = Path(folder) / 'pacman.conf'
            conf.write_text(PACMAN_CONF)
            with mock.patch.object(arch, 'CONF', conf), mock.patch.object(arch, 'write_file') as write:
                arch.add_repo({'name': 'multilib', 'include': '/etc/pacman.d/mirrorlist'}, 'rolling')
                written = write.call_args.args
                self.assertEqual(written[0], conf)
                conf.write_text(written[1])
                arch.remove_repo({'name': 'multilib'})
                self.assertEqual(write.call_args.args[1], PACMAN_CONF)

    def test_packages_from_a_repository_are_the_installed_ones(self):
        lines = 'multilib steam 1.0.0.87-3 [installed]\nmultilib lib32-glibc 2.42-1 [installed: 2.41-1]\nmultilib wine 10-1\n'
        qi = 'Name : steam\nArchitecture : x86_64\n\nName : lib32-glibc\nArchitecture : x86_64\n'
        with mock.patch.object(arch, 'query', side_effect=lambda *c: reply(lines if c[1] == '-Sl' else qi)):
            self.assertEqual(arch.packages_from({'name': 'multilib'}), {'steam.x86_64', 'lib32-glibc.x86_64'})


class RemovalTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(arch, 'query', side_effect=lambda *command: reply(QI if command == ('pacman', '-Qi') else ''))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_long_value_goes_on_in_indented_lines(self):
        self.assertEqual(arch.local_packages()['webkitgtk-6.0']['depends'], ['gtk3', 'glib2'])

    def test_names_keep_their_dots(self):
        self.assertEqual(arch.installed_names(['webkitgtk-6.0', 'gdm']), ['webkitgtk-6.0.x86_64', 'gdm.x86_64'])
        self.assertEqual(arch.bare(['webkitgtk-6.0.x86_64']), ['webkitgtk-6.0'])

    def test_a_name_something_provides_gives_its_provider(self):
        self.assertEqual(arch.installed_names(['libgtk-3.so']), ['gtk3.x86_64'])

    def test_only_explicit_installs_count_as_by_hand(self):
        self.assertEqual(arch.installed_by_hand(['gdm.x86_64', 'gnome-shell.x86_64', 'webkitgtk-6.0.x86_64']),
                         {'gdm.x86_64', 'webkitgtk-6.0.x86_64'})

    def test_requirements_follow_dependencies_and_what_provides_them(self):
        self.assertEqual(arch.requirements(['gdm.x86_64']), {'gnome-shell.x86_64', 'libgdm.x86_64', 'glib2.x86_64', 'gtk3.x86_64'})

    def test_the_removal_preview_asks_pacman_for_names_without_the_architecture(self):
        with mock.patch.object(arch, 'query', return_value=reply('gdm.x86_64\nlibgdm.x86_64\n')) as query, \
                mock.patch.object(arch, 'left_behind', return_value=[]):
            self.assertEqual(arch.removal(['gdm.x86_64']), ['gdm.x86_64', 'libgdm.x86_64'])
        query.assert_called_once_with('pacman', '-Rsc', '--print', '--print-format', '%n.%a', '--', 'gdm')
        self.assertEqual(arch.removal([]), [])

    def test_a_refused_preview_stops(self):
        with mock.patch.object(arch, 'query', return_value=reply('', 1, 'error: target not found: x')), self.assertRaises(RuntimeError):
            arch.removal(['x.x86_64'])

    def test_remove_takes_what_depends_then_what_is_left_unneeded(self):
        with mock.patch.object(arch, 'sudo') as sudo, mock.patch.object(arch, 'cascade', return_value=['gdm.x86_64']), \
                mock.patch.object(arch, 'left_behind', return_value=['lib32-systemd.x86_64']):
            arch.remove(['gdm.x86_64', 'webkitgtk-6.0.x86_64'])
            arch.remove([])
        self.assertEqual(sudo.call_args_list, [mock.call('pacman', '-Rsc', '--noconfirm', '--', 'gdm', 'webkitgtk-6.0'),
                                               mock.call('pacman', '-Rs', '--noconfirm', '--', 'lib32-systemd')])


# Steam's 32-bit systemd, which -s keeps: device-mapper depends on a bare libudev.so, which it also provides.
STEAM = '''Name : steam
Architecture : x86_64
Depends On : lib32-systemd  bash
Install Reason : Explicitly installed

Name : lib32-systemd
Architecture : x86_64
Provides : libudev.so=1-32
Depends On : lib32-libgcrypt
Install Reason : Installed as a dependency for another package

Name : lib32-libgcrypt
Architecture : x86_64
Install Reason : Installed as a dependency for another package

Name : device-mapper
Architecture : x86_64
Depends On : libudev.so  systemd-libs
Install Reason : Installed as a dependency for another package

Name : systemd-libs
Architecture : x86_64
Provides : libudev.so=1-64
Install Reason : Installed as a dependency for another package

Name : bash
Architecture : x86_64
Install Reason : Installed as a dependency for another package
'''


class LeftBehindTests(unittest.TestCase):
    def setUp(self):
        self.asked = []
        patcher = mock.patch.object(arch, 'brought', return_value={'steam', 'lib32-systemd', 'lib32-libgcrypt'})
        patcher.start()
        self.addCleanup(patcher.stop)

    def answers(self, removals):
        def query(*command):
            if command == ('pacman', '-Qi'):
                return reply(STEAM)
            self.asked.append(command)
            return removals.pop(0)
        return mock.patch.object(arch, 'query', side_effect=query)

    def test_what_the_desktop_brought_and_nothing_needs_goes(self):
        with self.answers([reply('steam.x86_64\nlib32-systemd.x86_64\nlib32-libgcrypt.x86_64\n')]):
            self.assertEqual(arch.left_behind(['steam.x86_64']), ['lib32-systemd.x86_64', 'lib32-libgcrypt.x86_64'])
        # Only what the desktop brought: bash, there before, is not even asked about.
        self.assertEqual(self.asked, [('pacman', '-Rs', '--print', '--print-format', '%n.%a', '--', 'steam', 'lib32-libgcrypt', 'lib32-systemd')])

    def test_what_pacman_says_would_break_something_stays(self):
        refusal = reply('', 1, "error: failed to prepare transaction (could not satisfy dependencies)\n"
                               ":: removing lib32-systemd breaks dependency 'libudev.so=1-32' required by lib32-other\n")
        with self.answers([refusal, reply('steam.x86_64\nlib32-libgcrypt.x86_64\n')]):
            self.assertEqual(arch.left_behind(['steam.x86_64']), ['lib32-libgcrypt.x86_64'])
        self.assertEqual(self.asked[1][-2:], ('steam', 'lib32-libgcrypt'))

    def test_a_refusal_about_something_else_stops(self):
        with self.answers([reply('', 1, 'error: something else')]), self.assertRaises(RuntimeError):
            arch.left_behind(['steam.x86_64'])

    def test_nothing_brought_nothing_asked(self):
        with mock.patch.object(arch, 'brought', return_value=set()), self.answers([]):
            self.assertEqual(arch.left_behind(['steam.x86_64']), [])
        self.assertEqual(self.asked, [])


class HistoryTests(unittest.TestCase):
    LOG = '''[2026-11-01T00:03:58+0000] [ALPM] installed filesystem (2025.10.12-1)
[2026-11-01T00:03:59+0000] [ALPM] installed gdm (51.0-1)
[2026-11-05T10:00:00+0000] [PACMAN] Running 'pacman -Syu --noconfirm --needed sudo git python'
[2026-11-05T10:00:01+0000] [ALPM] transaction started
[2026-11-05T10:00:02+0000] [ALPM] installed git (2.56.0-1)
[2026-11-05T10:00:02+0000] [ALPM] upgraded filesystem (2025.10.12-1 -> 2026.10.12-1)
[2026-11-05T10:00:03+0000] [ALPM] removed gdm (51.0-1)
[2026-11-05T10:01:00+0000] [PACMAN] Running 'pacman -Syu --needed --noconfirm -- gdm hyprland'
[2026-11-05T10:01:02+0000] [ALPM] installed gdm (51.1.1-1)
[2026-11-05T10:01:02+0000] [ALPM] installed hyprland (0.57.1-1)
'''

    def history(self, text):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'pacman.log'
            log.write_text(text)
            with mock.patch.object(arch, 'LOG', log):
                return arch.history()

    def test_changes_before_any_command_are_a_transaction(self):
        transactions = self.history(self.LOG)
        self.assertEqual([t['command_line'] for t in transactions],
                         ['', 'pacman -Syu --noconfirm --needed sudo git python', 'pacman -Syu --needed --noconfirm -- gdm hyprland'])
        self.assertEqual(transactions[0]['packages'], [{'name': 'filesystem', 'action': 'installed'}, {'name': 'gdm', 'action': 'installed'}])

    def test_the_system_is_what_came_before_the_first_install_of_the_desktop(self):
        installed = 'Name : filesystem\nArchitecture : any\n\nName : git\nArchitecture : x86_64\n\nName : gdm\nArchitecture : x86_64\n'
        with mock.patch.object(arch, 'query', return_value=reply(installed)):
            self.assertEqual(arch.base_packages(self.history(self.LOG)), {'filesystem.any', 'git.x86_64'})

    def test_without_an_install_of_the_desktop_nobody_can_tell(self):
        with mock.patch.object(arch, 'query', return_value=reply('')):
            self.assertEqual(arch.base_packages(self.history(self.LOG.split("[2026-11-05T10:01:00")[0])), set())

    def test_the_desktop_brought_what_came_from_its_first_install_on(self):
        # makepkg's install of an AUR package included; gdm, there before and removed, came back with the desktop.
        log = self.LOG + ("[2026-11-05T10:02:00+0000] [PACMAN] Running 'pacman -U --config /etc/pacman.conf -- /p.pkg.tar.zst'\n"
                          "[2026-11-05T10:02:01+0000] [ALPM] installed zen-browser-bin (1.24b-1)\n")
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'pacman.log').write_text(log)
            with mock.patch.object(arch, 'LOG', Path(folder) / 'pacman.log'):
                self.assertEqual(arch.brought(), {'gdm', 'hyprland', 'zen-browser-bin'})
            (Path(folder) / 'pacman.log').write_text(self.LOG.split('[2026-11-05T10:01:00')[0])
            with mock.patch.object(arch, 'LOG', Path(folder) / 'pacman.log'):
                self.assertEqual(arch.brought(), set())

    def test_no_log_is_no_history(self):
        with mock.patch.object(arch, 'LOG', Path('/nonexistent/pacman.log')):
            self.assertEqual(arch.history(), [])


class SystemTests(unittest.TestCase):
    def test_firmware_is_installed_as_root_without_selinux(self):
        with mock.patch.object(arch, 'sudo') as sudo:
            arch.install_firmware(Path('/media/blob.bin'), '/usr/lib/firmware/x.bin')
        sudo.assert_called_once_with('install', '-D', '-o', 'root', '-g', 'root', '-m', '0644', '/media/blob.bin', '/usr/lib/firmware/x.bin')

    def test_the_initramfs_is_rebuilt_by_the_generator_installed(self):
        for tools, expected in (({'mkinitcpio', 'dracut'}, ('mkinitcpio', '-P')), ({'dracut'}, ('dracut', '--force', '--regenerate-all'))):
            with mock.patch('shutil.which', side_effect=lambda name: name if name in tools else None), \
                    mock.patch.object(arch, 'sudo') as sudo:
                arch.rebuild_initramfs()
            sudo.assert_called_once_with(*expected)
        with mock.patch('shutil.which', return_value=None), self.assertRaises(RuntimeError):
            arch.rebuild_initramfs()

    def test_tablet_sign_in_is_not_offered(self):
        self.assertEqual((arch.auth_pending(), arch.auth_reconstruct(['fprintd.x86_64'])), ([], []))
        with self.assertRaises(RuntimeError):
            arch.auth_apply(['x'], Path('/repo/tablet-auth.sh'))

    def test_owned_asks_pacman(self):
        with mock.patch.object(arch, 'query', return_value=reply('/etc/x is owned by y 1-1')) as query:
            self.assertTrue(arch.owned('/etc/x'))
        query.assert_called_once_with('pacman', '-Qo', '--', '/etc/x')


ITEM = {'package': 'zen-browser-bin', 'commit': 'a' * 40, 'version': '1.24b-1'}
TABLE = {'core': {'packages': ['a']}, 'apps': {'packages': ['base-devel'], 'aur': [ITEM, {**ITEM, 'package': 'p', 'key': 'https://k/p.asc'}]}}


def aur_plan(versions):
    distro = mock.Mock(PROTECTED=arch.PROTECTED, MANAGER='pacman')
    distro.version.side_effect = lambda package: versions.get(package, '')
    distro.installed.side_effect = lambda package: bool(versions.get(package))
    return installer.Plan(distro, 'rolling', TABLE, [], ('core', 'apps'))


class AurStepTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.home = Path(folder.name)
        home = mock.patch.object(Path, 'home', return_value=self.home)
        home.start()
        self.addCleanup(home.stop)

    def test_missing_or_another_version_is_pending(self):
        self.assertEqual(installer.aur_pending(aur_plan({'p': '1.24b-1'})), ['zen-browser-bin 1.24b-1'])
        self.assertEqual(installer.aur_pending(aur_plan({'zen-browser-bin': '1.23b-1', 'p': '1.24b-1'})),
                         ['zen-browser-bin 1.23b-1 -> 1.24b-1'])
        self.assertEqual(installer.aur_pending(aur_plan({'zen-browser-bin': '1.24b-1', 'p': '1.24b-1'})), [])

    def test_the_version_of_a_srcinfo(self):
        text = 'pkgbase = p\n\tpkgver = 1.2\n\tpkgrel = 3\n\tepoch = 2\n\npkgname = p\n\tpkgver = 9\n'
        self.assertEqual(installer.srcinfo_version(text), '2:1.2-3')
        self.assertEqual(installer.srcinfo_version('pkgbase = p\n\tpkgver = 1.24b\n\tpkgrel = 1\n'), '1.24b-1')

    def built_by(self, srcinfo, items):
        commands = []
        current = aur_plan({})

        def run(command, **kwargs):
            commands.append(tuple(command))
            if 'checkout' in command:
                path = Path(command[2])
                path.mkdir(parents=True, exist_ok=True)
                (path / '.SRCINFO').write_text(srcinfo)
            return reply()
        with mock.patch('subprocess.run', side_effect=run), mock.patch.object(installer, 'import_key') as key:
            installer.aur_apply(current, items)
        return commands, current.distro.build_package, key

    def test_apply_builds_the_pinned_commit_as_the_user(self):
        commands, build_package, key = self.built_by('pkgbase = x\n\tpkgver = 1.24b\n\tpkgrel = 1\n', ['zen-browser-bin 1.24b-1'])
        path = self.home / '.cache/dotfiles/aur/zen-browser-bin'
        self.assertIn(('git', '-C', str(path), 'fetch', '-q', '--depth', '1', 'https://aur.archlinux.org/zen-browser-bin.git', 'a' * 40), commands)
        self.assertFalse([command for command in commands if command[0] == 'sudo'])
        build_package.assert_called_once_with(path)
        key.assert_not_called()
        # The sources and the built package go; the PKGBUILD stays for the next update.
        self.assertEqual(commands[-1], ('git', '-C', str(path), 'clean', '-q', '-d', '-x', '--force'))

    def test_the_signing_key_comes_before_the_build(self):
        _, build_package, key = self.built_by('pkgbase = p\n\tpkgver = 1.24b\n\tpkgrel = 1\n', ['p 1.24b-1'])
        key.assert_called_once_with('https://k/p.asc')
        build_package.assert_called_once()

    def test_a_pin_that_builds_another_version_stops_before_building(self):
        with self.assertRaises(RuntimeError) as caught:
            self.built_by('pkgbase = x\n\tpkgver = 1.25b\n\tpkgrel = 1\n', ['zen-browser-bin 1.24b-1'])
        self.assertIn('1.25b-1', str(caught.exception))

    def test_only_what_apply_installs_is_recorded(self):
        record = {}
        installer.aur_remember(aur_plan({'p': '1.0-1'}), ['zen-browser-bin 1.24b-1', 'p 1.0-1 -> 1.24b-1'], record)
        self.assertEqual(record['packages'], ['zen-browser-bin'])

    def test_uninstall_removes_the_checkouts(self):
        (self.home / '.cache/dotfiles/aur/p').mkdir(parents=True)
        self.assertEqual(installer.unaur_pending(aur_plan({})), [str(self.home / '.cache/dotfiles/aur')])
        installer.unaur_apply(aur_plan({}), [])
        self.assertFalse((self.home / '.cache/dotfiles/aur').exists())
        self.assertEqual(installer.unaur_pending(aur_plan({})), [])

    def test_the_aur_step_comes_after_the_packages(self):
        titles = [step.title for step in installer.STEPS]
        self.assertEqual(titles.index('aur'), titles.index('packages') + 1)


class ReconstructTests(unittest.TestCase):
    def test_without_a_record_the_aur_packages_count_and_the_boot_target_stays(self):
        # Arch's base system boots into graphical.target already: only GDM, which came with the desktop, goes.
        distro = mock.Mock(PROTECTED=arch.PROTECTED, BASE_TARGET=arch.BASE_TARGET)
        distro.history.return_value = []
        distro.base_packages.return_value = {'base.x86_64'}
        distro.installed_names.side_effect = lambda specs: [spec + '.x86_64' for spec in specs if spec in ('gdm', 'zen-browser-bin')]
        distro.installed.return_value = False
        distro.repo_missing.return_value = True
        distro.auth_reconstruct.return_value = []
        current = installer.Plan(distro, 'rolling', {'core': {'packages': ['gdm']}, 'apps': {'aur': [ITEM]}}, [], ('core',))
        with mock.patch.object(installer, 'query', return_value=reply('graphical.target')), \
                mock.patch.object(installer, 'booted', return_value=False), mock.patch.object(installer, 'login_shell', return_value='/bin/bash'), \
                mock.patch('grp.getgrnam', return_value=mock.Mock(gr_mem=[])):
            record = installer.reconstruct(current)
        self.assertEqual(record['packages'], ['gdm.x86_64', 'zen-browser-bin.x86_64'])
        self.assertEqual(record['boot'], {'gdm': 'disabled'})


class PinTests(unittest.TestCase):
    MANIFEST = """[arch.apps]
packages = ['base-devel']

[[arch.apps.aur]]
package = 'zen-browser-bin'
commit = '{zen}'
version = '1.24b-1'

[[arch.apps.aur]]
package = '1password'
commit = '{one}'
version = '8.12.44-33'
key = 'https://downloads.1password.com/linux/keys/1password.asc'
"""

    def pins(self, heads, update=False):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'manifest.toml').write_text(self.MANIFEST.format(zen='a' * 40, one='b' * 40))
            out = io.StringIO()
            with mock.patch.object(installer, 'INSTALL', Path(folder)), mock.patch.object(installer, 'REPO', Path(folder)), \
                    mock.patch.object(installer, 'aur_head', side_effect=lambda package: heads[package]), \
                    mock.patch.object(installer, 'aur_srcinfo', side_effect=lambda package, commit: 'pkgbase = x\n\tpkgver = 1.25b\n\tpkgrel = 2\n'), \
                    mock.patch('sys.stdout', out):
                code = installer.pins(update)
            return code, out.getvalue(), (Path(folder) / 'manifest.toml').read_text()

    def test_nothing_newer(self):
        code, out, text = self.pins({'zen-browser-bin': 'a' * 40, '1password': 'b' * 40})
        self.assertEqual((code, out.strip()), (0, 'Every pin is at its latest commit.'))

    def test_a_newer_commit_is_shown_with_its_changes_and_not_written(self):
        code, out, text = self.pins({'zen-browser-bin': 'c' * 40, '1password': 'b' * 40})
        self.assertIn('zen-browser-bin 1.24b-1 -> 1.25b-2', out)
        self.assertIn(f'https://aur.archlinux.org/cgit/aur.git/diff/?h=zen-browser-bin&id={"c" * 40}&id2={"a" * 40}', out)
        self.assertIn('a' * 40, text)

    def test_update_rewrites_that_table_only(self):
        code, out, text = self.pins({'zen-browser-bin': 'c' * 40, '1password': 'b' * 40}, update=True)
        manifest = tomllib.loads(text)['arch']['apps']['aur']
        self.assertEqual((manifest[0]['commit'], manifest[0]['version']), ('c' * 40, '1.25b-2'))
        self.assertEqual((manifest[1]['commit'], manifest[1]['version']), ('b' * 40, '8.12.44-33'))
        self.assertEqual(text, self.MANIFEST.format(zen='c' * 40, one='b' * 40).replace("'1.24b-1'", "'1.25b-2'"))

    def test_an_aur_that_does_not_answer_fails(self):
        code, out, text = self.pins({'zen-browser-bin': '', '1password': 'b' * 40})
        self.assertEqual(code, 1)
        self.assertIn('zen-browser-bin: the AUR did not answer.', out)

    def test_pins_needs_no_supported_distribution(self):
        with mock.patch('os.geteuid', return_value=1000), mock.patch.object(installer, 'pins', return_value=0) as pins, \
                mock.patch.object(installer, 'load_plan') as load:
            self.assertEqual(installer.main(['pins', '--update']), 0)
        pins.assert_called_once_with(True)
        load.assert_not_called()

    def test_update_goes_with_pins_only(self):
        with mock.patch('os.geteuid', return_value=1000), mock.patch('sys.stderr'), self.assertRaises(SystemExit) as caught:
            installer.main(['apply', '--update'])
        self.assertEqual(caught.exception.code, 2)


class PluginTests(unittest.TestCase):
    def test_the_headers_are_in_hyprland_on_arch(self):
        with mock.patch.object(bundle, 'release_id', return_value='arch'):
            self.assertEqual(bundle.headers_package(), 'hyprland')
        with mock.patch.object(bundle, 'release_id', return_value='fedora'):
            self.assertEqual(bundle.headers_package(), 'hyprland-devel')

    def test_the_arch_build_is_read_with_pacman(self):
        with mock.patch.object(build, 'release_id', return_value='arch'), \
                mock.patch('subprocess.run', return_value=reply('hyprland 0.57.1-1\n')) as run:
            self.assertEqual(build.package_version('hyprland'), '0.57.1-1')
        self.assertEqual(run.call_args.args[0], ['pacman', '-Q', 'hyprland'])

    def test_what_a_package_provides_is_not_the_package(self):
        with mock.patch.object(build, 'release_id', return_value='arch'), \
                mock.patch('subprocess.run', return_value=reply('hyprland 0.57.1-1\n')), self.assertRaises(subprocess.CalledProcessError):
            build.package_version('wayland-compositor')

    def test_arch_s_build_is_verified_and_never_mismatched(self):
        self.assertIn('0.57.1-1', bundle.VERIFIED)
        with mock.patch.object(bundle, 'release_id', return_value='arch'), \
                mock.patch.object(bundle, 'package_version', side_effect=lambda package: '0.57.1-1' if package == 'hyprland' else ''):
            self.assertEqual(bundle.verify(), '0.57.1-1')

    def test_the_release_comes_from_os_release(self):
        with mock.patch.object(Path, 'read_text', return_value='NAME="Arch Linux"\nID=arch\nBUILD_ID=rolling\n'):
            self.assertEqual(build.release_id(), 'arch')
        with mock.patch.object(Path, 'read_text', side_effect=OSError):
            self.assertEqual(build.release_id(), '')


if __name__ == '__main__':
    unittest.main()
