#!/usr/bin/env python3
"""Operations started from Settings that run in the background, each under a name (services/Job.qml).

jobs.py run NAME [--root] [--title TEXT] -- COMMAND...
    Run COMMAND, as the desktop user; with --root, behind one pkexec prompt (privileged.py), so its sudo calls run
    as root. One at a time per NAME (a lock). Its state is in ~/.local/state/desktop-shell/jobs/NAME.json, its output
    in NAME.log, and a notification titled TEXT gives the result.
jobs.py status NAME
    That state as JSON, with the end of the log.
"""
from common import last_lines, lock_held, read_json, write_atomic
from i18n import tr
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

JOBS = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-shell/jobs'
HERE = Path(__file__).resolve().parent
NAME = re.compile(r'[a-z0-9][a-z0-9-]{0,63}')
LOG_LINES = 80


def paths(name):
    if not NAME.fullmatch(name):
        raise ValueError(tr('jobs.errors.name', [name]))
    return JOBS / f'{name}.json', JOBS / f'{name}.log', JOBS / f'.{name}.lock'


def run(name, command, root=False, title=''):
    state, log, lock = paths(name)
    JOBS.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(tr('jobs.errors.running'), file=sys.stderr)
            return 1
        started = int(time.time())
        write_atomic(state, json.dumps({'running': True, 'started': started, 'title': title, 'root': root}) + '\n')
        if root:
            command = [sys.executable, str(HERE / 'privileged.py'), 'run', *command]
        with log.open('w', encoding='utf-8') as output:
            try:
                status = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT).returncode
            except OSError as error:
                output.write(f'{command[0]}: {error.strerror}\n')
                status = 127
        write_atomic(state, json.dumps({'running': False, 'started': started, 'finished': int(time.time()), 'status': status,
                                        'title': title, 'root': root}) + '\n')
    if title:
        lines = last_lines(log, 5)
        body = tr('jobs.done') if status == 0 else tr('jobs.failed', [lines[-1] if lines else str(status)])
        subprocess.run(['notify-send', '--app-name=' + title, '--app-icon=' + ('emblem-ok-symbolic' if status == 0 else 'dialog-error'),
                        title, body], check=False)
    return status


def status(name):
    state, log, lock = paths(name)
    value = read_json(state)
    if value.get('running') and not (lock.exists() and lock_held(lock)):
        value = {**value, 'running': False, 'status': -1}  # Stopped without writing its result.
    return {**value, 'log': last_lines(log, LOG_LINES)}


def main(arguments):
    if len(arguments) == 2 and arguments[0] == 'status':
        print(json.dumps(status(arguments[1]), ensure_ascii=False))
        return 0
    if len(arguments) >= 4 and arguments[0] == 'run' and '--' in arguments:
        split = arguments.index('--')
        name, options, command = arguments[1], arguments[2:split], arguments[split + 1:]
        root = '--root' in options
        title = options[options.index('--title') + 1] if '--title' in options[:-1] else ''
        if command and not set(options) - {'--root', '--title', title}:
            return run(name, command, root, title)
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
