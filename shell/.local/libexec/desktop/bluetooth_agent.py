#!/usr/bin/env python3
"""BlueZ Agent1. Only an explicit UI reply grants a pending authorization."""
from i18n import tr
import json
import os
import re
import signal
import sys
from gi.repository import Gio, GLib, GLibUnix

PATH = '/org/angelo/Desktop/BluetoothAgent'
XML = '''<node><interface name="org.bluez.Agent1">
<method name="Release"/><method name="Cancel"/>
<method name="RequestPinCode"><arg type="o" direction="in"/><arg type="s" direction="out"/></method>
<method name="DisplayPinCode"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
<method name="RequestPasskey"><arg type="o" direction="in"/><arg type="u" direction="out"/></method>
<method name="DisplayPasskey"><arg type="o" direction="in"/><arg type="u" direction="in"/><arg type="q" direction="in"/></method>
<method name="RequestConfirmation"><arg type="o" direction="in"/><arg type="u" direction="in"/></method>
<method name="RequestAuthorization"><arg type="o" direction="in"/></method>
<method name="AuthorizeService"><arg type="o" direction="in"/><arg type="s" direction="in"/></method>
</interface></node>'''


def emit(**data):
    try:
        print(json.dumps(data, ensure_ascii=False), flush=True)
    except BrokenPipeError:
        pass


class Agent:
    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.pending = None
        self.timeout = 0
        self.sequence = 0
        self.display_device = None
        self.registered = False
        self.pairing = set()
        self.bus.register_object(PATH, Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0], self.method, None, None)
        self.bus.signal_subscribe('org.bluez', 'org.freedesktop.DBus.Properties', 'PropertiesChanged', None, 'org.bluez.Device1', Gio.DBusSignalFlags.NONE, self.changed)
        self.watch = Gio.bus_watch_name_on_connection(self.bus, 'org.bluez', Gio.BusNameWatcherFlags.NONE, self.appeared, self.vanished)

    def call(self, path, interface, method, args, callback=None):
        self.bus.call('org.bluez', path, interface, method, args, None, Gio.DBusCallFlags.NONE, 120000, None, callback, None)

    def appeared(self, *args):
        self.call('/org/bluez', 'org.bluez.AgentManager1', 'RegisterAgent', GLib.Variant('(os)', (PATH, 'KeyboardDisplay')), self.on_register)

    def on_register(self, bus, result, *_):
        try:
            bus.call_finish(result)
            self.call('/org/bluez', 'org.bluez.AgentManager1', 'RequestDefaultAgent', GLib.Variant('(o)', (PATH,)), self.on_default)
        except GLib.Error as error:
            emit(type='status', registered=False, error=error.message)

    def on_default(self, bus, result, *_):
        try:
            bus.call_finish(result)
            self.registered = True
            emit(type='status', registered=True)
        except GLib.Error as error:
            emit(type='status', registered=False, error=error.message)

    def vanished(self, *args):
        self.registered = False
        self.finish(False)
        self.pairing.clear()
        emit(type='status', registered=False, error=tr('bluetooth.errors.serviceUnavailable'))

    def finish(self, accepted, value='', request_id=None):
        if request_id is not None and (not self.pending or self.pending[0] != request_id):
            return
        pending, self.pending = self.pending, None
        if self.timeout:
            GLib.source_remove(self.timeout)
            self.timeout = 0
        if pending:
            _, method, invocation = pending
            if not accepted:
                invocation.return_dbus_error('org.bluez.Error.Rejected', tr('bluetooth.errors.rejected'))
            elif method == 'RequestPinCode':
                if not isinstance(value, str) or not 1 <= len(value) <= 16 or '\x00' in value:
                    invocation.return_dbus_error('org.bluez.Error.Rejected', tr('bluetooth.errors.invalidPin'))
                else:
                    invocation.return_value(GLib.Variant('(s)', (value,)))
            elif method == 'RequestPasskey':
                if not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,6}', value):
                    invocation.return_dbus_error('org.bluez.Error.Rejected', tr('bluetooth.errors.invalidPasskey'))
                else:
                    invocation.return_value(GLib.Variant('(u)', (int(value),)))
            else:
                invocation.return_value(None)
        self.display_device = None
        emit(type='prompt', prompt=None)

    def expired(self):
        self.timeout = 0
        self.finish(False)
        return GLib.SOURCE_REMOVE

    def method(self, bus, sender, path, interface, method, parameters, invocation):
        # Only the current BlueZ daemon may request authorization.
        try:
            owner = self.bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'GetNameOwner', GLib.Variant('(s)', ('org.bluez',)), GLib.VariantType.new('(s)'), Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
            if sender != owner:
                invocation.return_dbus_error('org.bluez.Error.Rejected', tr('bluetooth.errors.unauthorizedSender'))
                return
        except GLib.Error:
            invocation.return_dbus_error('org.bluez.Error.Rejected', tr('bluetooth.errors.bluezUnavailable'))
            return
        args = parameters.unpack()
        if method in ('Cancel', 'Release'):
            self.finish(False)
            if method == 'Release':
                self.registered = False
                emit(type='status', registered=False, error=tr('bluetooth.errors.agentReleased'))
            invocation.return_value(None)
            return
        if self.pending:
            invocation.return_dbus_error('org.bluez.Error.Rejected', tr('bluetooth.errors.requestPending'))
            return
        self.sequence += 1
        prompt = dict(id=self.sequence, kind=method, device=args[0], value=args[1] if len(args) > 1 else '', entered=args[2] if len(args) > 2 else 0)
        if method in ('DisplayPinCode', 'DisplayPasskey'):
            self.display_device = args[0]
            invocation.return_value(None)
        else:
            self.pending = (self.sequence, method, invocation)
        if self.timeout:
            GLib.source_remove(self.timeout)
        self.timeout = GLib.timeout_add_seconds(120, self.expired)
        emit(type='prompt', prompt=prompt)

    def changed(self, bus, sender, path, interface, signal_name, parameters, *_):
        _, changes, _ = parameters.unpack()
        if path == self.display_device and changes.get('Paired'):
            self.finish(False)

    def command(self, data):
        action = data.get('action')
        if action == 'reply':
            self.finish(data.get('accepted') is True, data.get('value', ''), data.get('id'))
        elif action in ('pair', 'cancel'):
            path = data.get('device', '')
            if not re.fullmatch(r'/org/bluez/hci[0-9]+/dev_(?:[0-9A-Fa-f]{2}_){5}[0-9A-Fa-f]{2}', path):
                raise ValueError(tr('bluetooth.errors.invalidDevice'))
            if action == 'pair':
                if not self.registered:
                    raise ValueError(tr('bluetooth.errors.agentNotReady'))
                if path in self.pairing:
                    return
                self.pairing.add(path)
            method = 'Pair' if action == 'pair' else 'CancelPairing'
            def completed(bus, result, *_):
                self.pairing.discard(path)
                try:
                    bus.call_finish(result)
                    emit(type='operation', device=path, action=action, ok=True)
                except GLib.Error as error:
                    emit(type='operation', device=path, action=action, ok=False, error=error.message)
                if self.display_device == path:
                    self.finish(False)
            self.call(path, 'org.bluez.Device1', method, None, completed)

    def shutdown(self):
        self.finish(False)
        if self.registered:
            try:
                self.bus.call_sync('org.bluez', '/org/bluez', 'org.bluez.AgentManager1', 'UnregisterAgent', GLib.Variant('(o)', (PATH,)), None, Gio.DBusCallFlags.NONE, 2000, None)
            except GLib.Error:
                pass


def main():
    agent = Agent()
    loop = GLib.MainLoop()
    buffer = bytearray()
    def read(channel, condition):
        if condition & (GLib.IO_HUP | GLib.IO_ERR):
            loop.quit()
            return False
        chunk = os.read(sys.stdin.fileno(), 65536)
        if not chunk:
            loop.quit()
            return False
        buffer.extend(chunk)
        while b'\n' in buffer:
            line, _, rest = buffer.partition(b'\n')
            buffer[:] = rest
            try:
                agent.command(json.loads(line))
            except (ValueError, TypeError, KeyError) as error:
                emit(type='error', error=str(error))
        return True
    GLib.io_add_watch(sys.stdin, GLib.PRIORITY_DEFAULT, GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR, read)
    for sig in (signal.SIGINT, signal.SIGTERM):
        GLibUnix.signal_add(GLib.PRIORITY_DEFAULT, sig, lambda: (loop.quit(), False)[1])
    try:
        loop.run()
    finally:
        agent.shutdown()


if __name__ == '__main__':
    main()
