#!/usr/bin/env python3
"""Hyprland plugins: they are replaced only while none is loaded, and rebuilt at login when their packaging or Hyprland changes."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'scripts/hyprpm'))
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import build  # noqa: E402
import bundle  # noqa: E402
import plugins  # noqa: E402
spec = importlib.util.spec_from_file_location('install_hypr_plugins', REPO / 'scripts/install-hypr-plugins.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

RPM = '0.57.1-1.fc45.x86_64'
ABI = 'abi-one'
NAMES = sorted(build.PLUGINS)
SAMEFILE = os.path.samefile


class Home(unittest.TestCase):
    """A temporary home and hyprpm cache, with the stamp and repository state of a finished build."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.cache = self.root / 'cache'
        self.stamp_path = self.root / 'state/hypr-plugins.json'
        # No installer record: every plugin, whatever this machine's record says.
        for target, value in ((bundle, 'CACHE'), (bundle, 'STAMP'), (bundle, 'RECORD')):
            patcher = mock.patch.object(target, value, {'CACHE': self.cache, 'STAMP': self.stamp_path, 'RECORD': self.root / 'no-record.json'}[value])
            patcher.start()
            self.addCleanup(patcher.stop)
        home = mock.patch.object(Path, 'home', return_value=self.root / 'home')
        home.start()
        self.addCleanup(home.stop)
        # Fedora's packaging, whatever runs the tests: on Arch the headers are in hyprland itself (ArchPackageTests).
        release = mock.patch.object(bundle, 'release_id', return_value='fedora')
        release.start()
        self.addCleanup(release.stop)

    def built(self, digest=None, rpm=RPM, failed=False, abi=ABI):
        self.stamp_path.parent.mkdir(parents=True, exist_ok=True)
        self.stamp_path.write_text(json.dumps({'rpm': rpm, 'version': '0.57.1', 'abiHash': abi}))
        state = self.cache / bundle.REPOSITORY / 'state.toml'
        state.parent.mkdir(parents=True, exist_ok=True)
        source = self.root / 'home/.local/share/dotfiles/hyprpm' / (digest or bundle.digest())
        lines = ['[repository]', f"name = '{bundle.REPOSITORY}'", f"url = '{source.as_uri()}'"]
        for name in NAMES:
            lines += [f'[{name}]', f'failed = {"true" if failed else "false"}']
        state.write_text('\n'.join(lines) + '\n')
        (self.cache / 'state.toml').write_text(f"[state]\nhash = '{abi}'\n")


class StatusTests(Home):
    def status(self, rpm=RPM):
        with mock.patch.object(bundle, 'package_version', return_value=rpm):
            return bundle.status()

    def test_nothing_built_yet(self):
        self.assertEqual(self.status(), bundle.MISSING)

    def test_built_from_this_packaging_for_this_hyprland(self):
        self.built()
        self.assertEqual(self.status(), bundle.CURRENT)

    def test_another_packaging(self):
        self.built(digest='0123456789abcdef')
        self.assertEqual(self.status(), bundle.PACKAGING_CHANGED)

    def test_a_verified_hyprland_update(self):
        self.built(rpm='0.57.0-1.fc45.x86_64')
        self.assertEqual(self.status(), bundle.COMPOSITOR_CHANGED)

    def test_an_unverified_hyprland_update(self):
        self.built()
        self.assertEqual(self.status('0.58.0-1.fc45.x86_64'), bundle.UNVERIFIED)

    def test_a_rebuild_that_stopped_after_the_remove_is_incomplete(self):
        self.built()
        (self.cache / bundle.REPOSITORY / 'state.toml').unlink()
        self.assertEqual(self.status(), bundle.INCOMPLETE)

    def test_a_failed_plugin_is_incomplete(self):
        self.built(failed=True)
        self.assertEqual(self.status(), bundle.INCOMPLETE)

    def test_hyprland_and_its_headers_from_different_updates(self):
        self.built(rpm='0.57.0-1.fc45.x86_64')
        with mock.patch.object(bundle, 'package_version', side_effect=lambda package: RPM if package == 'hyprland' else '0.57.0-1.fc45.x86_64'):
            self.assertEqual(bundle.status(), bundle.MISMATCHED)

    def test_the_verified_builds_are_not_part_of_the_digest(self):
        self.assertNotIn('bundle.py', bundle.FILES)
        self.assertNotIn('VERIFIED', (bundle.PACKAGING / 'build.py').read_text())

    def test_the_bundle_is_what_hyprpm_builds_from(self):
        manifest = (bundle.PACKAGING / 'hyprpm.toml').read_text()
        self.assertIn('python3 build.py', manifest)
        self.assertEqual(set(bundle.FILES), {'build.py', 'hyprpm.toml', build.HYPRGRASS_PATCH.name})

    def test_verify_refuses_other_builds(self):
        with mock.patch.object(bundle, 'package_version', side_effect=lambda package: '0.58.0-1.fc45.x86_64'):
            with self.assertRaises(RuntimeError):
                bundle.verify()
        with mock.patch.object(bundle, 'package_version', side_effect=lambda package: RPM if package == 'hyprland' else 'other'):
            with self.assertRaises(RuntimeError):
                bundle.verify()
        with mock.patch.object(bundle, 'package_version', return_value=RPM):
            self.assertEqual(bundle.verify(), RPM)


class StateDirectory(unittest.TestCase):
    """plugins.py writes its rebuild state, log and lock in a temporary state directory."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.state = Path(folder.name)
        for name, value in (('STATE', self.state), ('REBUILD', self.state / 'plugin-rebuild.json'),
                            ('LOG', self.state / 'plugin-rebuild.log'), ('LOCK', self.state / 'plugin-rebuild.lock')):
            patcher = mock.patch.object(plugins, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def rebuild_state(self):
        return json.loads(plugins.REBUILD.read_text())


class LoginTests(StateDirectory):
    def login(self, state, matches=True):
        with mock.patch.object(bundle, 'status', return_value=state), mock.patch.object(bundle, 'stamp', return_value={}), \
                mock.patch.object(plugins, 'session_matches', return_value=matches), \
                mock.patch('subprocess.run') as run, mock.patch('subprocess.Popen') as popen:
            try:
                plugins.main([])
                exited = False
            except SystemExit:
                exited = True
        commands = [call.args[0] for call in run.call_args_list]
        return commands, popen, exited

    def test_a_first_install_is_left_to_the_installer(self):
        commands, popen, exited = self.login(bundle.MISSING)
        self.assertEqual((commands, exited), ([], False))
        popen.assert_not_called()

    def test_a_login_with_current_plugins_drops_an_old_request(self):
        plugins.write_rebuild({'wanted': bundle.PACKAGING_CHANGED})
        self.login(bundle.CURRENT)
        self.assertFalse(plugins.REBUILD.exists())

    def test_current_plugins_load(self):
        commands, popen, _ = self.login(bundle.CURRENT)
        self.assertEqual(commands, [['hyprpm', 'reload']])
        popen.assert_not_called()

    def test_a_changed_packaging_asks_the_shell_for_a_rebuild(self):
        # No terminal: the shell starts plugins.py rebuild once its polkit agent is up.
        for state in (bundle.INCOMPLETE, bundle.PACKAGING_CHANGED, bundle.COMPOSITOR_CHANGED):
            commands, popen, exited = self.login(state)
            self.assertNotIn(['hyprpm', 'reload'], commands)
            self.assertFalse(exited)
            popen.assert_not_called()
            self.assertEqual([command[0] for command in commands], ['notify-send'])
            self.assertEqual(self.rebuild_state()['wanted'], state)

    def test_an_unverified_hyprland_stays_without_plugins(self):
        for state in (bundle.UNVERIFIED, bundle.MISMATCHED):
            commands, popen, exited = self.login(state)
            self.assertTrue(exited)
            self.assertEqual([command[0] for command in commands], ['notify-send'])
            popen.assert_not_called()

    def test_another_binary_in_the_session_stays_without_plugins(self):
        commands, popen, exited = self.login(bundle.CURRENT, matches=False)
        self.assertTrue(exited)
        self.assertNotIn(['hyprpm', 'reload'], commands)

    def test_the_repository_is_found_through_the_link(self):
        self.assertEqual(plugins.REPO, REPO)


class InstallTests(Home):
    def install(self, in_use, status=bundle.CURRENT, abi=ABI):
        commands = []

        def run(*command, **_):
            commands.append(command)
            if command[:2] == ('hyprpm', 'remove'):
                (self.cache / bundle.REPOSITORY / 'state.toml').unlink()
            if command[:2] == ('hyprpm', 'add'):
                self.built()
            if command[:3] == ('sudo', 'rm', '-rf'):
                import shutil
                shutil.rmtree(command[-1])
            if command[:2] == ('sudo', 'install') and command[-1].endswith('state.toml'):
                Path(command[-1]).parent.mkdir(parents=True, exist_ok=True)
                Path(command[-1]).write_text(Path(command[-2]).read_text())

        replies = {
            ('hyprctl', '-j', 'version'): {'version': '0.57.1', 'commit': 'c', 'abiHash': abi},
            ('Hyprland', '--version-json'): {'version': '0.57.1', 'commit': 'c', 'abiHash': abi},
            ('hyprctl', '-j', 'instances'): [{'instance': 'sig', 'pid': 1}],
        }
        loaded = iter([set(NAMES) if in_use else set(), set(NAMES)])
        (self.cache / 'headersRoot/share/pkgconfig').mkdir(parents=True, exist_ok=True)
        (self.cache / 'headersRoot/share/pkgconfig/hyprland.pc').write_text('')
        # A reset cache seeds its headers again from the system's pkg-config file, which CI does not have.
        pc = self.root / 'hyprland.pc'
        pc.write_text('prefix=/usr/include\n')
        with mock.patch.dict(os.environ, {'HYPRLAND_INSTANCE_SIGNATURE': 'sig'}), mock.patch('os.geteuid', return_value=1000), \
                mock.patch.object(bundle, 'verify'), mock.patch.object(bundle, 'package_version', return_value=RPM), \
                mock.patch.object(bundle, 'status', return_value=status), \
                mock.patch.object(installer, 'json_of', side_effect=lambda *command: replies[command]), \
                mock.patch.object(installer, 'loaded', side_effect=lambda: next(loaded)), \
                mock.patch('os.path.samefile', side_effect=lambda a, b: str(a).startswith('/proc/') or SAMEFILE(a, b)), mock.patch('shutil.which', return_value='/usr/bin/Hyprland'), \
                mock.patch.object(installer, 'run', side_effect=run), mock.patch('subprocess.check_output', return_value=''), \
                mock.patch.object(installer, 'HYPRLAND_PC', pc), \
                mock.patch('builtins.print'):
            try:
                installer.main()
                message = None
            except SystemExit as stop:
                message = str(stop.code)
        return commands, message

    def hyprpm(self, commands):
        return [command[:2] for command in commands if command[0] == 'hyprpm']

    def test_nothing_to_do_touches_nothing(self):
        self.built()
        commands, message = self.install(in_use=True)
        self.assertEqual((commands, message), ([], None))

    def test_a_changed_packaging_is_never_swapped_in_the_session(self):
        self.built(digest='0123456789abcdef')
        commands, message = self.install(in_use=True, status=bundle.PACKAGING_CHANGED)
        self.assertEqual(message, installer.AT_LOGIN)
        self.assertEqual(self.hyprpm(commands), [])

    def test_at_login_a_changed_packaging_is_replaced(self):
        self.built(digest='0123456789abcdef')
        commands, message = self.install(in_use=False, status=bundle.PACKAGING_CHANGED)
        self.assertIsNone(message)
        hyprpm = self.hyprpm(commands)
        self.assertEqual(hyprpm[:2], [('hyprpm', 'remove'), ('hyprpm', 'add')])
        self.assertEqual(hyprpm[2:], [('hyprpm', 'enable')] * len(NAMES))

    def test_an_incomplete_build_is_replaced_at_login_too(self):
        self.built(failed=True)
        commands, _ = self.install(in_use=False, status=bundle.MISSING)
        self.assertEqual(self.hyprpm(commands)[:2], [('hyprpm', 'remove'), ('hyprpm', 'add')])

    def test_a_cache_for_another_abi_is_reset_only_without_plugins_loaded(self):
        self.built(abi='abi-old')
        commands, message = self.install(in_use=True, status=bundle.COMPOSITOR_CHANGED)
        self.assertEqual(message, installer.AT_LOGIN)
        self.assertFalse([command for command in commands if command[0] in ('sudo', 'hyprpm')])
        self.built(abi='abi-old')
        commands, message = self.install(in_use=False, status=bundle.COMPOSITOR_CHANGED)
        self.assertIsNone(message)
        self.assertIn(('sudo', 'rm', '-rf', '--', str(self.cache)), commands)
        self.assertIn(('hyprpm', 'add'), self.hyprpm(commands))

    def test_a_cache_shared_with_other_repositories_is_not_reset(self):
        self.built(abi='abi-old')
        (self.cache / 'someone-else').mkdir()
        commands, message = self.install(in_use=False, status=bundle.COMPOSITOR_CHANGED)
        self.assertIn('someone-else', message)
        self.assertFalse([command for command in commands if command[0] in ('sudo', 'hyprpm')])


class LoadedTests(unittest.TestCase):
    def test_hyprctl_answers_in_words_when_nothing_is_loaded(self):
        with mock.patch('subprocess.check_output', return_value='no plugins loaded\n'):
            self.assertEqual(installer.loaded(), set())

    def test_only_our_plugins_count(self):
        reply = json.dumps([{'name': 'hyprgrass'}, {'name': 'someone-else'}])
        with mock.patch('subprocess.check_output', return_value=reply):
            self.assertEqual(installer.loaded(), {'hyprgrass'})


class SelectionTests(unittest.TestCase):
    """Which plugins the installed profiles build: Hyprgrass only with tablet."""

    def record(self, value):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / 'install.json'
        path.write_text(json.dumps(value))
        patcher = mock.patch.object(bundle, 'RECORD', path)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_without_a_record_every_plugin(self):
        self.record('not a record')
        self.assertEqual(bundle.selected(), tuple(build.PLUGINS))

    def test_hyprgrass_only_with_tablet(self):
        self.record({'profiles': ['core', 'hardware', 'plugins', *bundle.PLUGIN_PARTS], 'profiles_version': bundle.PROFILES_VERSION})
        self.assertNotIn('hyprgrass', bundle.selected())
        self.record({'profiles': ['core', 'tablet', 'plugins', *bundle.PLUGIN_PARTS], 'profiles_version': bundle.PROFILES_VERSION})
        self.assertIn('hyprgrass', bundle.selected())

    def test_each_plugin_with_its_part(self):
        self.record({'profiles': ['core', 'plugins', 'plugins.hyprglass'], 'profiles_version': bundle.PROFILES_VERSION})
        self.assertEqual(bundle.selected(), ('hyprglass',))
        # A version 3 record: plugins was every plugin.
        self.record({'profiles': ['core', 'plugins'], 'profiles_version': 3})
        self.assertEqual(bundle.selected(), ('Hyprspace', 'hyprglass', 'HyprCapture'))

    def test_a_record_from_before_the_tablet_profile_keeps_hyprgrass(self):
        # hardware held what tablet holds now.
        self.record({'profiles': ['core', 'hardware', 'plugins']})
        self.assertEqual(bundle.recorded_profiles(), ['core', *bundle.UNITS_OF_V2['hardware'], 'tablet', 'plugins', *bundle.PLUGIN_PARTS])
        self.assertIn('hyprgrass', bundle.selected())
        self.record({'profiles': ['core', 'plugins']})
        self.assertNotIn('hyprgrass', bundle.selected())

    def test_a_version_2_record_in_the_names_of_version_3(self):
        # Only names change: what each old profile installed, in the units that hold it now.
        self.record({'profiles': ['core', 'tablet', 'apps', 'herdr', 'containers', 'media', 'gaming', 'steam-hidpi', 'codecs'],
                     'profiles_version': 2})
        self.assertEqual(bundle.recorded_profiles(), [
            'core', 'tablet', 'apps', 'apps.zen', 'apps.onepassword', 'apps.vscode', 'utils', 'utils.neovim', 'utils.gcc',
            'utils.xclip', 'utils.unrar', 'utils.fuse', 'utils.gh', 'utils.glab', 'utils.uv', 'utils.wev', 'assistant', 'containers',
            'utils.tailscale', 'radio', 'apps.loupe', 'apps.papers', 'apps.showtime', 'gaming', 'gaming.steam', 'gaming.gamescope',
            'gaming.steam-hidpi'])
        # Already version 3: as it is.
        self.record({'profiles': ['core', 'radio'], 'profiles_version': 3})
        self.assertEqual(bundle.recorded_profiles(), ['core', 'radio'])

    def test_the_full_set_keeps_its_digest(self):
        # A laptop with every plugin rebuilds nothing because of the selection.
        old = __import__('hashlib').sha256(b''.join((bundle.PACKAGING / name).read_bytes() for name in bundle.FILES)).hexdigest()[:16]
        self.assertEqual(bundle.digest(tuple(build.PLUGINS)), old)
        self.assertNotEqual(bundle.digest(bundle.selected(['core', 'plugins', *bundle.PLUGIN_PARTS])), old)

    def test_the_manifest_lists_only_the_selection(self):
        import tomllib
        full = tomllib.loads(bundle.manifest(tuple(build.PLUGINS)))
        self.assertEqual(set(full) - {'repository'}, set(build.PLUGINS))
        without = tomllib.loads(bundle.manifest(bundle.selected(['core', 'plugins', *bundle.PLUGIN_PARTS])))
        self.assertEqual(set(without) - {'repository'}, set(build.PLUGINS) - {'hyprgrass'})
        self.assertEqual(without['HyprCapture'], full['HyprCapture'])


class CacheTests(unittest.TestCase):
    """The build cache: one key per plugin, so moving one pin rebuilds only that plugin."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.cache = Path(folder.name)
        for patcher in (mock.patch.object(build, 'CACHE', self.cache),
                        mock.patch.object(build, 'package_version', return_value=RPM)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def keys(self):
        return {name: build.cache_key(name) for name in build.PLUGINS}

    def test_moving_one_pin_changes_only_its_key(self):
        before = self.keys()
        repo, revision, artifact = build.PLUGINS['Hyprspace']
        with mock.patch.dict(build.PLUGINS, {'Hyprspace': (repo, '0' * 40, artifact)}):
            after = self.keys()
        self.assertNotEqual(before['Hyprspace'], after['Hyprspace'])
        self.assertEqual({k: v for k, v in before.items() if k != 'Hyprspace'},
                         {k: v for k, v in after.items() if k != 'Hyprspace'})

    def test_the_patch_counts_only_for_hyprgrass(self):
        before = self.keys()
        patch = self.cache / 'other.patch'
        patch.write_text('another patch\n')
        with mock.patch.object(build, 'HYPRGRASS_PATCH', patch):
            after = self.keys()
        self.assertNotEqual(before['hyprgrass'], after['hyprgrass'])
        self.assertEqual(before['Hyprspace'], after['Hyprspace'])

    def test_another_hyprland_changes_every_key(self):
        before = self.keys()
        with mock.patch.object(build, 'package_version', return_value='0.58.0-1.fc45.x86_64'):
            after = self.keys()
        self.assertTrue(all(before[name] != after[name] for name in build.PLUGINS))

    def test_the_build_steps_are_part_of_every_key(self):
        before = self.keys()
        with mock.patch.object(build.inspect, 'getsource', return_value='other steps'):
            after = self.keys()
        self.assertTrue(all(before[name] != after[name] for name in build.PLUGINS))

    def test_prune_keeps_the_current_build_and_the_other_plugins(self):
        current = self.cache / 'Hyprspace/current'
        for path in (current, self.cache / 'Hyprspace/old', self.cache / 'hyprglass/kept',
                     self.cache / '1e76f99bfec7856f2614/Hyprspace'):
            path.mkdir(parents=True)
        build.prune('Hyprspace', 'current')
        self.assertEqual(sorted(p.relative_to(self.cache).as_posix() for p in self.cache.glob('*/*')),
                         ['Hyprspace/current', 'hyprglass/kept'])

    def test_a_cached_build_is_copied_without_building(self):
        key = build.cache_key('Hyprspace')
        cache = self.cache / 'Hyprspace' / key
        cache.mkdir(parents=True)
        (cache / 'Hyprspace.so').write_bytes(b'built')
        (cache / '.dotfiles-built').write_text('revision\n')
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        work = Path(folder.name)
        with mock.patch.object(build, 'run') as run:
            os.chdir(work)
            self.addCleanup(os.chdir, REPO)
            build.build('Hyprspace')
        run.assert_not_called()
        self.assertEqual((work / 'out/Hyprspace.so').read_bytes(), b'built')


class RebuildTests(StateDirectory):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(plugins, 'up_to_date', return_value=False)
        self.up_to_date = patcher.start()
        self.addCleanup(patcher.stop)

    def test_nothing_to_rebuild_asks_for_no_password(self):
        plugins.write_rebuild({'wanted': bundle.PACKAGING_CHANGED})
        self.up_to_date.return_value = True
        with mock.patch('subprocess.run') as run:
            self.assertEqual(plugins.main(['rebuild']), 0)
        run.assert_not_called()
        self.assertEqual((self.rebuild_state()['running'], self.rebuild_state()['status']), (False, 0))

    def test_the_rebuild_runs_the_installer_behind_one_pkexec_and_records_the_result(self):
        plugins.write_rebuild({'wanted': bundle.PACKAGING_CHANGED})
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if 'stdout' in kwargs and hasattr(kwargs['stdout'], 'write'):
                kwargs['stdout'].write('4 plugins installed and loaded\n')
            return mock.Mock(returncode=0)

        with mock.patch('subprocess.run', side_effect=run):
            self.assertEqual(plugins.main(['rebuild']), 0)
        runner = calls[0]
        self.assertEqual(runner[1:3], [str(plugins.HERE / 'privileged.py'), 'run'])
        self.assertEqual(runner[-1], str(REPO / 'scripts/install-hypr-plugins.py'))
        self.assertEqual(calls[1][0], 'notify-send')
        state = self.rebuild_state()
        self.assertEqual((state['running'], state['status'], state['reason']), (False, 0, bundle.PACKAGING_CHANGED))
        self.assertEqual(plugins.log_tail(), ['4 plugins installed and loaded'])

    def test_a_failed_rebuild_says_its_last_line(self):
        def run(command, **kwargs):
            if 'stdout' in kwargs and hasattr(kwargs['stdout'], 'write'):
                kwargs['stdout'].write('Authentication was cancelled: nothing was changed.\n')
            return mock.Mock(returncode=1)

        # The message names the log's last line, whatever the catalog says around it.
        with mock.patch('subprocess.run', side_effect=run) as runner, \
                mock.patch.object(plugins, 'tr', side_effect=lambda key, args=(): ' '.join([key, *args])):
            self.assertEqual(plugins.main(['rebuild']), 1)
        self.assertIn('Authentication was cancelled', runner.call_args_list[-1].args[0][-1])
        self.assertEqual(self.rebuild_state()['status'], 1)

    def test_one_rebuild_at_a_time(self):
        import fcntl
        with open(plugins.LOCK, 'a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            self.assertTrue(plugins.locked())
            with mock.patch('subprocess.run') as run, self.assertRaises(SystemExit):
                plugins.main(['rebuild'])
            run.assert_not_called()
            # Asked again at login while one runs: the running state stays.
            plugins.write_rebuild({'running': True})
            with mock.patch('subprocess.run'):
                plugins.ask_rebuild(bundle.PACKAGING_CHANGED)
            self.assertTrue(self.rebuild_state()['running'])
        self.assertFalse(plugins.locked())


class CacheCleanupTests(StateDirectory):
    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.cache = Path(folder.name)
        for patcher in (mock.patch.object(build, 'CACHE', self.cache), mock.patch.object(build, 'package_version', return_value=RPM)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.current = self.cache / 'Hyprspace' / build.cache_key('Hyprspace')
        for path in (self.current, self.cache / 'Hyprspace/old', self.cache / 'hyprglass/old', self.cache / '1e76f99bfec7856f2614/Hyprspace'):
            path.mkdir(parents=True)
            (path / 'file').write_bytes(b'x' * 10)

    def test_the_entries_and_their_sizes(self):
        entries = {(entry['plugin'], entry['key']): entry for entry in plugins.cache_entries()}
        self.assertTrue(entries[('Hyprspace', self.current.name)]['current'])
        self.assertFalse(entries[('Hyprspace', 'old')]['current'])
        self.assertFalse(entries[('', '1e76f99bfec7856f2614')]['current'])
        self.assertEqual(entries[('hyprglass', 'old')]['bytes'], 10)

    def test_old_entries_go_and_the_current_ones_stay(self):
        plugins.main(['clear-cache', 'old'])
        self.assertEqual([p.relative_to(self.cache).as_posix() for p in self.cache.glob('*/*')], [f'Hyprspace/{self.current.name}'])

    def test_all_of_it(self):
        plugins.main(['clear-cache', 'all'])
        self.assertFalse(self.cache.exists())

    def test_not_while_a_rebuild_runs(self):
        with mock.patch.object(plugins, 'locked', return_value=True), self.assertRaises(SystemExit):
            plugins.main(['clear-cache', 'all'])
        self.assertTrue(self.current.exists())


class Log(unittest.TestCase):
    def test_escape_sequences_and_redraws_are_gone(self):
        raw = '\x1b[2K\r\x1b[32mBuilding 10%\x1b[0m\r\x1b[2K\x1b[32mBuilding 100%\x1b[0m\n\n\x1b]0;title\x07done\r\n'
        self.assertEqual(plugins.clean_log(raw), ['Building 100%', 'done'])

    def test_plain_lines_stay(self):
        self.assertEqual(plugins.clean_log('one\ntwo\n'), ['one', 'two'])

    # Bytes, not text mode: universal newlines would turn each carriage return into a line.
    def test_tail_reads_the_cleaned_log(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / 'rebuild.log'
            log.write_text('\x1b[31ma\x1b[0m\nb\rc\n', encoding='utf-8')
            with mock.patch.object(plugins, 'LOG', log):
                self.assertEqual(plugins.log_tail(), ['a', 'c'])
                self.assertEqual(plugins.log_tail(1), ['c'])
            with mock.patch.object(plugins, 'LOG', Path(folder) / 'missing.log'):
                self.assertEqual(plugins.log_tail(), [])


if __name__ == '__main__':
    unittest.main()
