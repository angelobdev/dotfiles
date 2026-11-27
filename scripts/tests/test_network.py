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


class SpeedTests(unittest.TestCase):
    def test_each_tool_in_mbit_per_second(self):
        import json
        ookla = json.dumps({'download': {'bandwidth': 12_500_000}, 'upload': {'bandwidth': 2_500_000}, 'ping': {'latency': 11.6}, 'server': {'name': 'Milano'}})
        self.assertEqual(network.speed_result('speedtest', ookla), {'down': 100.0, 'up': 20.0, 'ping': 12, 'server': 'Milano'})
        libre = json.dumps([{'download': 93.37, 'upload': 18.04, 'ping': 9.2, 'server': {'name': 'Roma'}}])
        self.assertEqual(network.speed_result('librespeed-cli', libre), {'down': 93.4, 'up': 18.0, 'ping': 9, 'server': 'Roma'})
        cli = json.dumps({'download': 50_000_000, 'upload': 10_000_000, 'ping': 20.4, 'server': {'sponsor': 'ISP'}})
        self.assertEqual(network.speed_result('speedtest-cli', cli), {'down': 50.0, 'up': 10.0, 'ping': 20, 'server': 'ISP'})

    def test_no_tool_no_test(self):
        with mock.patch.object(network.shutil, 'which', return_value=None):
            self.assertEqual(network.speed_test_tool(), '')
            with self.assertRaises(ValueError):
                network.speed_test()


class BandTests(unittest.TestCase):
    def test_a_band_is_set_and_reconnects(self):
        calls = []
        with mock.patch.object(network, 'connection', return_value=(network.WIFI, 'Home', 'wlan0')), \
                mock.patch.object(network, 'nmcli', side_effect=lambda *args, **kwargs: calls.append(args) or ''):
            network.set_band('u1', '5')
        self.assertEqual(calls[0], ('connection', 'modify', 'u1', '802-11-wireless.band', 'a'))
        self.assertEqual(calls[1], ('connection', 'up', 'u1'))

    def test_only_wifi_has_a_band(self):
        with mock.patch.object(network, 'connection', return_value=(network.WIRED, 'Cable', 'eth0')):
            with self.assertRaises(ValueError):
                network.set_band('u1', '5')


if __name__ == '__main__':
    unittest.main()
