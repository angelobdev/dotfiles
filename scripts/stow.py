#!/usr/bin/env python3
"""Manage the explicit GNU Stow packages; back up conflicting leaf files on apply."""
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import os
import shutil
import subprocess
import sys

PACKAGES = ('hypr', 'quickshell', 'shell', 'hypridle', 'hyprlock', 'hyprpaper', 'gtk', 'kitty', 'fastfetch', 'portals', 'udiskie', 'electron')
ROOT = Path(__file__).resolve().parents[1]
parser = ArgumentParser(description=__doc__)
parser.add_argument('action', choices=('dry-run', 'apply', 'remove'))
parser.add_argument('--target', type=Path, default=Path.home(), help='Stow target (default: home)')
args = parser.parse_args()
target = args.target.expanduser().absolute()
if not target.is_dir():
    parser.error(f'Target directory does not exist: {target}')
if not shutil.which('stow'):
    parser.error('Install GNU Stow first: sudo dnf install stow')

command = ['stow', '--dir', str(ROOT), '--target', str(target), '--no-folding', '--verbose', r'--ignore=__pycache__|\.py[co]$']
if args.action == 'remove':
    sys.exit(subprocess.call(command + ['--delete', *PACKAGES]))

conflicts = []
for package in PACKAGES:
    package_root = ROOT / package
    for source in sorted(package_root.rglob('*')):
        if source.is_dir() or '__pycache__' in source.parts or source.suffix in ('.pyc', '.pyo'):
            continue
        destination = target / source.relative_to(package_root)
        # Refuse redirects/collisions in parent directories before changing anything.
        parent = destination.parent
        while parent != target:
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                parser.error(f'Parent must be a real directory: {parent}')
            parent = parent.parent
        if destination.is_symlink() and destination.resolve() == source.resolve():
            continue
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink():
                parser.error(f'Refusing to replace a directory: {destination}')
            conflicts.append(destination)

if args.action == 'dry-run':
    for path in conflicts:
        print(f'Will back up on apply: {path}', flush=True)
    sys.exit(subprocess.call(command + ['--simulate', '--stow', *PACKAGES]))

backup = None
moved = []
try:
    if conflicts:
        state = Path(os.environ.get('XDG_STATE_HOME', str(target / '.local/state')))
        backup = state / 'dotfiles/backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        for path in conflicts:
            saved = backup / path.relative_to(target)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(saved))
            moved.append((path, saved))
        print(f'Backup: {backup}', flush=True)
    # Check the entire transaction before creating any links.
    subprocess.run(command + ['--simulate', '--stow', *PACKAGES], check=True)
    subprocess.run(command + ['--stow', *PACKAGES], check=True)
except (OSError, subprocess.CalledProcessError):
    for original, saved in reversed(moved):
        # Never overwrite a new file that appeared while Stow was running.
        if not original.exists() and not original.is_symlink():
            shutil.move(str(saved), str(original))
    raise
