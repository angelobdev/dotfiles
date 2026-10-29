#!/usr/bin/env python3
"""agent.py: hook events to assistant states, newest event wins, silent hooks, status line usage."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
HELPER = REPO / 'shell/.local/libexec/desktop/agent.py'
sys.path.insert(0, str(HELPER.parent))
import agent  # noqa: E402


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.patches = [mock.patch.object(agent, 'RUNTIME', root / 'run'),
                        mock.patch.object(agent, 'STATE', root / 'run/agent.json'),
                        mock.patch.object(agent, 'USAGE', root / 'state/agent-usage.json'),
                        mock.patch.object(agent, 'ACCOUNT', root / 'claude.json')]
        for patch in self.patches:
            patch.start()
        (root / 'claude.json').write_text(json.dumps({'oauthAccount': {'organizationRateLimitTier': 'default_claude_max_5x'}}))

    def tearDown(self):
        for patch in self.patches:
            patch.stop()
        self.directory.cleanup()

    def state(self):
        return json.loads(agent.STATE.read_text())

    def test_a_turn_goes_through_the_states(self):
        agent.hook({'hook_event_name': 'SessionStart', 'session_id': 's'}, 1)
        self.assertEqual(self.state()['state'], 'ready')
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

    def test_main_reads_stdin(self):
        with mock.patch.object(sys, 'argv', ['agent.py', 'hook']), \
                mock.patch.object(sys, 'stdin', io.StringIO(json.dumps({'hook_event_name': 'SessionStart', 'session_id': 'x'}))):
            self.assertEqual(agent.main(), 0)
        self.assertEqual(self.state()['session'], 'x')


if __name__ == '__main__':
    unittest.main()
