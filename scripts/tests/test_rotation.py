#!/usr/bin/env python3
"""rotation.py: sensor orientations to Hyprland transforms, and the state file config/tablet.lua reads."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import rotation  # noqa: E402


class RotationTests(unittest.TestCase):
    def emitted(self, orientation):
        with mock.patch('sys.stdout', new=io.StringIO()) as output:
            rotation.emit(True, orientation)
        return json.loads(output.getvalue())

    def test_orientations_map_to_quarter_turns(self):
        for orientation, transform in (('normal', 0), ('left-up', 1), ('bottom-up', 2), ('right-up', 3)):
            self.assertEqual(self.emitted(orientation)['transform'], transform)

    def test_lying_flat_keeps_the_rotation(self):
        self.assertIsNone(self.emitted('undefined')['transform'])

    def test_apply_writes_the_lua_state_and_calls_hyprland(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / 'desktop-session/rotation.lua'
            done = mock.Mock(returncode=0, stdout='ok\n', stderr='')
            with mock.patch.object(rotation, 'STATE', state), mock.patch('subprocess.run', return_value=done) as run:
                rotation.apply(3)
            self.assertEqual(state.read_text(encoding='utf-8'), 'return { transform = 3 }\n')
            self.assertEqual(run.call_args.args[0][:2], ['hyprctl', 'eval'])
            self.assertIn('desktop_rotate(3)', run.call_args.args[0][2])

    def test_a_lua_error_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            failed = mock.Mock(returncode=0, stdout='attempt to call a nil value', stderr='')
            with mock.patch.object(rotation, 'STATE', Path(directory) / 'rotation.lua'), \
                    mock.patch('subprocess.run', return_value=failed):
                with self.assertRaises(ValueError):
                    rotation.apply(1)

    def test_usage_is_checked(self):
        for arguments in ([], ['apply'], ['apply', '4'], ['spin']):
            with mock.patch('sys.argv', ['rotation.py'] + arguments), self.assertRaises(ValueError):
                rotation.main()


if __name__ == '__main__':
    unittest.main()
