#!/usr/bin/env python3
"""Per-user migrations: one-shot scripts in the repository's migrations/ folder for state that Stow links cannot reach.

run: run the pending ones in order, as the user (at login, from desktop-session, and after a pull of the repository).
pending: list them as JSON.
mark-all: record every migration as done, for a new install, whose files are already in their new form.

A migration is migrations/YYYYMMDDhhmm-name.sh or .py. It runs once: exit 0 records it in
~/.local/state/dotfiles/migrations; exit 75 means "not yet" (something it needs is missing), which stops the queue
without an error and tries again next time; any other exit stops the queue, says so in a notification, and tries
again next time. Its output goes to ~/.local/state/dotfiles/migrations.log; its last line is what a notification says.
DOTFILES_REPO names the repository in its environment.
"""
from common import write_atomic
from i18n import tr
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

# The clone this helper is linked from (Stow links every file, so the path resolves into it).
REPO = Path(__file__).resolve().parents[4]
FOLDER = REPO / 'migrations'
STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'dotfiles/migrations'
LOG = STATE.with_name('migrations.log')
NAME = re.compile(r'^\d{12}-[a-z0-9][a-z0-9-]*\.(sh|py)$')
# EX_TEMPFAIL: what the migration needs is not there yet.
DEFER = 75
TIMEOUT = 600


def migrations(folder=None):
    folder = folder or FOLDER
    try:
        return sorted(path.name for path in folder.iterdir() if path.is_file() and NAME.match(path.name))
    except OSError:
        return []


def pending(folder=None, state=None):
    state = state or STATE
    return [name for name in migrations(folder) if not (state / name).exists()]


def mark(name, state=None):
    state = state or STATE
    state.mkdir(parents=True, exist_ok=True)
    write_atomic(state / name, time.strftime('%Y-%m-%dT%H:%M:%S%z') + '\n')


def notify(body):
    subprocess.run(['notify-send', '--app-name=' + tr('migrations.title'), '--app-icon=system-software-update',
                    tr('migrations.title'), body], check=False)


def last_line(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ''


def run(folder=None, state=None, log=None):
    """0 when nothing failed (done, or waiting), 1 when one failed; either way the rest waits for the next run."""
    folder, state, log = folder or FOLDER, state or STATE, log or LOG
    state.mkdir(parents=True, exist_ok=True)
    # Login and a pull can start one at the same time: one runs, the other waits for it and finds nothing left.
    with (state.parent / '.migrations.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for name in pending(folder, state):
            path = folder / name
            command = ['bash', str(path)] if name.endswith('.sh') else [sys.executable, str(path)]
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT, cwd=Path.home(),
                                        env={**os.environ, 'DOTFILES_REPO': str(REPO)})
                code, output = result.returncode, result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                code, output = 1, tr('migrations.timeout', [TIMEOUT])
            with log.open('a', encoding='utf-8') as handle:
                handle.write(f'== {name} ({code}) {time.strftime("%Y-%m-%d %H:%M:%S")}\n{output}')
            if code == 0:
                mark(name, state)
                continue
            if code == DEFER:
                notify(tr('migrations.waiting', [name, last_line(output) or name]))
                return 0
            notify(tr('migrations.failed', [name, last_line(output) or str(code)]))
            return 1
    return 0


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments == ['run']:
        return run()
    if arguments == ['pending']:
        print(json.dumps(pending(), ensure_ascii=False))
        return 0
    if arguments == ['mark-all']:
        for name in pending():
            mark(name)
        return 0
    print(tr('migrations.errors.usage'), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except OSError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
