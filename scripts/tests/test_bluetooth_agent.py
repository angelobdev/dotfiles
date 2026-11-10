#!/usr/bin/env python3
"""bluetooth_agent.py: only an explicit reply to the request still pending answers BlueZ, and a PIN or passkey must fit."""
from pathlib import Path
import sys
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
try:
    import bluetooth_agent  # noqa: E402
except ImportError:  # No PyGObject (a container without it): nothing to test here.
    bluetooth_agent = None


@unittest.skipIf(bluetooth_agent is None, 'PyGObject is not installed')
class FinishTests(unittest.TestCase):
    def agent(self, request_id, method):
        # Without __init__: no system bus. Only what finish() uses.
        agent = bluetooth_agent.Agent.__new__(bluetooth_agent.Agent)
        invocation = mock.Mock()
        agent.pending, agent.timeout, agent.display_device = (request_id, method, invocation), 0, '/org/bluez/hci0/dev_X'
        return agent, invocation

    def setUp(self):
        for patcher in (mock.patch.object(bluetooth_agent, 'emit'), mock.patch.object(bluetooth_agent, 'tr', side_effect=lambda key, values=(): key)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_a_reply_to_another_request_changes_nothing(self):
        agent, invocation = self.agent(4, 'RequestConfirmation')
        agent.finish(True, request_id=3)
        self.assertEqual(agent.pending[0], 4)
        invocation.return_value.assert_not_called()
        invocation.return_dbus_error.assert_not_called()

    def test_a_refusal_is_rejected_and_clears_the_prompt(self):
        agent, invocation = self.agent(4, 'RequestConfirmation')
        agent.finish(False, request_id=4)
        invocation.return_dbus_error.assert_called_once_with('org.bluez.Error.Rejected', 'bluetooth.errors.rejected')
        self.assertIsNone(agent.pending)
        bluetooth_agent.emit.assert_called_with(type='prompt', prompt=None)

    def test_a_pin_code_must_fit(self):
        for value, accepted in (('0000', True), ('1234567890123456', True), ('', False), ('x' * 17, False), ('12\x0034', False)):
            with self.subTest(value=value):
                agent, invocation = self.agent(1, 'RequestPinCode')
                agent.finish(True, value, request_id=1)
                if accepted:
                    self.assertEqual(invocation.return_value.call_args.args[0].unpack(), (value,))
                else:
                    invocation.return_dbus_error.assert_called_once_with('org.bluez.Error.Rejected', 'bluetooth.errors.invalidPin')

    def test_a_passkey_is_up_to_six_digits(self):
        for value, accepted in (('123456', True), ('7', True), ('1234567', False), ('12a', False), ('-1', False)):
            with self.subTest(value=value):
                agent, invocation = self.agent(1, 'RequestPasskey')
                agent.finish(True, value, request_id=1)
                if accepted:
                    self.assertEqual(invocation.return_value.call_args.args[0].unpack(), (int(value),))
                else:
                    invocation.return_dbus_error.assert_called_once_with('org.bluez.Error.Rejected', 'bluetooth.errors.invalidPasskey')

    def test_a_confirmation_answers_with_nothing(self):
        agent, invocation = self.agent(2, 'RequestConfirmation')
        agent.finish(True, request_id=2)
        invocation.return_value.assert_called_once_with(None)


if __name__ == '__main__':
    unittest.main()
