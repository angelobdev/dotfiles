#!/usr/bin/env python3
"""Run one operation from Settings with root behind a single pkexec prompt: privileged.py run COMMAND...

pkexec starts the root broker (scripts/privileged/root-broker, installed by the installer's files step), which asks
once through the shell's polkit agent. COMMAND then runs as the desktop user with the sudo shim (root/sudo) first in
PATH, so every sudo it or its children call (the installer, makepkg, hyprpm) runs in the broker. When COMMAND ends,
the broker's standard input closes and it exits. COMMAND's output goes to this process's, and its status is ours.
"""
from i18n import tr
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile

BROKER = Path('/usr/local/libexec/dotfiles-desktop/root-broker')
SHIM = Path(__file__).resolve().parent / 'root'
# pkexec: 126 when the prompt is dismissed, 127 when the user may not authenticate.
CANCELLED = 126
DENIED = 127


def installed():
    # pkexec must run a file only root can change: the installer's copy, not the repository's.
    try:
        info = BROKER.stat()
    except OSError:
        return False
    return info.st_uid == 0 and not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH) and bool(info.st_mode & stat.S_IXUSR)


def start_broker(socket_path):
    broker = subprocess.Popen(['pkexec', str(BROKER), str(socket_path)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              text=True)
    if broker.stdout.readline().strip() == 'ready':
        return broker
    status = broker.wait()
    if status == CANCELLED:
        sys.exit(tr('privileged.errors.cancelled'))
    if status == DENIED:
        sys.exit(tr('privileged.errors.denied'))
    sys.exit(tr('privileged.errors.failed', [str(status)]))


def run(command):
    if not installed():
        sys.exit(tr('privileged.errors.missing', [str(BROKER)]))
    runtime = os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}'
    directory = Path(tempfile.mkdtemp(prefix='desktop-root.', dir=runtime))
    broker = None
    try:
        socket_path = directory / 'socket'
        broker = start_broker(socket_path)
        env = {**os.environ, 'PATH': f'{SHIM}:{os.environ.get("PATH", "/usr/bin")}', 'DESKTOP_ROOT_SOCKET': str(socket_path)}
        child = subprocess.Popen(command, env=env)
        # Stopping the operation stops the command, and with it the broker.
        for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(number, lambda signum, _frame: child.send_signal(signum))
        return child.wait()
    finally:
        if broker is not None:
            broker.stdin.close()
            try:
                broker.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass  # Root: this process cannot kill it, and it exits on its own once its commands end.
        shutil.rmtree(directory, ignore_errors=True)


def main(arguments):
    if arguments[:1] != ['run'] or len(arguments) < 2:
        sys.exit(__doc__.splitlines()[0])
    command = arguments[2:] if arguments[1] == '--' else arguments[1:]
    if not command:
        sys.exit(__doc__.splitlines()[0])
    status = run(command)
    return status if status >= 0 else 128 - status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
