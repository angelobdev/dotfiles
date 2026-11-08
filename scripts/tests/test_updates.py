#!/usr/bin/env python3
"""updates.py: dnf or pacman, Flatpak and repository listings to updates.json, the Hyprland flag, errors kept apart."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import updates  # noqa: E402


def done(stdout='', code=0, stderr=''):
    return subprocess.CompletedProcess([], code, stdout, stderr)


class UpdatesTests(unittest.TestCase):
    def setUp(self):
        # Fedora, whatever runs the tests: ArchUpdatesTests covers pacman.
        release = mock.patch.object(updates, 'release_id', return_value='fedora')
        release.start()
        self.addCleanup(release.stop)
        # No fetch of this clone: RepositoryTests covers it.
        repository = mock.patch.object(updates, 'repository_updates', return_value=({}, None))
        repository.start()
        self.addCleanup(repository.stop)

    def test_dnf_lines_are_parsed_and_sorted(self):
        output = 'kernel\t7.2.14-200.fc44\tupdates\nhyprland\t0.56.3-1.fc44\tcopr:nett00n:hyprland\n\nnoise\n'
        self.assertEqual(updates.dnf_updates(output), [
            {'name': 'hyprland', 'version': '0.56.3-1.fc44', 'repo': 'copr:nett00n:hyprland'},
            {'name': 'kernel', 'version': '7.2.14-200.fc44', 'repo': 'updates'}])

    def test_flatpak_columns(self):
        self.assertEqual(updates.flatpak_updates('com.spotify.Client\t1.2.70\tflathub\n'),
                         [{'id': 'com.spotify.Client', 'version': '1.2.70', 'origin': 'flathub'}])

    def test_hyprland_sets_the_compositor_flag(self):
        replies = [done('hyprland\t0.56.3-1.fc44\tcopr\n'), done('')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check()
        self.assertTrue(result['compositor'])
        self.assertEqual((len(result['packages']), result['flatpaks'], result['errors']), (1, [], []))

    def test_a_failing_source_is_an_error_not_an_empty_list(self):
        replies = [done('', 1, 'Cannot download repomd.xml'), done('org.app\t2\tflathub\n')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check()
        self.assertEqual(result['errors'], ['updates.errors.dnf'])
        self.assertEqual(len(result['flatpaks']), 1)

    def test_a_failing_source_keeps_its_last_list(self):
        before = {'checked': 1.0, 'packages': [{'name': 'kernel', 'version': '1', 'repo': 'updates'}],
                  'flatpaks': [{'id': 'org.app', 'version': '1', 'origin': 'flathub'}]}
        replies = [done('', 1, 'Cannot download repomd.xml'), done('', 1, 'Unable to connect')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check(before)
        self.assertEqual((result['packages'], result['flatpaks'], result['checked']), (before['packages'], before['flatpaks'], 1.0))
        self.assertEqual(result['errors'], ['updates.errors.dnf', 'updates.errors.flatpak'])

    def test_a_failed_check_is_tried_again_later(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'updates.json'
            for errors, retried in (([], False), (['offline'], True)):
                with mock.patch.object(updates, 'STATE', state), mock.patch.object(updates, 'check', return_value={'errors': errors}), \
                        mock.patch.object(sys, 'argv', ['updates.py', 'check']), mock.patch.object(updates, 'retry_later') as retry:
                    updates.main()
                self.assertEqual(retry.called, retried)

    def test_check_writes_the_state_file(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'updates.json'
            with mock.patch.object(updates, 'STATE', state), mock.patch.object(updates, 'check', return_value={'packages': []}), \
                    mock.patch.object(sys, 'argv', ['updates.py', 'check']), mock.patch.object(updates, 'retry_later'):
                self.assertEqual(updates.main(), 0)
            self.assertEqual(json.loads(state.read_text()), {'packages': []})


class ArchUpdatesTests(unittest.TestCase):
    def setUp(self):
        release = mock.patch.object(updates, 'release_id', return_value='arch')
        release.start()
        self.addCleanup(release.stop)
        repository = mock.patch.object(updates, 'repository_updates', return_value=({}, None))
        repository.start()
        self.addCleanup(repository.stop)

    def test_checkupdates_lines_are_parsed_and_sorted(self):
        output = 'linux 7.2.14.arch1-1 -> 7.2.15.arch1-1\nhyprland 0.57.0-1 -> 0.57.1-1\nnoise\n'
        self.assertEqual(updates.pacman_updates(output), [
            {'name': 'hyprland', 'version': '0.57.1-1', 'repo': ''},
            {'name': 'linux', 'version': '7.2.15.arch1-1', 'repo': ''}])

    def test_checkupdates_runs_as_the_user_and_sets_the_compositor_flag(self):
        replies = [done('hyprland 0.57.0-1 -> 0.57.1-1\n'), done('')]
        with mock.patch.object(updates, 'run', side_effect=replies) as run, mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check()
        self.assertEqual(run.call_args_list[0].args[0], ['checkupdates', '--nocolor'])
        self.assertTrue(result['compositor'])
        self.assertEqual(result['errors'], [])

    def test_nothing_to_update_is_not_an_error(self):
        # checkupdates exits 2 when the system is current.
        replies = [done('', 2), done('')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check({'packages': [{'name': 'old', 'version': '1', 'repo': ''}]})
        self.assertEqual((result['packages'], result['errors']), ([], []))

    def test_a_failing_checkupdates_keeps_the_last_list(self):
        before = {'checked': 1.0, 'packages': [{'name': 'linux', 'version': '1', 'repo': ''}], 'flatpaks': []}
        replies = [done('', 1, '==> ERROR: Cannot fetch updates'), done('')]
        with mock.patch.object(updates, 'run', side_effect=replies), mock.patch('updates.tr', side_effect=lambda k, a=None: k):
            result = updates.check(before)
        self.assertEqual((result['packages'], result['errors']), (before['packages'], ['updates.errors.pacman']))


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.repo = Path(folder.name)
        (self.repo / '.git').mkdir()
        (self.repo / 'scripts').mkdir()
        (self.repo / 'scripts/install-desktop.py').write_text('', encoding='utf-8')
        for patcher in (mock.patch.object(updates, 'REPO', self.repo), mock.patch('updates.tr', side_effect=lambda k, a=None: k)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def repository(self, behind='3', ahead='0', dirty='', upstream=done('origin/main\n'), fetch=done()):
        answers = {'fetch': fetch, 'status': done(dirty), 'log': done('abc1234\tdocs: x\ndef5678\tfix: y\n')}

        def git(*arguments):
            if arguments[0] == 'rev-list':
                return done(behind if arguments[-1] == 'HEAD..@{u}' else ahead)
            if arguments[0] == 'rev-parse':
                return upstream if '--abbrev-ref' in arguments else done('fedcba9\n')
            return answers[arguments[0]]
        with mock.patch.object(updates, 'git', side_effect=git) as called:
            return updates.repository_updates(), called

    def test_new_commits_of_the_upstream(self):
        (state, error), called = self.repository()
        self.assertIsNone(error)
        self.assertEqual(state, {'upstream': 'origin/main', 'head': 'fedcba9', 'behind': 3, 'ahead': 0, 'dirty': False,
                                 'commits': [{'hash': 'abc1234', 'subject': 'docs: x'}, {'hash': 'def5678', 'subject': 'fix: y'}]})
        self.assertIn(('fetch', '--quiet', 'origin'), [call.args for call in called.call_args_list])

    def test_commits_of_its_own_and_local_changes_are_reported(self):
        (state, _), _ = self.repository(ahead='2', dirty=' M x')
        self.assertEqual((state['ahead'], state['dirty']), (2, True))

    def test_no_upstream_or_no_clone_lists_nothing(self):
        self.assertEqual(self.repository(upstream=done('', 128))[0], ({}, None))
        (self.repo / '.git').rmdir()
        with mock.patch.object(updates, 'git') as git:
            self.assertEqual(updates.repository_updates(), ({}, None))
        git.assert_not_called()

    def test_a_failed_fetch_is_an_error(self):
        (state, error), _ = self.repository(fetch=done('', 128, 'Could not resolve host: github.com'))
        self.assertIsNone(state)
        self.assertEqual(error, 'updates.errors.git')

    def test_git_never_prompts(self):
        with mock.patch.dict('os.environ', {}, clear=False), mock.patch('subprocess.run', return_value=done()) as run:
            updates.os.environ.pop('GIT_SSH_COMMAND', None)
            updates.git('fetch', '--quiet', 'origin')
        environment = run.call_args.kwargs['env']
        self.assertEqual((environment['GIT_TERMINAL_PROMPT'], environment['GIT_SSH_COMMAND']), ('0', 'ssh -o BatchMode=yes'))

    def test_a_failed_fetch_keeps_the_last_state_and_the_other_lists(self):
        before = {'checked': 1.0, 'packages': [], 'flatpaks': [], 'repository': {'behind': 2, 'commits': []}}
        with mock.patch.object(updates, 'system_updates', return_value=([], None)), \
                mock.patch.object(updates, 'flatpak_listing', return_value=([], None)), \
                mock.patch.object(updates, 'repository_updates', return_value=(None, 'updates.errors.git')):
            result = updates.check(before)
        self.assertEqual((result['repository'], result['errors'], result['failed']),
                         (before['repository'], ['updates.errors.git'], {'repository': 'updates.errors.git'}))
        self.assertGreater(result['checked'], 1.0)

    def test_a_check_of_the_repository_alone_keeps_the_rest(self):
        before = {'checked': 1.0, 'packages': [{'name': 'kernel', 'version': '2', 'repo': 'updates'}], 'flatpaks': [],
                  'repository': {'behind': 2}, 'errors': ['flatpak down'], 'failed': {'flatpaks': 'flatpak down'}}
        with mock.patch.object(updates, 'system_updates') as system, mock.patch.object(updates, 'flatpak_listing') as flatpak, \
                mock.patch.object(updates, 'repository_updates', return_value=({'behind': 0}, None)):
            result = updates.check(before, ['repository'])
        system.assert_not_called()
        flatpak.assert_not_called()
        self.assertEqual((result['packages'], result['repository'], result['errors'], result['checked']),
                         (before['packages'], {'behind': 0}, ['flatpak down'], 1.0))

    def test_check_repository_from_the_command_line(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'updates.json'
            with mock.patch.object(updates, 'STATE', state), mock.patch.object(updates, 'check', return_value={}) as check, \
                    mock.patch.object(sys, 'argv', ['updates.py', 'check', 'repository']), mock.patch.object(updates, 'retry_later'):
                self.assertEqual(updates.main(), 0)
            self.assertEqual(check.call_args.args[1], ['repository'])


class ApplyTests(unittest.TestCase):
    """apply: the updates screen's apply in the background, behind one pkexec only when root is needed."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        for name, value in (('STATE', root / 'updates.json'), ('APPLY', root / 'updates-apply.json'),
                            ('APPLY_LOG', root / 'updates-apply.log'), ('APPLY_LOCK', root / '.updates-apply.lock')):
            patcher = mock.patch.object(updates, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        # The message names the log's last line, whatever the catalog says around it.
        translate = mock.patch.object(updates, 'tr', side_effect=lambda key, args=(): ' '.join([key, *map(str, args)]))
        translate.start()
        self.addCleanup(translate.stop)

    def apply(self, keys, code=0, line='Done.'):
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if hasattr(kwargs.get('stdout'), 'write'):
                kwargs['stdout'].write(line + '\n')
            return done(code=code)

        with mock.patch('subprocess.run', side_effect=run):
            status = updates.main_with(['apply', keys])
        return status, calls

    def test_system_and_flatpak_go_through_the_root_broker(self):
        status, calls = self.apply('flatpak,system')
        self.assertEqual(status, 0)
        self.assertEqual(calls[0][1:3], [str(updates.HERE / 'privileged.py'), 'run'])
        self.assertEqual(calls[0][-3:], [str(updates.REPO / 'scripts/install-tui.py'), '--apply-updates', 'system,flatpak'])
        self.assertEqual(calls[1][0], 'notify-send')
        state = json.loads(updates.APPLY.read_text())
        self.assertEqual((state['running'], state['status'], state['keys']), (False, 0, ['system', 'flatpak']))
        self.assertEqual(updates.apply_status()['log'], ['Done.'])

    def test_a_pull_alone_asks_for_no_password(self):
        _, calls = self.apply('repository')
        self.assertNotIn(str(updates.HERE / 'privileged.py'), calls[0])
        self.assertEqual(calls[0][-2:], ['--apply-updates', 'repository'])

    def test_a_hyprland_update_says_the_plugins_rebuild_at_login(self):
        updates.STATE.write_text(json.dumps({'compositor': True}))
        _, calls = self.apply('system')
        self.assertIn('updates.apply.doneCompositor', calls[-1][-1])
        self.assertTrue(json.loads(updates.APPLY.read_text())['compositor'])

    def test_a_failure_says_the_last_line(self):
        status, calls = self.apply('system', code=1, line='Authentication was cancelled: nothing was changed.')
        self.assertEqual(status, 1)
        self.assertIn('Authentication was cancelled', calls[-1][-1])

    def test_unknown_keys_run_nothing(self):
        status, calls = self.apply('everything')
        self.assertEqual((status, calls), (2, []))

    def test_one_apply_at_a_time(self):
        import fcntl
        with updates.APPLY_LOCK.open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            status, calls = self.apply('system')
            self.assertEqual((status, calls), (1, []))
            updates.APPLY.write_text(json.dumps({'running': True}))
            self.assertTrue(updates.apply_status()['running'])
        # The lock is gone without a result: it stopped.
        self.assertEqual(updates.apply_status()['status'], -1)


if __name__ == '__main__':
    unittest.main()
