#!/usr/bin/env python3
"""Root for one operation from Settings: one pkexec for the broker, and every sudo of the operation runs in it.

The broker runs here as the test user, started by a stand-in pkexec that claims root for it: the protocol, the
streams, the statuses and the shutdown are the same, only the privileges differ.
"""
from importlib.machinery import SourceFileLoader
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import privileged  # noqa: E402

BROKER = REPO / 'scripts/privileged/root-broker'
SHIM = REPO / 'shell/.local/libexec/desktop/root/sudo'


def load(name, path):
    loader = SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


shim = load('sudo_shim', SHIM)
broker = load('root_broker', BROKER)

# pkexec for the tests: the broker as this user, with PKEXEC_UID and the runtime directory a real pkexec would give.
FAKE_PKEXEC = '''#!/bin/sh
[ -n "$FAKE_PKEXEC_STATUS" ] && exit "$FAKE_PKEXEC_STATUS"
export PKEXEC_UID="$(id -u)"
exec python3 -I -c '
import os, sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
loader = SourceFileLoader("root_broker", sys.argv[1])
broker = module_from_spec(spec_from_loader("root_broker", loader))
loader.exec_module(broker)
broker.os.geteuid = lambda: 0
broker.RUNTIME = Path(sys.argv[2])
sys.argv = ["root-broker", sys.argv[3]]
broker.main()
' "$BROKER_PATH" "$FAKE_RUNTIME" "$2"
'''


class ShimArguments(unittest.TestCase):
    def test_a_command_with_options(self):
        self.assertEqual(shim.command(['-n', 'dnf', 'upgrade', '-y']), ['dnf', 'upgrade', '-y'])
        self.assertEqual(shim.command(['--', 'rm', '-rf', '--', '/x']), ['rm', '-rf', '--', '/x'])
        self.assertEqual(shim.command(['-E', 'install', '-m', '0644', 'a', 'b']), ['install', '-m', '0644', 'a', 'b'])

    def test_timestamp_calls_do_nothing(self):
        for arguments in (['-v'], ['-n', '-v'], ['-k'], ['-K'], []):
            self.assertIsNone(shim.command(arguments), arguments)

    def test_another_user_is_refused(self):
        with self.assertRaises(SystemExit):
            shim.command(['-u', 'nobody', 'id'])


class Broker(unittest.TestCase):
    def test_it_needs_pkexec(self):
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(broker.os, 'geteuid', return_value=0):
            with self.assertRaises(SystemExit):
                broker.caller()
        with mock.patch.object(broker.os, 'geteuid', return_value=1000), self.assertRaises(SystemExit):
            broker.caller()

    def test_the_socket_directory_is_the_users_and_private(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = Path(folder)
            uid = os.getuid()
            (runtime / str(uid)).mkdir()
            private = runtime / str(uid) / 'desktop-root.x'
            private.mkdir(mode=0o700)
            with mock.patch.object(broker, 'RUNTIME', runtime):
                self.assertEqual(broker.checked_directory(private / 'socket', uid), private)
                private.chmod(0o755)
                with self.assertRaises(SystemExit):
                    broker.checked_directory(private / 'socket', uid)
                with self.assertRaises(SystemExit):
                    broker.checked_directory(runtime / 'elsewhere' / 'socket', uid)
                with self.assertRaises(SystemExit):
                    broker.checked_directory(private / 'socket', uid + 1)


class Operation(unittest.TestCase):
    """privileged.run with the stand-in pkexec: the operation's sudo calls go through the broker."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        runtime = self.root / 'run'
        (runtime / str(os.getuid())).mkdir(parents=True, mode=0o700)
        tools = self.root / 'bin'
        tools.mkdir()
        pkexec = tools / 'pkexec'
        pkexec.write_text(FAKE_PKEXEC)
        pkexec.chmod(0o755)
        environment = {'PATH': f'{tools}:{os.environ["PATH"]}', 'XDG_RUNTIME_DIR': str(runtime / str(os.getuid())),
                       'BROKER_PATH': str(BROKER), 'FAKE_RUNTIME': str(runtime)}
        for patcher in (mock.patch.dict(os.environ, environment), mock.patch.object(privileged, 'installed', return_value=True)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.runtime = runtime / str(os.getuid())

    def test_sudo_runs_in_the_broker_with_the_streams_and_the_status(self):
        script = 'sudo -v && printf "%s\\n" "$(echo in | sudo sh -c "cat; echo \\$SUDO_UID; echo err >&2; exit 0")"; sudo sh -c "exit 7"; echo "status $?"'
        result = self.run_installed(script)
        self.assertEqual(result.stdout.split('\n')[:3], ['in', str(os.getuid()), 'status 7'], result.stderr)
        self.assertIn('err', result.stderr)
        self.assertEqual(result.returncode, 0)
        # The broker is gone with its socket and directory.
        self.assertEqual(list(self.runtime.iterdir()), [])

    def test_the_operations_status_is_returned(self):
        self.assertEqual(self.run_installed('exit 3').returncode, 3)

    def test_the_environment_is_reset_for_root(self):
        result = self.run_installed('SECRET=x sudo sh -c "echo ${SECRET:-none} \\$HOME \\$PATH"')
        self.assertEqual(result.stdout.split(), ['none', '/root', broker.PATH])

    def test_a_dismissed_prompt_runs_nothing(self):
        marker = self.root / 'ran'
        result = self.run_installed(f'touch {marker}', FAKE_PKEXEC_STATUS='126')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(marker.exists())
        self.assertEqual(list(self.runtime.iterdir()), [])

    def run_installed(self, script, **extra):
        # privileged.installed() is patched only in this process: the child checks the real path, so a copy of
        # privileged.py with the broker check passing stands in for it.
        copy = self.root / 'lib'
        if not copy.exists():
            copy.mkdir()
            source = (REPO / 'shell/.local/libexec/desktop/privileged.py').read_text()
            source = source.replace("SHIM = Path(__file__).resolve().parent / 'root'", f"SHIM = Path({str(SHIM.parent)!r})")
            (copy / 'privileged.py').write_text(source.replace('def installed():', 'def installed():\n    return True\n\n\ndef _installed():'))
        environment = {**os.environ, 'PYTHONPATH': str(REPO / 'shell/.local/libexec/desktop'), **extra}
        return subprocess.run([sys.executable, str(copy / 'privileged.py'), 'run', 'sh', '-c', script], capture_output=True,
                              text=True, timeout=30, env=environment)


class Installed(unittest.TestCase):
    def test_only_a_root_owned_copy_is_run(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'root-broker'
            path.write_text('#!/bin/sh\n')
            path.chmod(0o755)
            with mock.patch.object(privileged, 'BROKER', path):
                # Owned by the test user, not root.
                self.assertEqual(privileged.installed(), os.getuid() == 0)
            with mock.patch.object(privileged, 'BROKER', Path(folder) / 'missing'):
                self.assertFalse(privileged.installed())

    def test_the_manifest_installs_the_repositorys_broker_as_root_executable(self):
        import tomllib
        manifest = tomllib.loads((REPO / 'scripts/install/manifest.toml').read_text())
        for distro in ('fedora', 'arch'):
            entry = next(item for item in manifest[distro]['core']['files'] if item['path'] == str(privileged.BROKER))
            self.assertEqual((entry['source'], entry['mode']), ('scripts/privileged/root-broker', '0755'))
        self.assertTrue(BROKER.stat().st_mode & stat.S_IXUSR and SHIM.stat().st_mode & stat.S_IXOTH)


if __name__ == '__main__':
    unittest.main()
