#!/usr/bin/env python3
"""Match XWayland clients to the monitor scale: X resources for text and cursor, integer scaling for Aseprite."""
from common import focused_monitor, write_atomic
from i18n import tr
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

CURSOR_SIZE = 24
# Aseprite's usual 200% on an unscaled monitor; DESKTOP_ASEPRITE_SCALE overrides it.
ASEPRITE_BASE = 2
ASEPRITE_INI = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'aseprite' / 'aseprite.ini'


def target():
    monitor = focused_monitor()
    if not monitor:
        raise ValueError(tr('xwayland.errors.noMonitor'))
    return monitor.get('name', ''), float(monitor.get('scale', 1))


def cursor_theme():
    result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'cursor-theme'],
        capture_output=True, text=True, timeout=5)
    theme = result.stdout.strip().strip("'") if result.returncode == 0 else ''
    if theme and theme != 'default':
        return theme
    # X clients did not resolve "default" through its index.theme here, so name the inherited theme.
    for base in (Path.home() / '.icons', Path.home() / '.local/share/icons', Path('/usr/share/icons')):
        index = base / 'default' / 'index.theme'
        if index.is_file():
            for line in index.read_text(encoding='utf-8', errors='replace').splitlines():
                if line.startswith('Inherits='):
                    return line.split('=', 1)[1].split(',')[0].strip() or 'Adwaita'
    return 'Adwaita'


def aseprite_scale(monitor_scale):
    try:
        base = float(os.environ.get('DESKTOP_ASEPRITE_SCALE', ASEPRITE_BASE))
    except ValueError:
        raise ValueError(tr('xwayland.errors.asepriteScale')) from None
    # X11 draws in physical pixels here, so 200% on a 1.667 panel means about 3.3 device pixels per UI pixel;
    # Aseprite only takes whole numbers, and the nearest keeps it crisp (1.667 -> 3, 1 -> 2).
    return max(1, int(base * monitor_scale + 0.5))


def apply():
    name, scale = target()
    # Under force_zero_scaling X clients draw in physical pixels, so DPI and cursor size carry the scale.
    resources = {'Xft.dpi': round(96 * scale), 'Xcursor.theme': cursor_theme(), 'Xcursor.size': round(CURSOR_SIZE * scale)}
    data = ''.join(f'{key}: {value}\n' for key, value in resources.items())
    subprocess.run(['xrdb', '-merge'], input=data, text=True, check=True, timeout=10)
    result = {'monitor': name, 'scale': scale, **resources}
    # Keep Aseprite in step too, so it fits however it is started (a running Aseprite rewrites its
    # own value when it quits, and the next apply or desktop-aseprite launch corrects it).
    if ASEPRITE_INI.is_file():
        result['asepriteScale'] = prepare_aseprite(scale)
    return result


def status():
    result = subprocess.run(['xrdb', '-query'], capture_output=True, text=True, timeout=10)
    current = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition(':')
        if key in ('Xft.dpi', 'Xcursor.theme', 'Xcursor.size'):
            current[key] = value.strip()
    name, scale = target()
    return {'focusedMonitor': name, 'focusedScale': scale, 'resources': current}


def set_ini_value(path, section, key, value, overwrite=True):
    lines = path.read_text(encoding='utf-8').splitlines() if path.is_file() else []
    current, done, out = '', False, []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('['):
            if current == section and not done:
                out.append(f'{key} = {value}')
                done = True
            current = stripped[1:-1]
        elif current == section and stripped.split('=', 1)[0].strip() == key:
            if not overwrite:
                return
            if not done:
                out.append(f'{key} = {value}')
                done = True
            continue
        out.append(line)
    if not done:
        out += ([] if current == section else [f'[{section}]']) + [f'{key} = {value}']
    write_atomic(path, '\n'.join(out) + '\n')


def prepare_aseprite(monitor_scale):
    scale = aseprite_scale(monitor_scale)
    set_ini_value(ASEPRITE_INI, 'general', 'screen_scale', scale)
    # Aseprite's own cursor is multiplied by screen_scale (huge at 3); the native one is the X theme cursor,
    # already sized by Xcursor.size. Only set when absent, so a choice made in Preferences is kept.
    set_ini_value(ASEPRITE_INI, 'cursor', 'use_native_cursor', 'true', overwrite=False)
    return scale


def aseprite(command):
    if not command:
        raise ValueError(tr('xwayland.errors.asepriteUsage'))
    prepare_aseprite(target()[1])
    environment = dict(os.environ)
    # A session-wide XCURSOR_SIZE would override the X resource set by apply.
    environment.pop('XCURSOR_SIZE', None)
    os.execvpe(command[0], command, environment)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('apply')
    commands.add_parser('status')
    launcher = commands.add_parser('aseprite', description='Use as the Steam launch option: desktop-aseprite %%command%%')
    launcher.add_argument('program', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command == 'aseprite':
        aseprite(args.program)
    print(json.dumps(apply() if args.command == 'apply' else status(), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
