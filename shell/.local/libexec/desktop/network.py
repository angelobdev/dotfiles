#!/usr/bin/env python3
"""Read and change NetworkManager details the Quickshell Networking API does not expose."""
from i18n import tr
import argparse
import ctypes
import ctypes.util
import ipaddress
import json
import os
import subprocess
import sys
import time

CLEAR_AFTER = 45
WIFI = '802-11-wireless'
PERSONAL = {'wpa-psk', 'sae'}


def nmcli(*args, secrets=False):
    result = subprocess.run(['nmcli', '-t', '-e', 'yes'] + (['-s'] if secrets else []) + list(args),
        capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        raise ValueError(tr('network.errors.commandFailed', ((result.stderr or result.stdout).strip()[:300],)))
    return result.stdout


def unescape(value):
    out, escaped = [], False
    for char in value:
        if escaped or char != '\\':
            out.append(char)
            escaped = False
        else:
            escaped = True
    return ''.join(out)


def split_terse(line):
    # nmcli -t escapes ':' and '\' inside values, so split on unescaped colons only.
    fields, current, escaped = [], [], False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            fields.append(''.join(current))
            current = []
        else:
            current.append(char)
    fields.append(''.join(current))
    return fields


def values(*args, secrets=False):
    lines = nmcli(*args, secrets=secrets).split('\n')
    return [unescape(line) for line in lines]


def multi(value, separator):
    return [item.strip() for item in value.split(separator) if item.strip()]


def connection(uuid):
    kind, device = values('-g', 'connection.type,GENERAL.DEVICES', 'connection', 'show', uuid)[:2]
    ssid = values('-g', '802-11-wireless.ssid', 'connection', 'show', uuid)[0] if kind == WIFI else ''
    return kind, ssid, device


def reapply(uuid):
    device = connection(uuid)[2]
    if device:
        nmcli('device', 'reapply', device.split(',')[0])


def details(device):
    fields = 'IP4.ADDRESS,IP4.GATEWAY,IP4.DNS,IP6.ADDRESS,IP6.GATEWAY,IP6.DNS,GENERAL.HWADDR,GENERAL.TYPE'
    ip4, gateway4, dns4, ip6, gateway6, dns6, mac, kind = values('-g', fields, 'device', 'show', device)[:8]
    data = {
        'device': device,
        'ipv4': multi(ip4, '|'),
        'gateway': gateway4 or gateway6,
        'ipv6': [address for address in multi(ip6, '|') if not address.lower().startswith('fe80')],
        'dns': multi(dns4, '|') + multi(dns6, '|'),
        'mac': mac,
    }
    if kind == 'wifi':
        for line in nmcli('-f', 'IN-USE,FREQ,CHAN,RATE', 'device', 'wifi', 'list', 'ifname', device, '--rescan', 'no').splitlines():
            active, frequency, channel, rate = (split_terse(line) + ['', '', '', ''])[:4]
            if active == '*':
                data.update(frequency=int(frequency.split()[0] or 0), channel=int(channel or 0), rate=rate)
                break
    return data


def profile(uuid):
    kind = connection(uuid)[0]
    fields = 'connection.autoconnect,connection.metered,ipv4.dns,ipv4.ignore-auto-dns,ipv6.dns,ipv6.ignore-auto-dns'
    if kind == WIFI:
        fields += ',802-11-wireless-security.key-mgmt'
    result = values('-g', fields, 'connection', 'show', uuid)
    autoconnect, metered, dns4, ignore4, dns6, ignore6 = result[:6]
    security = result[6] if kind == WIFI else ''
    dns = multi(dns4, ',') + multi(dns6, ',')
    return {
        'uuid': uuid,
        'type': kind,
        'autoconnect': autoconnect == 'yes',
        'metered': metered == 'yes',
        'dns': dns,
        'dnsAutomatic': not dns and ignore4 != 'yes' and ignore6 != 'yes',
        'personal': security in PERSONAL,
    }


def set_dns(uuid, servers):
    ipv4, ipv6 = [], []
    for server in servers:
        try:
            address = ipaddress.ip_address(server)
        except ValueError:
            raise ValueError(tr('network.errors.invalidDns', (server,))) from None
        (ipv4 if address.version == 4 else ipv6).append(str(address))
    # Custom servers replace the router's on both families, otherwise IPv6 would still use the router.
    custom = 'yes' if servers else 'no'
    nmcli('connection', 'modify', uuid, 'ipv4.dns', ','.join(ipv4), 'ipv4.ignore-auto-dns', custom,
        'ipv6.dns', ','.join(ipv6), 'ipv6.ignore-auto-dns', custom)
    reapply(uuid)


def set_option(uuid, option, enabled):
    if option == 'autoconnect':
        nmcli('connection', 'modify', uuid, 'connection.autoconnect', 'yes' if enabled else 'no')
        return
    # "unknown" lets NetworkManager guess again (for example on phone hotspots) instead of forcing "no".
    nmcli('connection', 'modify', uuid, 'connection.metered', 'yes' if enabled else 'unknown')
    reapply(uuid)


def secret(uuid):
    if connection(uuid)[0] != WIFI:
        raise ValueError(tr('network.errors.noSecret'))
    psk = values('-g', '802-11-wireless-security.psk', 'connection', 'show', uuid, secrets=True)[0]
    if not psk:
        raise ValueError(tr('network.errors.noSecret'))
    return psk


def copy_secret(uuid):
    psk = secret(uuid)
    subprocess.run(['wl-copy', '--sensitive'], input=psk, text=True, check=True, timeout=5)
    clearer = subprocess.Popen([sys.executable, os.path.abspath(__file__), 'clear-clipboard'],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    clearer.stdin.write(psk)
    clearer.stdin.close()


def clear_clipboard():
    psk = sys.stdin.read()
    time.sleep(CLEAR_AFTER)
    current = subprocess.run(['wl-paste', '--no-newline'], capture_output=True, text=True, timeout=5)
    # Leave anything the user copied afterwards alone.
    if current.returncode == 0 and current.stdout == psk:
        subprocess.run(['wl-copy', '--clear'], timeout=5)


def wifi_payload(uuid):
    kind, ssid, _ = connection(uuid)
    if kind != WIFI:
        raise ValueError(tr('network.errors.noSecret'))
    security, hidden = values('-g', '802-11-wireless-security.key-mgmt,802-11-wireless.hidden', 'connection', 'show', uuid)[:2]

    def escape(text):
        return ''.join('\\' + char if char in '\\;,:"' else char for char in text)
    if security in PERSONAL:
        payload = f'WIFI:T:WPA;S:{escape(ssid)};P:{escape(secret(uuid))};'
    elif security in ('', 'none', 'owe'):
        payload = f'WIFI:T:nopass;S:{escape(ssid)};'
    else:
        raise ValueError(tr('network.errors.noSecret'))
    return payload + ('H:true;' if hidden == 'yes' else '') + ';'


class QRcode(ctypes.Structure):
    _fields_ = [('version', ctypes.c_int), ('width', ctypes.c_int), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def qr(text):
    name = ctypes.util.find_library('qrencode')
    if not name:
        raise ValueError(tr('network.errors.qrUnavailable'))
    library = ctypes.CDLL(name)
    library.QRcode_encodeString.restype = ctypes.POINTER(QRcode)
    library.QRcode_encodeString.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    library.QRcode_free.argtypes = [ctypes.POINTER(QRcode)]
    # Version 0 = smallest fit, level M, 8-bit mode, case sensitive.
    code = library.QRcode_encodeString(text.encode('utf-8'), 0, 1, 2, 1)
    if not code:
        raise ValueError(tr('network.errors.qrUnavailable'))
    try:
        width = code.contents.width
        data = code.contents.data
        rows = [''.join('1' if data[y * width + x] & 1 else '0' for x in range(width)) for y in range(width)]
    finally:
        library.QRcode_free(code)
    return {'size': width, 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('details').add_argument('device')
    for name in ('profile', 'secret', 'copy-secret', 'qr'):
        commands.add_parser(name).add_argument('uuid')
    dns = commands.add_parser('set-dns')
    dns.add_argument('uuid')
    dns.add_argument('servers', nargs='*')
    option = commands.add_parser('set')
    option.add_argument('uuid')
    option.add_argument('option', choices=('autoconnect', 'metered'))
    option.add_argument('value', choices=('yes', 'no'))
    commands.add_parser('clear-clipboard')
    args = parser.parse_args()
    if args.command == 'clear-clipboard':
        clear_clipboard()
        return 0
    if args.command == 'details':
        result = details(args.device)
    elif args.command == 'profile':
        result = profile(args.uuid)
    elif args.command == 'secret':
        result = {'secret': secret(args.uuid)}
    elif args.command == 'copy-secret':
        copy_secret(args.uuid)
        result = {'copied': True, 'clearAfter': CLEAR_AFTER}
    elif args.command == 'qr':
        result = qr(wifi_payload(args.uuid))
    elif args.command == 'set-dns':
        set_dns(args.uuid, args.servers)
        result = profile(args.uuid)
    else:
        set_option(args.uuid, args.option, args.value == 'yes')
        result = profile(args.uuid)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
