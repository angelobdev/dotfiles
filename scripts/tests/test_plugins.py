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
        for target, value in ((bundle, 'CACHE'), (bundle, 'STAMP')):
            patcher = mock.patch.object(target, value, {'CACHE': self.cache, 'STAMP': self.stamp_path}[value])
            patcher.start()
            self.addCleanup(patcher.stop)
        home = mock.patch.object(Path, 'home', return_value=self.root / 'home')
        home.start()
        self.addCleanup(home.stop)

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
        with mock.patch.object(bundle, 'rpm_version', return_value=rpm):
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
        with mock.patch.object(bundle, 'rpm_version', side_effect=lambda package: RPM if package == 'hyprland' else '0.57.0-1.fc45.x86_64'):
            self.assertEqual(bundle.status(), bundle.MISMATCHED)

    def test_the_verified_builds_are_not_part_of_the_digest(self):
        self.assertNotIn('bundle.py', bundle.FILES)
        self.assertNotIn('VERIFIED', (bundle.PACKAGING / 'build.py').read_text())

    def test_the_bundle_is_what_hyprpm_builds_from(self):
        manifest = (bundle.PACKAGING / 'hyprpm.toml').read_text()
        self.assertIn('python3 build.py', manifest)
        self.assertEqual(set(bundle.FILES), {'build.py', 'hyprpm.toml', build.HYPRGRASS_PATCH.name})

    def test_verify_refuses_other_builds(self):
        with mock.patch.object(bundle, 'rpm_version', side_effect=lambda package: '0.58.0-1.fc45.x86_64'):
            with self.assertRaises(RuntimeError):
                bundle.verify()
        with mock.patch.object(bundle, 'rpm_version', side_effect=lambda package: RPM if package == 'hyprland' else 'other'):
            with self.assertRaises(RuntimeError):
                bundle.verify()
        with mock.patch.object(bundle, 'rpm_version', return_value=RPM):
            self.assertEqual(bundle.verify(), RPM)


class LoginTests(unittest.TestCase):
    def login(self, state, matches=True):
        with mock.patch.object(bundle, 'status', return_value=state), mock.patch.object(bundle, 'stamp', return_value={}), \
                mock.patch.object(plugins, 'session_matches', return_value=matches), \
                mock.patch('subprocess.run') as run, mock.patch('subprocess.Popen') as popen:
            try:
                plugins.main()
                exited = False
            except SystemExit:
                exited = True
        commands = [call.args[0] for call in run.call_args_list]
        return commands, popen, exited

    def test_a_first_install_is_left_to_the_installer(self):
        commands, popen, exited = self.login(bundle.MISSING)
        self.assertEqual((commands, exited), ([], False))
        popen.assert_not_called()

    def test_current_plugins_load(self):
        commands, popen, _ = self.login(bundle.CURRENT)
        self.assertEqual(commands, [['hyprpm', 'reload']])
        popen.assert_not_called()

    def test_a_changed_packaging_is_rebuilt_instead_of_loaded(self):
        for state in (bundle.INCOMPLETE, bundle.PACKAGING_CHANGED, bundle.COMPOSITOR_CHANGED):
            commands, popen, exited = self.login(state)
            self.assertNotIn(['hyprpm', 'reload'], commands)
            self.assertFalse(exited)
            self.assertEqual(popen.call_args.args[0][-1], str(REPO / 'scripts/install-hypr-plugins.py'))
            self.assertEqual(popen.call_args.args[0][:2], ['kitty', '--hold'])

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
        with mock.patch.dict(os.environ, {'HYPRLAND_INSTANCE_SIGNATURE': 'sig'}), mock.patch('os.geteuid', return_value=1000), \
                mock.patch.object(bundle, 'verify'), mock.patch.object(bundle, 'rpm_version', return_value=RPM), \
                mock.patch.object(bundle, 'status', return_value=status), \
                mock.patch.object(installer, 'json_of', side_effect=lambda *command: replies[command]), \
                mock.patch.object(installer, 'loaded', side_effect=lambda: next(loaded)), \
                mock.patch('os.path.samefile', side_effect=lambda a, b: str(a).startswith('/proc/') or SAMEFILE(a, b)), mock.patch('shutil.which', return_value='/usr/bin/Hyprland'), \
                mock.patch.object(installer, 'run', side_effect=run), mock.patch('subprocess.check_output', return_value=''), \
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


if __name__ == '__main__':
    unittest.main()
