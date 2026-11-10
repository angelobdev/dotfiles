#!/usr/bin/env python3
"""network.py: the extras poll lists the saved connections once and asks for every Wi-Fi mode in one call."""
from pathlib import Path
import sys
import unittest
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import network  # noqa: E402

LISTING = ('Home:u-home:802-11-wireless:yes\n'
           'Work VPN:u-vpn:vpn:no\n'
           'Hotspot:u-ap:802-11-wireless:no\n'
           'lo:u-lo:loopback:yes\n')
# nmcli -g connection.uuid,802-11-wireless.mode with several connections: uuid, mode, then a blank line.
MODES = 'u-home\ninfrastructure\n\nu-ap\nap\n'


class ExtrasTests(unittest.TestCase):
    def nmcli(self, *args, secrets=False):
        self.calls.append(args)
        if args[:3] == ('-f', 'NAME,UUID,TYPE,ACTIVE', 'connection'):
            return LISTING
        if args[:2] == ('-g', 'connection.uuid,802-11-wireless.mode'):
            return MODES
        if args[:2] == ('-g', 'connection.type,GENERAL.DEVICES'):
            return '802-11-wireless\n\n'
        if args[:2] == ('-g', '802-11-wireless.ssid'):
            return 'My hotspot\n'
        raise AssertionError(args)

    def setUp(self):
        self.calls = []
        patcher = mock.patch.object(network, 'nmcli', side_effect=self.nmcli)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_one_listing_and_one_mode_query_whatever_the_profiles(self):
        listed = network.connections()
        self.assertEqual(network.vpns(listed), [{'name': 'Work VPN', 'uuid': 'u-vpn', 'type': 'vpn', 'active': False}])
        self.assertEqual(network.hotspot_profile(listed), 'u-ap')
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.calls[1][4:], ('u-home', 'u-ap'))

    def test_no_wifi_profile_needs_no_mode_query(self):
        self.assertEqual(network.hotspot_profile([('lo', 'u-lo', 'loopback', 'yes')]), '')
        self.assertEqual(self.calls, [])



class TimeoutTests(unittest.TestCase):
    def test_a_command_that_takes_too_long_gives_a_translated_error(self):
        with mock.patch.object(network.subprocess, 'run', side_effect=network.subprocess.TimeoutExpired('nmcli', 15)), \
                mock.patch.object(network, 'tr', side_effect=lambda key, values=(): f'{key} {values}'):
            with self.assertRaises(ValueError) as caught:
                network.nmcli('device', 'status')
        self.assertEqual(str(caught.exception), 'network.errors.noAnswer (15,)')

    def test_activations_wait_as_long_as_nmcli_does(self):
        with mock.patch.object(network.subprocess, 'run', return_value=mock.Mock(returncode=0, stdout='', stderr='')) as run, \
                mock.patch.object(network.sys, 'argv', ['network.py', 'vpn-up', 'u-vpn']), \
                mock.patch.object(network, 'vpns', return_value=[]), mock.patch('builtins.print'):
            network.main()
        self.assertEqual(run.call_args.args[0][-3:], ['connection', 'up', 'u-vpn'])
        self.assertEqual(run.call_args.kwargs['timeout'], network.ACTIVATION_TIMEOUT)
        self.assertGreater(network.ACTIVATION_TIMEOUT, 90)


if __name__ == '__main__':
    unittest.main()
