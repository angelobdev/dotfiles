#!/usr/bin/env python3
"""Read and change NetworkManager details the Quickshell Networking API does not expose."""
from i18n import tr
import argparse
import ctypes
import ctypes.util
import ipaddress
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import time

CLEAR_AFTER = 45
WIFI = '802-11-wireless'
WIRED = '802-3-ethernet'
PERSONAL = {'wpa-psk', 'sae'}
VPN_TYPES = {'vpn', 'wireguard'}
# Values of {wifi,ethernet}.cloned-mac-address; '' leaves the choice to the system default.
MAC_MODES = {'default': '', 'private': 'stable-ssid', 'rotating': 'random', 'fixed': 'permanent'}


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
    fields = ('connection.autoconnect,connection.metered,ipv4.dns,ipv4.ignore-auto-dns,ipv6.dns,ipv6.ignore-auto-dns,'
        'ipv4.method,ipv4.addresses,ipv4.gateway')
    if kind == WIFI:
        fields += ',802-11-wireless.cloned-mac-address,802-11-wireless-security.key-mgmt'
    elif kind == WIRED:
        fields += ',802-3-ethernet.cloned-mac-address'
    result = values('-g', fields, 'connection', 'show', uuid) + ['', '']
    autoconnect, metered, dns4, ignore4, dns6, ignore6, method, addresses, gateway, mac, security = result[:11]
    dns = multi(dns4, ',') + multi(dns6, ',')
    mode = {'stable': 'private', 'stable-ssid': 'private', 'random': 'rotating', 'permanent': 'fixed'}.get(mac, 'default')
    return {
        'uuid': uuid,
        'type': kind,
        'autoconnect': autoconnect == 'yes',
        'metered': metered == 'yes',
        'dns': dns,
        'dnsAutomatic': not dns and ignore4 != 'yes' and ignore6 != 'yes',
        'personal': kind == WIFI and security in PERSONAL,
        'ipv4Method': method,
        'ipv4Address': (multi(addresses, ',') or [''])[0],
        'ipv4Gateway': gateway,
        'mac': mode if kind in (WIFI, WIRED) else '',
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


def set_ipv4(uuid, method, address, gateway):
    if method == 'auto':
        nmcli('connection', 'modify', uuid, 'ipv4.method', 'auto', 'ipv4.addresses', '', 'ipv4.gateway', '')
    else:
        try:
            interface = ipaddress.IPv4Interface(address)
        except ValueError:
            raise ValueError(tr('network.errors.invalidAddress', (address,))) from None
        if '/' not in address or interface.ip in (interface.network.network_address, interface.network.broadcast_address):
            raise ValueError(tr('network.errors.invalidAddress', (address,)))
        if gateway:
            try:
                router = ipaddress.IPv4Address(gateway)
            except ValueError:
                raise ValueError(tr('network.errors.invalidAddress', (gateway,))) from None
            if router not in interface.network:
                raise ValueError(tr('network.errors.gatewayOutside', (gateway, interface.network)))
        nmcli('connection', 'modify', uuid, 'ipv4.method', 'manual',
            'ipv4.addresses', interface.with_prefixlen, 'ipv4.gateway', gateway)
    reapply(uuid)


def set_mac(uuid, mode):
    kind, _, device = connection(uuid)
    if kind not in (WIFI, WIRED):
        raise ValueError(tr('network.errors.commandFailed', (kind,)))
    value = MAC_MODES[mode]
    if kind == WIRED and value == 'stable-ssid':
        value = 'stable'
    nmcli('connection', 'modify', uuid, ('802-11-wireless' if kind == WIFI else '802-3-ethernet') + '.cloned-mac-address', value)
    # The address is only chosen while activating, so an active connection has to reconnect.
    if device:
        nmcli('connection', 'up', uuid)


def add_hidden(device, ssid, secure):
    psk = sys.stdin.read().rstrip('\n') if secure else ''
    if not ssid.strip() or any(char in ssid for char in '\r\n'):
        raise ValueError(tr('network.errors.invalidSsid'))
    if secure and (any(char in psk for char in '\r\n') or not 8 <= len(psk) <= 64):
        raise ValueError(tr('network.errors.invalidPassword'))
    # The interactive editor reads the password from stdin, so it never appears in a process command line.
    # Saving with autoconnect on makes nmcli ask for confirmation; it is enabled once the network works.
    commands = ['set connection.id ' + ssid, 'set wifi.ssid ' + ssid, 'set wifi.hidden yes',
        'set connection.interface-name ' + device, 'set connection.autoconnect no']
    if secure:
        commands += ['set wifi-sec.key-mgmt wpa-psk', 'set wifi-sec.psk ' + psk]
    result = subprocess.run(['nmcli', 'connection', 'edit', 'type', 'wifi'], input='\n'.join(commands + ['save persistent', 'quit']) + '\n',
        capture_output=True, text=True, timeout=15)
    # Without a terminal nmcli reports the saved profile on stderr.
    saved = [line for line in (result.stderr + result.stdout).splitlines() if 'successfully saved' in line]
    if result.returncode != 0 or not saved:
        # stdout echoes the editor session, password included, so only stderr is reported.
        raise ValueError(tr('network.errors.commandFailed', (result.stderr.strip()[-300:] or result.returncode,)))
    uuid = saved[-1].rsplit('(', 1)[1].split(')', 1)[0]
    activation = subprocess.run(['nmcli', 'connection', 'up', uuid], capture_output=True, text=True, timeout=60)
    if activation.returncode != 0:
        # Do not leave a broken profile behind for a mistyped name or password.
        subprocess.run(['nmcli', 'connection', 'delete', uuid], capture_output=True, timeout=15)
        raise ValueError(tr('network.errors.commandFailed', ((activation.stderr or activation.stdout).strip()[:300],)))
    nmcli('connection', 'modify', uuid, 'connection.autoconnect', 'yes')
    return uuid


def vpns():
    found = []
    for line in nmcli('-f', 'NAME,UUID,TYPE,ACTIVE', 'connection', 'show').splitlines():
        name, uuid, kind, active = (split_terse(line) + ['', '', '', ''])[:4]
        if kind in VPN_TYPES:
            found.append({'name': name, 'uuid': uuid, 'type': kind, 'active': active == 'yes'})
    return sorted(found, key=lambda vpn: vpn['name'].lower())


def edit(uuid, commands):
    # The interactive editor reads values from stdin, so secrets never appear in a process command line.
    result = subprocess.run(['nmcli', 'connection', 'edit', uuid], input='\n'.join(commands + ['save persistent', 'quit']) + '\n',
        capture_output=True, text=True, timeout=15)
    if result.returncode != 0 or 'successfully' not in result.stderr + result.stdout:
        raise ValueError(tr('network.errors.commandFailed', (result.stderr.strip()[-300:] or result.returncode,)))


def hotspot_profile():
    for line in nmcli('-f', 'UUID,TYPE', 'connection', 'show').splitlines():
        uuid, kind = (split_terse(line) + ['', ''])[:2]
        if kind == WIFI and values('-g', '802-11-wireless.mode', 'connection', 'show', uuid)[0] == 'ap':
            return uuid
    return ''


def hotspot():
    uuid = hotspot_profile()
    if not uuid:
        return {'uuid': '', 'ssid': '', 'active': False}
    _, ssid, device = connection(uuid)
    return {'uuid': uuid, 'ssid': ssid, 'active': bool(device)}


def hotspot_on(device):
    uuid = hotspot_profile()
    if not uuid:
        name = socket.gethostname().split('.')[0] or 'Linux'
        output = nmcli('connection', 'add', 'type', 'wifi', 'ifname', device, 'con-name', 'Hotspot', 'ssid', name,
            '802-11-wireless.mode', 'ap', '802-11-wireless.band', 'bg', 'ipv4.method', 'shared', 'ipv6.method', 'shared',
            'connection.autoconnect', 'no', 'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.proto', 'rsn', 'wifi-sec.pairwise', 'ccmp')
        uuid = output.rsplit('(', 1)[1].split(')', 1)[0]
        # Unambiguous characters only, so the password is easy to type on a phone.
        alphabet = 'abcdefghjkmnpqrstuvwxyz23456789'
        edit(uuid, ['set wifi-sec.psk ' + ''.join(secrets.choice(alphabet) for _ in range(12))])
    nmcli('connection', 'up', uuid, 'ifname', device)
    return hotspot()


def hotspot_off():
    uuid = hotspot_profile()
    if uuid and connection(uuid)[2]:
        nmcli('connection', 'down', uuid)
    return hotspot()


def tailscale():
    if not shutil.which('tailscale'):
        return {'installed': False}
    result = subprocess.run(['tailscale', 'status', '--json'], capture_output=True, text=True, timeout=10)
    try:
        data = json.loads(result.stdout)
    except ValueError:
        return {'installed': True, 'state': 'Unavailable'}
    peers = list((data.get('Peer') or {}).values())
    exit_node = next((peer.get('HostName', '') for peer in peers if peer.get('ExitNode')), '')
    addresses = (data.get('Self') or {}).get('TailscaleIPs') or []
    return {
        'installed': True,
        'state': data.get('BackendState', ''),
        'tailnet': (data.get('CurrentTailnet') or {}).get('Name', ''),
        'address': next((address for address in addresses if ':' not in address), ''),
        'peers': len(peers),
        'online': sum(1 for peer in peers if peer.get('Online')),
        'exitNode': exit_node,
    }


def tailscale_toggle(up):
    # The current user must be the Tailscale operator (tailscale set --operator=$USER) to do this without root.
    result = subprocess.run(['tailscale', 'up' if up else 'down'], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise ValueError(tr('network.errors.commandFailed', ((result.stderr or result.stdout).strip()[:300],)))
    return tailscale()


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
    ipv4 = commands.add_parser('set-ipv4')
    ipv4.add_argument('uuid')
    ipv4.add_argument('method', choices=('auto', 'manual'))
    ipv4.add_argument('address', nargs='?', default='')
    ipv4.add_argument('gateway', nargs='?', default='')
    mac = commands.add_parser('set-mac')
    mac.add_argument('uuid')
    mac.add_argument('mode', choices=tuple(MAC_MODES))
    hidden = commands.add_parser('add-hidden', description='The password, if any, is read from stdin.')
    hidden.add_argument('device')
    hidden.add_argument('ssid')
    hidden.add_argument('--secure', action='store_true')
    commands.add_parser('vpn')
    for name in ('vpn-up', 'vpn-down'):
        commands.add_parser(name).add_argument('uuid')
    commands.add_parser('hotspot')
    commands.add_parser('hotspot-on').add_argument('device')
    commands.add_parser('hotspot-off')
    # One poll for everything the panel list shows besides Quickshell's own devices.
    commands.add_parser('extras')
    for name in ('tailscale', 'tailscale-up', 'tailscale-down'):
        commands.add_parser(name)
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
    elif args.command == 'set-ipv4':
        set_ipv4(args.uuid, args.method, args.address, args.gateway)
        result = profile(args.uuid)
    elif args.command == 'set-mac':
        set_mac(args.uuid, args.mode)
        result = profile(args.uuid)
    elif args.command == 'add-hidden':
        result = {'uuid': add_hidden(args.device, args.ssid, args.secure)}
    elif args.command == 'vpn':
        result = {'vpn': vpns()}
    elif args.command in ('vpn-up', 'vpn-down'):
        nmcli('connection', 'up' if args.command == 'vpn-up' else 'down', args.uuid)
        result = {'vpn': vpns()}
    elif args.command == 'hotspot':
        result = hotspot()
    elif args.command == 'hotspot-on':
        result = hotspot_on(args.device)
    elif args.command == 'hotspot-off':
        result = hotspot_off()
    elif args.command == 'tailscale':
        result = tailscale()
    elif args.command == 'extras':
        result = {'vpn': vpns(), 'hotspot': hotspot(), 'tailscale': tailscale()}
    elif args.command in ('tailscale-up', 'tailscale-down'):
        result = tailscale_toggle(args.command == 'tailscale-up')
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
