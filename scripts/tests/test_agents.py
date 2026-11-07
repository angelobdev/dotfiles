#!/usr/bin/env python3
"""agents.py: the shipped descriptors, the user's own winning by id, the primary agent and its command."""
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import agents  # noqa: E402

SHIPPED = REPO / 'shell/.local/share/desktop/agents'


class AgentsTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.own = self.root / 'own'
        self.own.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.shell_json = self.root / 'shell.json'
        # The catalogs of this tree (they are not stowed in CI), in English; no binary of the machine counts.
        for patcher in (
            mock.patch.object(agents, 'SHIPPED', SHIPPED),
            mock.patch.object(agents, 'OWN', self.own),
            mock.patch.object(agents, 'SHELL_JSON', self.shell_json),
            mock.patch.object(agents, 'LOCAL_BIN', self.bin),
            mock.patch.dict('os.environ', {'PATH': str(self.bin), 'XDG_CONFIG_HOME': str(REPO / 'quickshell/.config'),
                                           'LANG': 'en_US.UTF-8', 'LC_ALL': '', 'LC_MESSAGES': '', 'LANGUAGE': ''}),
            mock.patch('i18n.language', return_value='en_US'),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        os.environ.pop('DESKTOP_AI_AGENT', None)

    def install(self, binary):
        program = self.bin / binary
        program.write_text('#!/bin/sh\n', encoding='utf-8')
        program.chmod(program.stat().st_mode | stat.S_IXUSR)
        return str(program)

    def run_command(self, *arguments):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            agents.main(list(arguments))
        return out.getvalue().strip()

    def test_every_shipped_descriptor_is_valid(self):
        files = sorted(SHIPPED.glob('*.json'))
        self.assertEqual([path.stem for path in files], ['antigravity', 'claude', 'codex'])
        for path in files:
            with self.subTest(path.name):
                entry = json.loads(path.read_text(encoding='utf-8'))
                self.assertIsNotNone(agents.valid(entry))
                self.assertTrue(agents.ID.match(path.stem))
                self.assertTrue(entry['install'])

    def test_shipped_order_and_claude_hooks(self):
        listed = agents.agents()
        self.assertEqual([agent['id'] for agent in listed], ['claude', 'codex', 'antigravity'])
        self.assertEqual([agent['hooks'] for agent in listed], ['claude', '', ''])

    def test_invalid_descriptors_are_left_out(self):
        for name, entry in {
            'nobinary': {'name': 'A', 'command': ['a']},
            'badbinary': {'name': 'A', 'binary': 'a/b', 'command': ['a']},
            'nocommand': {'name': 'A', 'binary': 'a', 'command': []},
            'noimage': {'name': 'A', 'binary': 'a', 'command': ['a'], 'image': 'path'},
            'badneeds': {'name': 'A', 'binary': 'a', 'command': ['a'], 'needs': ['rm -rf']},
            'Bad_Id': {'name': 'A', 'binary': 'a', 'command': ['a']},
        }.items():
            (self.own / f'{name}.json').write_text(json.dumps(entry), encoding='utf-8')
        (self.own / 'broken.json').write_text('{', encoding='utf-8')
        self.assertEqual([agent['id'] for agent in agents.agents()], ['claude', 'codex', 'antigravity'])

    def test_own_descriptor_wins_and_adds(self):
        (self.own / 'codex.json').write_text(json.dumps({'name': 'My Codex', 'binary': 'codex', 'command': ['codex', '--full-auto'],
                                                         'order': 0}), encoding='utf-8')
        (self.own / 'aider.json').write_text(json.dumps({'name': 'Aider', 'binary': 'aider', 'command': ['aider']}),
                                             encoding='utf-8')
        listed = agents.agents()
        self.assertEqual([agent['id'] for agent in listed], ['codex', 'claude', 'antigravity', 'aider'])
        self.assertEqual(listed[0]['name'], 'My Codex')
        self.assertEqual(listed[0]['install'], '')

    def test_primary_follows_order_choice_and_override(self):
        self.assertIsNone(agents.primary())
        self.install('agy')
        self.install('codex')
        self.assertEqual(agents.primary()['id'], 'codex')
        self.shell_json.write_text(json.dumps({'aiPrimary': 'antigravity'}), encoding='utf-8')
        self.assertEqual(agents.primary()['id'], 'antigravity')
        # A choice that is not installed falls back to the order.
        self.shell_json.write_text(json.dumps({'aiPrimary': 'claude'}), encoding='utf-8')
        self.assertEqual(agents.primary()['id'], 'codex')
        with mock.patch.dict('os.environ', DESKTOP_AI_AGENT='agy'):
            self.assertEqual(agents.primary()['id'], 'antigravity')

    def test_list_reports_paths_and_missing_needs(self):
        path = self.install('claude')
        data = json.loads(self.run_command('list'))
        rows = {agent['id']: agent for agent in data['agents']}
        self.assertEqual(rows['claude']['path'], path)
        self.assertEqual(rows['codex']['path'], '')
        self.assertEqual(rows['codex']['missing'], ['npm'])
        self.assertEqual(data['primary'], 'claude')
        self.assertEqual((data['chosen'], data['override']), ('', ''))

    def test_argv_resolves_the_program(self):
        path = self.install('codex')
        self.assertEqual(json.loads(self.run_command('argv', 'codex')), [path])
        with self.assertRaisesRegex(ValueError, 'Claude Code is not installed'):
            self.run_command('argv', 'claude')
        with self.assertRaisesRegex(ValueError, 'No coding agent is called nope'):
            self.run_command('argv', 'nope')

    def test_image_text_per_agent(self):
        self.assertEqual(self.run_command('image', 'claude', '/tmp/a.png'), '/tmp/a.png')
        self.assertEqual(self.run_command('image', 'antigravity', '/tmp/a.png'), '@/tmp/a.png')

    def test_install_refuses_missing_needs(self):
        with mock.patch.object(agents.subprocess, 'run') as run, \
                self.assertRaisesRegex(ValueError, 'Codex needs npm to install'):
            self.run_command('install', 'codex')
        run.assert_not_called()

    def test_install_runs_in_a_terminal(self):
        self.install('curl')
        with mock.patch.object(agents.subprocess, 'run') as run:
            self.run_command('install', 'claude')
        argv = run.call_args.args[0]
        self.assertEqual(argv[:3], ['kitty', '--class', 'desktop-updates'])
        self.assertIn('https://claude.ai/install.sh', argv[-1])
        self.assertTrue(run.call_args.kwargs['env']['PATH'].startswith(str(self.bin)))


if __name__ == '__main__':
    unittest.main()
