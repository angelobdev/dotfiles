#!/usr/bin/env python3
"""agent.py: multi-agent discovery, session tailers, hook events, newest-wins lock, status line usage."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / 'shell/.local/libexec/desktop/agent.py'
sys.path.insert(0, str(HELPER.parent))
import agent  # noqa: E402


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.patches = [mock.patch.object(agent, 'RUNTIME', self.root / 'run'),
                        mock.patch.object(agent, 'STATE', self.root / 'run/agent.json'),
                        mock.patch.object(agent, 'SESSION', self.root / 'run/agent-session.json'),
                        mock.patch.object(agent, 'USAGE', self.root / 'state/agent-usage.json'),
                        mock.patch.object(agent, 'CONFIG', self.root / 'config/shell.json'),
                        mock.patch.object(agent, 'ACCOUNT', self.root / 'claude.json'),
                        mock.patch.object(agent, 'AGY_DIR', self.root / 'agy'),
                        mock.patch.object(agent, 'CODEX_DIR', self.root / 'codex'),
                        mock.patch.object(agent, 'GEMINI_DIR', self.root / 'gemini')]
        for patch in self.patches:
            patch.start()
        (self.root / 'claude.json').write_text(json.dumps({'oauthAccount': {'organizationRateLimitTier': 'default_claude_max_5x'}}))

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.directory.cleanup()

    def state(self):
        return json.loads(agent.STATE.read_text())

    def make_bin(self, *names):
        bindir = self.root / 'bin'
        bindir.mkdir(exist_ok=True)
        for name in names:
            exe = bindir / name
            exe.write_text('#!/bin/sh\nexit 0\n')
            exe.chmod(0o755)
        return str(bindir)

    def test_a_turn_goes_through_the_states(self):
        agent.hook({'hook_event_name': 'SessionStart', 'session_id': 's'}, 1)
        self.assertEqual((self.state()['state'], self.state()['agent'], self.state()['name']), ('ready', 'claude', 'Claude'))
        agent.hook({'hook_event_name': 'UserPromptSubmit', 'session_id': 's', 'prompt': 'hi'}, 2)
        self.assertEqual(self.state()['state'], 'working')
        agent.hook({'hook_event_name': 'PermissionRequest', 'session_id': 's', 'tool_name': 'Bash',
                    'tool_input': {'command': 'rm -rf build'}}, 3)
        self.assertEqual((self.state()['state'], self.state()['detail']), ('permission', 'Bash: rm -rf build'))
        agent.hook({'hook_event_name': 'Notification', 'session_id': 's', 'notification_type': 'permission_prompt',
                    'message': 'Claude needs your permission'}, 4)
        self.assertEqual(self.state()['detail'], 'Bash: rm -rf build')
        agent.hook({'hook_event_name': 'PostToolUse', 'session_id': 's', 'tool_name': 'Bash'}, 5)
        self.assertEqual(self.state()['state'], 'working')
        agent.hook({'hook_event_name': 'Stop', 'session_id': 's', 'last_assistant_message': 'Done.\n\nAll   good'}, 6)
        self.assertEqual((self.state()['state'], self.state()['detail']), ('finished', 'Done. All good'))
        agent.hook({'hook_event_name': 'SessionEnd', 'session_id': 's', 'reason': 'prompt_input_exit'}, 7)
        self.assertFalse(agent.STATE.exists())

    def test_an_older_event_never_overwrites_a_newer_one(self):
        agent.hook({'hook_event_name': 'Stop', 'session_id': 's', 'last_assistant_message': 'done'}, 20)
        agent.hook({'hook_event_name': 'PostToolUse', 'session_id': 's'}, 10)
        self.assertEqual(self.state()['state'], 'finished')

    def test_since_is_kept_while_the_state_stays(self):
        agent.hook({'hook_event_name': 'UserPromptSubmit', 'session_id': 's'}, 1_000_000_000)
        agent.hook({'hook_event_name': 'PostToolUse', 'session_id': 's'}, 5_000_000_000)
        self.assertEqual(self.state()['since'], 1.0)

    def test_idle_and_unknown_events_change_nothing(self):
        agent.hook({'hook_event_name': 'Stop', 'session_id': 's', 'last_assistant_message': 'done'}, 1)
        agent.hook({'hook_event_name': 'Notification', 'session_id': 's', 'notification_type': 'idle_prompt'}, 2)
        agent.hook({'hook_event_name': 'SomethingNew', 'session_id': 's'}, 3)
        self.assertEqual(self.state()['state'], 'finished')

    def test_the_hook_prints_nothing_and_exits_0_even_on_garbage(self):
        environment = {'XDG_RUNTIME_DIR': self.directory.name, 'PATH': '/usr/bin:/bin'}
        for payload in ('not json', '[]', json.dumps({'hook_event_name': 'Stop', 'last_assistant_message': 3})):
            result = subprocess.run([sys.executable, str(HELPER), 'hook'], input=payload, capture_output=True,
                                    text=True, env=environment, timeout=10)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))

    def test_status_line_keeps_the_last_limits_until_new_ones_arrive(self):
        data = {'model': {'display_name': 'Opus 5.5'}, 'context_window': {'used_percentage': 33.6},
                'rate_limits': {'five_hour': {'used_percentage': 23.5, 'resets_at': 1761760800},
                                'seven_day': {'used_percentage': 41.2, 'resets_at': 1762200000}}}
        with mock.patch('agent.tr', side_effect=lambda key, args=None: f'context {args[0]}%'):
            line = agent.statusline(data)
            self.assertEqual(line, 'Opus 5.5 · context 34% · 5h 24% · 7d 41%')
            usage = json.loads(agent.USAGE.read_text())
            self.assertEqual(usage['fiveHour'], {'used': 23.5, 'resets': 1761760800})
            self.assertEqual(usage['tier'], 'default_claude_max_5x')
            # A new session before its first reply: no rate_limits, the previous ones stay.
            agent.statusline({'model': {'display_name': 'Opus 5.5'}})
            kept = json.loads(agent.USAGE.read_text())
            self.assertEqual((kept['sevenDay'], kept['limitsUpdated']), (usage['sevenDay'], usage['limitsUpdated']))
            self.assertIsNone(kept['context'])
            # A window that expired is unknown, not 0%.
            agent.statusline({'rate_limits': {'seven_day': {'used_percentage': 42}}})
            self.assertIsNone(json.loads(agent.USAGE.read_text())['fiveHour'])
            # Switching to Antigravity status line drops Claude windows instead of mixing them.
            agy_line = agent.statusline({
                'product': 'antigravity',
                'plan_tier': 'pro',
                'model': {'display_name': 'Gemini 4 Argon', 'effort': 'high'},
                'context_window': {'used_percentage': 12.2},
                'quota': {'Gemini Pro': {'remaining_fraction': 0.8, 'reset_time': '2026-11-07T12:00:00Z'}},
            })
            self.assertEqual(agy_line, 'Gemini 4 Argon (High) · context 12% · Gemini Pro 20%')
            agy_usage = json.loads(agent.USAGE.read_text())
            self.assertEqual(agy_usage['agent'], 'antigravity')
            self.assertIsNone(agy_usage['fiveHour'])
            self.assertEqual(agy_usage['buckets'][0]['used'], 20.0)

    def test_agent_resolution_and_launch_commands(self):
        bindir = self.make_bin('agy', 'claude', 'aider')
        with mock.patch.object(agent, 'search_path', return_value=bindir):
            with mock.patch.dict(os.environ, {'DESKTOP_AI_AGENT': ''}, clear=False):
                detected = agent.resolve_agent()
                self.assertEqual((detected['available'], detected['agent'], detected['name']), (True, 'antigravity', 'Antigravity'))

            # shell.json aiAgent selects Codex even when missing, keeping its display name for the error notice.
            agent.CONFIG.parent.mkdir(parents=True, exist_ok=True)
            agent.CONFIG.write_text(json.dumps({'aiAgent': 'codex'}))
            with mock.patch.dict(os.environ, {'DESKTOP_AI_AGENT': ''}, clear=False):
                missing = agent.resolve_agent()
                self.assertEqual((missing['available'], missing['agent'], missing['name']), (False, 'codex', 'Codex'))

            # DESKTOP_AI_AGENT overrides shell.json; Claude gets session-only --settings, custom commands run as-is.
            with mock.patch.dict(os.environ, {'DESKTOP_AI_AGENT': 'claude --model opus'}, clear=False), \
                    mock.patch('agent.tr', return_value='italian'):
                launched = agent.launch_info()
                self.assertEqual((launched['agent'], launched['name']), ('claude', 'Claude'))
                self.assertIn('--settings', launched['command'])
                self.assertEqual(launched['command'][1:3], ['--model', 'opus'])

            with mock.patch.dict(os.environ, {'DESKTOP_AI_AGENT': 'aider --dark-mode'}, clear=False):
                custom = agent.launch_info()
                self.assertEqual((custom['available'], custom['agent'], custom['name']), (True, 'aider', 'Aider'))
                self.assertEqual(custom['command'][-1], '--dark-mode')

            # Nothing installed at all.
            with mock.patch.object(agent, 'search_path', return_value=str(self.root / 'empty')), \
                    mock.patch.dict(os.environ, {'DESKTOP_AI_AGENT': ''}, clear=False):
                agent.CONFIG.unlink()
                none_found = agent.resolve_agent()
                self.assertEqual((none_found['available'], none_found['agent'], none_found['name']), (False, '', ''))

    def test_antigravity_tailer_tracks_states_model_and_context(self):
        (agent.AGY_DIR / 'brain/conv1/.system_generated/logs').mkdir(parents=True)
        (agent.AGY_DIR / 'settings.json').write_text(json.dumps({
            'model': 'Gemini 4 Argon (High)',
            'toolPermission': 'proceed-in-sandbox',
            'agentMode': 'auto',
        }))
        transcript = agent.AGY_DIR / 'brain/conv1/.system_generated/logs/transcript.jsonl'
        # An old completed reply present when the console attaches stays ready rather than re-notifying.
        transcript.write_text(json.dumps({
            'type': 'PLANNER_RESPONSE', 'status': 'DONE', 'created_at': '2026-11-06T10:00:00Z',
            'input_tokens': 50_000, 'cache_read_tokens': 30_000, 'output_tokens': 500,
            'content': 'Earlier reply',
        }) + '\n')
        tailer = agent.AntigravityTailer(started=0.0)
        self.assertEqual(tailer.poll(now=1_800_000_000.0), ('ready', '', 'Gemini 4 Argon (High)', 8.1))

        def append(step):
            with transcript.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(step) + '\n')

        append({'type': 'USER_INPUT', 'source': 'USER_EXPLICIT',
                'content': '<USER_SETTINGS_CHANGE>The user changed setting `Model Selection` from X to Gemini 4 Flash.</USER_SETTINGS_CHANGE>'})
        self.assertEqual(tailer.poll(now=1_800_000_001.0)[:3], ('working', '', 'Gemini 4 Flash'))

        append({'type': 'PLANNER_RESPONSE', 'status': 'DONE', 'input_tokens': 100_000, 'output_tokens': 1000,
                'tool_calls': [{'name': 'run_command', 'args': {'CommandLine': '"pytest"', 'toolSummary': '"Run tests"'}}]})
        self.assertEqual(tailer.poll(now=1_800_000_002.0), ('working', 'run_command: Run tests', 'Gemini 4 Flash', 10.1))

        append({'type': 'PLANNER_RESPONSE', 'status': 'DONE',
                'tool_calls': [{'name': 'run_command', 'args': {'CommandLine': '"curl example.com"', 'BypassSandbox': '"true"'}}]})
        self.assertEqual(tailer.poll(now=1_800_000_003.0)[:2], ('permission', 'run_command: curl example.com'))

        append({'type': 'GENERIC', 'status': 'DONE', 'content': 'ok'})
        self.assertEqual(tailer.poll(now=1_800_000_004.0)[0], 'working')

        append({'type': 'PLANNER_RESPONSE', 'status': 'DONE', 'created_at': '2027-01-15T00:00:05Z',
                'content': 'All checks\npassed!'})
        self.assertEqual(tailer.poll(now=1_800_000_005.0)[:2], ('finished', 'All checks passed!'))

        append({'type': 'PLANNER_RESPONSE', 'status': 'ERROR', 'error': 'Quota exceeded'})
        self.assertEqual(tailer.poll(now=1_800_000_006.0)[:2], ('error', 'Quota exceeded'))

    def test_codex_and_gemini_tailers(self):
        rollout = agent.CODEX_DIR / 'sessions/2026/11/07/rollout-1.jsonl'
        rollout.parent.mkdir(parents=True)
        (agent.CODEX_DIR / 'config.toml').write_text('model = "gpt-5-codex"\n')
        rollout.write_text(json.dumps({'type': 'event_msg', 'payload': {'type': 'task_started'}}) + '\n')
        codex = agent.CodexTailer(started=0.0)
        self.assertEqual(codex.poll()[:3], ('working', '', 'gpt-5-codex'))
        with rollout.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps({'type': 'event_msg', 'payload': {'type': 'exec_approval_request', 'command': ['git', 'push']}}) + '\n')
        self.assertEqual(codex.poll()[:2], ('permission', 'git push'))
        with rollout.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps({'type': 'event_msg', 'payload': {'type': 'task_complete', 'last_agent_message': 'Pushed.'}}) + '\n')
        self.assertEqual(codex.poll()[:2], ('finished', 'Pushed.'))

        chat = agent.GEMINI_DIR / 'tmp/proj/chats/session-1.json'
        chat.parent.mkdir(parents=True)
        chat.write_text(json.dumps({'messages': [{'type': 'user', 'content': 'hello'}]}))
        gemini = agent.GeminiTailer(started=0.0)
        self.assertEqual(gemini.poll()[0], 'working')
        # Force mtime change for second write.
        chat.write_text(json.dumps({'messages': [{'type': 'gemini', 'model': 'gemini-2.5-pro',
                                                  'tokens': {'total': 150_000}, 'content': 'Hi there!'}]}))
        os.utime(chat, ns=(chat.stat().st_atime_ns, chat.stat().st_mtime_ns + 1_000_000))
        self.assertEqual(gemini.poll(), ('finished', 'Hi there!', 'gemini-2.5-pro', 15.0))

    def test_antigravity_statusline_toggle_and_exhausted_quota(self):
        agent.AGY_DIR.mkdir(parents=True)
        settings_path = agent.AGY_DIR / 'settings.json'
        settings_path.write_text(json.dumps({'model': 'Gemini 4 Argon', 'toolPermission': 'proceed-in-sandbox'}))
        self.assertEqual(agent.antigravity_statusline_state(), {'enabled': False, 'custom': False})

        self.assertEqual(agent.set_antigravity_statusline(True), {'enabled': True, 'custom': False})
        saved = json.loads(settings_path.read_text())
        self.assertEqual((saved['model'], saved['toolPermission']), ('Gemini 4 Argon', 'proceed-in-sandbox'))
        self.assertFalse(agent.CODEX_DIR.exists())
        self.assertFalse(agent.GEMINI_DIR.exists())

        self.assertEqual(agent.set_antigravity_statusline(False), {'enabled': False, 'custom': False})
        cleared = json.loads(settings_path.read_text())
        self.assertEqual(cleared['statusLine'], {'type': '', 'command': '', 'enabled': True})

        # Custom user statusLine commands are detected and never overwritten by turning ours off.
        settings_path.write_text(json.dumps({'statusLine': {'type': 'command', 'command': '/usr/local/bin/custom-sl'}}))
        self.assertEqual(agent.antigravity_statusline_state(), {'enabled': False, 'custom': True})
        agent.set_antigravity_statusline(False)
        self.assertEqual(json.loads(settings_path.read_text())['statusLine']['command'], '/usr/local/bin/custom-sl')

        # Exhausted Antigravity bucket omits remaining_fraction: 0.0 -> 100.0%, and fresh statusline wins over watch().
        with mock.patch('agent.tr', side_effect=lambda _key, args=None: f'context {args[0]}%'):
            agent.statusline({
                'product': 'antigravity',
                'model': {'display_name': 'Gemini 4 Argon'},
                'context_window': {'used_percentage': 42.4},
                'quota': {'Claude': {'reset_time': '2026-11-07T18:00:00Z'}},
            })
        usage = json.loads(agent.USAGE.read_text())
        self.assertEqual(usage['buckets'], [{'label': 'Claude', 'used': 100.0, 'resets': 1794074400.0}])
        agent.write_usage('antigravity', model='Stale Transcript Model', context=10.0)
        after_watch = json.loads(agent.USAGE.read_text())
        self.assertEqual((after_watch['model'], after_watch['context']), ('Gemini 4 Argon', 42.4))
        self.assertEqual(after_watch['buckets'][0]['used'], 100.0)

    def test_per_harness_image_formatting_and_directory_resolution(self):
        for at_agent in ('antigravity', 'gemini'):
            self.assertEqual(agent.format_image_arg('/tmp/shot.png', at_agent), '@/tmp/shot.png ')
        for plain_agent in ('claude', 'codex', 'opencode', 'pi', 'aider'):
            self.assertEqual(agent.format_image_arg('/tmp/shot.png', plain_agent), '/tmp/shot.png ')

        agent.RUNTIME.mkdir(parents=True, exist_ok=True)
        agent.SESSION.write_text(json.dumps({'agent': 'antigravity'}))
        self.assertEqual(agent.format_image_arg('/tmp/shot.png'), '@/tmp/shot.png ')
        agent.SESSION.write_text(json.dumps({'agent': 'codex'}))
        self.assertEqual(agent.format_image_arg('/tmp/shot.png'), '/tmp/shot.png ')

        proj = self.root / 'project'
        env_dir = self.root / 'env-dir'
        repo_dir = self.root / 'repo-dir'
        explicit_dir = self.root / 'explicit-dir'
        for folder in (proj, env_dir, repo_dir, explicit_dir):
            folder.mkdir()
        agent.CONFIG.parent.mkdir(parents=True, exist_ok=True)
        agent.CONFIG.write_text(json.dumps({'aiDirectory': str(proj)}))
        with mock.patch.dict(os.environ, {'DESKTOP_AI_DIRECTORY': ''}, clear=False):
            self.assertEqual(agent.resolve_directory(repo_fallback=str(repo_dir)), str(proj))
            self.assertEqual(agent.resolve_directory(explicit=str(explicit_dir), repo_fallback=str(repo_dir)), str(explicit_dir))
        with mock.patch.dict(os.environ, {'DESKTOP_AI_DIRECTORY': str(env_dir)}, clear=False):
            self.assertEqual(agent.resolve_directory(repo_fallback=str(repo_dir)), str(env_dir))

        bindir = self.make_bin('agy', 'codex')
        with mock.patch.object(agent, 'search_path', return_value=bindir), \
                mock.patch.dict(os.environ, {'DESKTOP_AI_AGENT': ''}, clear=False):
            probed = agent.probe_info()
            self.assertEqual(probed['installed'], ['antigravity', 'codex'])
            self.assertEqual((probed['autoAgent'], probed['autoName']), ('antigravity', 'Antigravity'))

    def test_inotify_watcher_wakes_on_file_write(self):
        watcher = agent.InotifyWatcher()
        try:
            watcher.sync([self.root])
            if watcher.has_inotify:
                def touch():
                    time.sleep(0.05)
                    (self.root / 'event.txt').write_text('ok')

                worker = threading.Thread(target=touch)
                worker.start()
                t0 = time.monotonic()
                watcher.wait(timeout=2.0)
                elapsed = time.monotonic() - t0
                worker.join()
                self.assertLess(elapsed, 1.0)
        finally:
            watcher.close()

    def test_main_reads_stdin(self):
        with mock.patch.object(sys, 'argv', ['agent.py', 'hook']), \
                mock.patch.object(sys, 'stdin', io.StringIO(json.dumps({'hook_event_name': 'SessionStart', 'session_id': 'x'}))):
            self.assertEqual(agent.main(), 0)
        self.assertEqual(self.state()['session'], 'x')


if __name__ == '__main__':
    unittest.main()
