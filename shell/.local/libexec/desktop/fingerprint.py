#!/usr/bin/env python3
"""Fingerprints of the user through fprintd, for Settings → Privacy.

list: the reader and the enrolled fingers, as JSON ({"device": "" without a reader or fprintd}).
enroll FINGER: enroll one, printing a JSON line per touch ({"result", "done", "stage", "stages"}); a line "cancel" on
stdin stops it. fprintd asks for the user's own password first (polkit, net.reactivated.fprint.device.enroll).
delete FINGER: remove one.
FINGER is fprintd's name: left-thumb, right-index-finger, …
"""
from i18n import tr
import getpass
import json
import sys
import threading

FINGERS = tuple(f'{side}-{finger}' for side in ('left', 'right')
                for finger in ('thumb', 'index-finger', 'middle-finger', 'ring-finger', 'little-finger'))
BUS = 'net.reactivated.Fprint'
MANAGER = '/net/reactivated/Fprint/Manager'
DEVICE = 'net.reactivated.Fprint.Device'
# Long enough for a slow user, short enough that a forgotten dialog lets the reader go.
ENROLL_TIMEOUT = 180


def gio():
    from gi.repository import Gio, GLib
    return Gio, GLib


def bus():
    Gio, _ = gio()
    return Gio.bus_get_sync(Gio.BusType.SYSTEM, None)


def call(connection, path, interface, method, signature=None, arguments=(), timeout=10000):
    Gio, GLib = gio()
    parameters = GLib.Variant(signature, tuple(arguments)) if signature else None
    return connection.call_sync(BUS, path, interface, method, parameters, None, Gio.DBusCallFlags.NONE, timeout, None).unpack()


def device(connection):
    """The default reader's object path, '' without one (no reader, or no fprintd)."""
    _, GLib = gio()
    try:
        return call(connection, MANAGER, 'net.reactivated.Fprint.Manager', 'GetDefaultDevice')[0]
    except GLib.Error:
        return ''


def prop(connection, path, name):
    return call(connection, path, 'org.freedesktop.DBus.Properties', 'Get', '(ss)', (DEVICE, name))[0]


def listing():
    # Without PyGObject (a system that never installed the desktop's helpers) there is no reader to talk to either.
    try:
        _, GLib = gio()
    except ImportError:
        return {'device': '', 'fingers': [], 'stages': 0}
    try:
        connection = bus()
    except GLib.Error:
        return {'device': '', 'fingers': [], 'stages': 0}
    path = device(connection)
    if not path:
        return {'device': '', 'fingers': [], 'stages': 0}
    try:
        fingers = call(connection, path, DEVICE, 'ListEnrolledFingers', '(s)', (getpass.getuser(),))[0]
    except GLib.Error:
        # NoEnrolledPrints is an error in fprintd's API.
        fingers = []
    return {'device': prop(connection, path, 'name'), 'fingers': [finger for finger in fingers if finger in FINGERS],
            'stages': prop(connection, path, 'num-enroll-stages')}


def message(error):
    # fprintd's errors name what went wrong (net.reactivated.Fprint.Error.PermissionDenied: …).
    text = str(error)
    if 'PermissionDenied' in text or 'NotAuthorized' in text:
        return tr('fingerprint.errors.denied')
    if 'AlreadyInUse' in text:
        return tr('fingerprint.errors.busy')
    return tr('fingerprint.errors.failed', [text.split(': ', 1)[-1][:200]])


def emit(value):
    print(json.dumps(value), flush=True)


def enroll(finger):
    Gio, GLib = gio()
    connection = bus()
    path = device(connection)
    if not path:
        raise ValueError(tr('fingerprint.errors.noReader'))
    stages = prop(connection, path, 'num-enroll-stages')
    loop = GLib.MainLoop()
    state = {'stage': 0, 'status': 1}

    def on_status(_connection, _sender, _path, _interface, _signal, parameters):
        result, done = parameters.unpack()
        if result == 'enroll-stage-passed':
            state['stage'] += 1
        emit({'result': result, 'done': done, 'stage': state['stage'], 'stages': stages})
        if done:
            state['status'] = 0 if result == 'enroll-completed' else 1
            loop.quit()

    subscription = connection.signal_subscribe(BUS, DEVICE, 'EnrollStatus', path, None, Gio.DBusSignalFlags.NONE, on_status)
    # The dialog's Cancel: a line on stdin, read beside the loop.
    def watch_stdin():
        for line in sys.stdin:
            if line.strip() == 'cancel':
                GLib.idle_add(loop.quit)
                return
    threading.Thread(target=watch_stdin, daemon=True).start()
    GLib.timeout_add_seconds(ENROLL_TIMEOUT, loop.quit)
    claimed = False
    try:
        call(connection, path, DEVICE, 'Claim', '(s)', (getpass.getuser(),))
        claimed = True
        # The polkit prompt comes here and waits for the user: no short timeout.
        call(connection, path, DEVICE, 'EnrollStart', '(s)', (finger,), timeout=ENROLL_TIMEOUT * 1000)
        emit({'result': 'enroll-started', 'done': False, 'stage': 0, 'stages': stages})
        loop.run()
    except GLib.Error as error:
        emit({'result': 'error', 'done': True, 'stage': state['stage'], 'stages': stages, 'error': message(error)})
        return 1
    finally:
        connection.signal_unsubscribe(subscription)
        for method in ('EnrollStop', 'Release') if claimed else ():
            try:
                call(connection, path, DEVICE, method)
            except GLib.Error:
                pass
    return state['status']


def delete(finger):
    _, GLib = gio()
    connection = bus()
    path = device(connection)
    if not path:
        raise ValueError(tr('fingerprint.errors.noReader'))
    try:
        call(connection, path, DEVICE, 'Claim', '(s)', (getpass.getuser(),))
        try:
            call(connection, path, DEVICE, 'DeleteEnrolledFinger', '(s)', (finger,), timeout=120000)
        finally:
            call(connection, path, DEVICE, 'Release')
    except GLib.Error as error:
        raise ValueError(message(error)) from None
    return listing()


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments == ['list']:
        print(json.dumps(listing()))
        return 0
    if len(arguments) == 2 and arguments[0] in ('enroll', 'delete') and arguments[1] in FINGERS:
        if arguments[0] == 'enroll':
            return enroll(arguments[1])
        print(json.dumps(delete(arguments[1])))
        return 0
    print(tr('fingerprint.errors.usage'), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
