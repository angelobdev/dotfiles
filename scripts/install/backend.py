"""What every distribution module of install-desktop.py shares: the cache of the package manager's answers, sudo,
and root-owned files. Each module keeps thin wrappers of its own (query, sudo, write_file, ...), so what it calls
at run time is its own name, which the tests replace."""
import os
from pathlib import Path
import subprocess
import tempfile


class Answers:
    """The package manager's answers, kept while nothing changes once the installer turns them on: planning an
    uninstall asks the same questions from several steps, each a solver run of seconds. Any change forgets them."""

    def __init__(self, cached):
        # The commands whose answers are kept (the package manager's own); any other always runs.
        self.cached = tuple(cached)
        self.kept = None

    def remember(self):
        self.kept = {}

    def forget(self):
        if self.kept is not None:
            self.kept.clear()

    def query(self, command, run):
        if self.kept is None or command[0] not in self.cached:
            return run(command)
        if command not in self.kept:
            self.kept[command] = run(command)
        return self.kept[command]

    def remembered(self, key, compute):
        # A parsed answer (a log, every installed package), kept the same way.
        if self.kept is None:
            return compute()
        if key not in self.kept:
            self.kept[key] = compute()
        return self.kept[key]


def run_query(command):
    return subprocess.run(command, capture_output=True, text=True, env={**os.environ, 'LC_ALL': 'C'})


def sudo(command, forget):
    # The answers from before are stale once something changed, and so are those asked while it ran.
    forget()
    try:
        subprocess.run(('sudo', *command), check=True)
    finally:
        forget()


def file_differs(path, content):
    try:
        return Path(path).read_text(encoding='utf-8') != content
    except OSError:
        return True


def write_file(path, content, mode, sudo):
    # Through a temporary file and install(1), so the file is root's, with its mode, in one step.
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', prefix='desktop-install-') as temporary:
        temporary.write(content)
        temporary.flush()
        sudo('install', '-D', '-o', 'root', '-g', 'root', '-m', mode, temporary.name, str(path))
