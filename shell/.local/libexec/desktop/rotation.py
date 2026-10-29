#!/usr/bin/env python3
"""Accelerometer orientation from iio-sensor-proxy, and the rotation of the internal display.

probe: one JSON line, {"available"}: whether there is an accelerometer.
watch: one JSON line now and on every change, {"available", "orientation", "transform"}; the accelerometer
is claimed only while this runs, so the shell runs it only in tablet mode.
apply N: rotates the internal display with touch and stylus input (Hyprland transform 0-3) and keeps the
value for config reloads.
"""
from common import write_atomic
from i18n import tr
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-session/rotation.lua'
BUS_NAME = 'net.hadess.SensorProxy'
OBJECT = '/net/hadess/SensorProxy'
# iio-sensor-proxy orientation -> Hyprland transform (90 degree steps, counterclockwise).
TRANSFORMS = {'normal': 0, 'left-up': 1, 'bottom-up': 2, 'right-up': 3}


def emit(available, orientation=''):
    # "undefined" (lying flat) has no transform: the display keeps its rotation.
    print(json.dumps({'available': available, 'orientation': orientation, 'transform': TRANSFORMS.get(orientation)}),
          flush=True)


def sensor():
    import gi
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio, GLib
    try:
        proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SYSTEM, Gio.DBusProxyFlags.NONE, None, BUS_NAME, OBJECT,
                                               BUS_NAME, None)
        available = proxy.get_cached_property('HasAccelerometer')
    except GLib.Error:
        available = None
    return proxy if available is not None and available.unpack() else None


def watch():
    import gi
    from gi.repository import Gio, GLib
    proxy = sensor()
    if proxy is None:
        emit(False)
        return
    loop = GLib.MainLoop()

    def changed(_proxy, properties, _invalidated):
        values = properties.unpack()
        if 'AccelerometerOrientation' in values:
            emit(True, values['AccelerometerOrientation'])

    proxy.connect('g-properties-changed', changed)
    try:
        proxy.call_sync('ClaimAccelerometer', None, Gio.DBusCallFlags.NONE, -1, None)
    except GLib.Error as error:
        # The shell restarts the watcher; without a claim there are no readings to report.
        emit(False)
        raise ValueError(error.message) from error
    current = proxy.get_cached_property('AccelerometerOrientation')
    emit(True, current.unpack() if current else '')
    # The shell stops this process when tablet mode ends; the claim is released before exiting.
    try:
        gi.require_version('GLibUnix', '2.0')
        from gi.repository import GLibUnix
        add_signal = GLibUnix.signal_add
    except (ImportError, ValueError):
        add_signal = GLib.unix_signal_add
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        add_signal(GLib.PRIORITY_DEFAULT, number, loop.quit)
    try:
        loop.run()
    finally:
        try:
            proxy.call_sync('ReleaseAccelerometer', None, Gio.DBusCallFlags.NONE, -1, None)
        except GLib.Error:
            pass


def apply(transform):
    write_atomic(STATE, 'return { transform = %d }\n' % transform)
    # config/tablet.lua defines desktop_rotate, which reapplies the internal monitor with the transform.
    result = subprocess.run(['hyprctl', 'eval', 'if desktop_rotate then desktop_rotate(%d) end' % transform],
                            capture_output=True, text=True, timeout=10)
    if result.returncode != 0 or result.stdout.strip() not in ('', 'ok'):
        raise ValueError(result.stdout.strip() or result.stderr.strip())


def main():
    arguments = sys.argv[1:]
    if arguments == ['probe']:
        print(json.dumps({'available': sensor() is not None}))
    elif arguments == ['watch']:
        watch()
    elif len(arguments) == 2 and arguments[0] == 'apply' and arguments[1] in ('0', '1', '2', '3'):
        apply(int(arguments[1]))
    else:
        raise ValueError(tr('rotation.errors.usage'))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
