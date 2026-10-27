#!/usr/bin/env python3
"""Steam HiDPI startup and opt-in gamescope sessions for individual games."""
import argparse
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def hypr_json(*args):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return None
    try:
        result = subprocess.run(['hyprctl', '-j', *args], check=True,
                                capture_output=True, text=True, timeout=2)
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def focused_monitor():
    monitors = hypr_json('monitors')
    if not isinstance(monitors, list):
        return None
    active = [m for m in monitors if isinstance(m, dict) and not m.get('disabled')]
    return next((m for m in active if m.get('focused')), active[0] if active else None)


def scale_value(value):
    try:
        scale = float(value)
    except (TypeError, ValueError):
        raise ValueError('Steam scale must be a number between 1 and 4.') from None
    if not math.isfinite(scale) or not 1 <= scale <= 4:
        raise ValueError('Steam scale must be a number between 1 and 4.')
    return f'{scale:.3f}'.rstrip('0').rstrip('.')


@functools.cache
def steam_settings():
    config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'desktop/steam.json'
    try:
        settings = json.loads(config.read_text())
    except FileNotFoundError:
        settings = {}
    except (OSError, ValueError) as error:
        raise ValueError(f'Cannot read Steam settings from {config}: {error}') from error
    if not isinstance(settings, dict) or not isinstance(settings.get('monitorScales', {}), dict):
        raise ValueError('Steam settings must contain a monitorScales object.')
    return settings


def steam_monitor_scale(monitor):
    return steam_settings().get('monitorScales', {}).get(monitor.get('name'), monitor.get('scale', 1))


def prepare_steam_renderer(scale):
    if not steam_settings().get('rendererScaling', False):
        return
    helpers = Path(__file__).resolve().parent
    source = helpers / 'steam-scale.c'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
    cache = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home() / '.cache'))) / 'desktop/steam-ui'
    library = cache / f'scale-{digest}.so'
    cache.mkdir(parents=True, exist_ok=True)
    if not library.is_file():
        compiler = shutil.which('cc')
        if not compiler:
            raise ValueError('Steam renderer scaling needs a C compiler: sudo dnf install gcc')
        with tempfile.TemporaryDirectory(prefix='build-', dir=cache) as build:
            output = Path(build) / 'scale.so'
            result = subprocess.run([compiler, '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                                     '-O2', '-Wl,-z,relro,-z,now', '-o', str(output), str(source), '-ldl'],
                                    capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise ValueError(f'Cannot build Steam UI scaling library: {result.stderr.strip()}')
            output.replace(library)
    wrapper = helpers / 'steamrt-ui'
    configured = os.environ.get('STEAM_RUNTIME_STEAMRT')
    if configured and Path(configured).resolve() != wrapper.resolve():
        runtime = Path(configured)
    else:
        runtime = Path(os.environ.get('DESKTOP_STEAM_REAL_RUNTIME',
                       str(Path.home() / '.steam/root/steamrt64/pv-runtime/steam-runtime-steamrt')))
    if not (runtime / '_v2-entry-point').is_file():
        raise ValueError('Steam UI runtime not found. Start /usr/bin/steam once to complete its installation.')
    os.environ.update(STEAM_RUNTIME_STEAMRT=str(wrapper), DESKTOP_STEAM_REAL_RUNTIME=str(runtime),
                      DESKTOP_STEAM_CEF_LIBRARY=str(library), DESKTOP_STEAM_CEF_SCALE=scale)


def steam_command(arguments):
    # Explicit Steam arguments and the caller's environment take precedence.
    if any(a == '-forcedesktopscaling' or a.startswith('-forcedesktopscaling=')
           for a in arguments):
        return ['/usr/bin/steam', *arguments]
    override = os.environ.get('DESKTOP_STEAM_SCALE') or os.environ.get('STEAM_FORCE_DESKTOPUI_SCALING')
    if override:
        scale = scale_value(override)
    else:
        option = hypr_json('getoption', 'xwayland:force_zero_scaling')
        monitor = focused_monitor()
        if not isinstance(option, dict) or not monitor:
            return ['/usr/bin/steam', *arguments]
        # Scaling both the X11 surface and Steam's UI would enlarge it twice.
        scale = scale_value(steam_monitor_scale(monitor)
                            if option.get('bool', option.get('int')) in (True, 1) else 1)
    return ['/usr/bin/steam', '-forcedesktopscaling', scale, *arguments]


def resolution(value):
    match = re.fullmatch(r'([1-9][0-9]*)[xX]([1-9][0-9]*)', value)
    if not match or any(not 1 <= int(v) <= 16384 for v in match.groups()):
        raise argparse.ArgumentTypeError('Use WIDTHxHEIGHT with dimensions from 1 to 16384.')
    return tuple(int(v) for v in match.groups())


def positive_fps(value):
    try:
        fps = int(value)
    except ValueError:
        fps = 0
    if not 1 <= fps <= 1000:
        raise argparse.ArgumentTypeError('FPS must be an integer from 1 to 1000.')
    return fps


def gamescope_command(arguments):
    parser = argparse.ArgumentParser(prog='desktop-gamescope',
        description='Run one game in gamescope on Wayland. Separate the game command with --.')
    parser.add_argument('--render', type=resolution, metavar='WIDTHxHEIGHT',
                        help='Internal game resolution (default: output resolution).')
    parser.add_argument('--output', type=resolution, metavar='WIDTHxHEIGHT',
                        help='Output resolution (default: focused Hyprland monitor in physical pixels).')
    parser.add_argument('--fps', type=positive_fps, help='Optional frame-rate limit; unlimited by default.')
    parser.add_argument('--fsr', action='store_true', help='Use FSR 1 upscaling for a lower render resolution.')
    parser.add_argument('--windowed', action='store_true', help='Open a window instead of fullscreen.')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(arguments)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('A game command is required after --.')
    if not os.environ.get('WAYLAND_DISPLAY'):
        parser.error('Start this wrapper inside a Wayland session.')
    output = args.output
    if output is None:
        monitor = focused_monitor()
        if not monitor:
            parser.error('Cannot detect a monitor. Specify --output WIDTHxHEIGHT.')
        try:
            output = resolution(f"{monitor['width']}x{monitor['height']}")
            if int(monitor.get('transform', 0)) % 2:
                output = output[::-1]
        except (KeyError, TypeError, ValueError, argparse.ArgumentTypeError):
            parser.error('Invalid monitor dimensions. Specify --output WIDTHxHEIGHT.')
    render = args.render or output
    result = ['gamescope', '--backend', 'wayland', '-W', str(output[0]), '-H', str(output[1]),
              '-w', str(render[0]), '-h', str(render[1])]
    if not args.windowed:
        result.append('-f')
    if args.fps:
        result.extend(['-r', str(args.fps)])
    if args.fsr:
        result.extend(['-F', 'fsr'])
    return [*result, '--', *command]


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('steam', 'gamescope'):
        raise ValueError('Expected steam or gamescope mode.')
    if sys.argv[1] == 'steam':
        command = steam_command(sys.argv[2:])
        # Keep legacy client controls and the opt-in CEF workaround aligned.
        for index, argument in enumerate(command):
            if argument == '-forcedesktopscaling':
                if index + 1 == len(command):
                    raise ValueError('-forcedesktopscaling requires a scale value.')
                value = command[index + 1]
            elif argument.startswith('-forcedesktopscaling='):
                value = argument.split('=', 1)[1]
            else:
                continue
            scale = scale_value(value)
            os.environ['STEAM_FORCE_DESKTOPUI_SCALING'] = scale
            prepare_steam_renderer(scale)
            break
    else:
        command = gamescope_command(sys.argv[2:])
    if not shutil.which(command[0]):
        raise ValueError(f'{command[0]} is not installed.')
    os.execvp(command[0], command)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        print(f'desktop-gaming: {error}', file=sys.stderr)
        sys.exit(1)
