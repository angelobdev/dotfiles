"""Snapshots of the root around a system update (the utils.snapshots part): snapper, only when / is btrfs. A pre
snapshot before the upgrade step of an update, a post one after, numbered, at most KEEP kept (snapper-cleanup.timer).
The root config is made at the first update that needs one. On Arch snap-pac takes the same pair for every pacman
transaction, so these are left to it. The way back is snapper undochange PRE..POST (docs/guide/installation.md)."""
from pathlib import Path
import shutil
import subprocess

import install_plan

DESCRIPTION = 'desktop update'
KEEP = 5
CONFIG = Path('/etc/snapper/configs/root')
# A hook of snap-pac: pacman takes the snapshots itself.
SNAP_PAC = Path('/usr/share/libalpm/hooks/05-snap-pac-pre.hook')


def available():
    return shutil.which('snapper') is not None and install_plan.query('findmnt', '-no', 'FSTYPE', '/').stdout.strip() == 'btrfs'


def ensure_config():
    if CONFIG.exists():
        return
    print('Snapshots: a snapper config for / (numbered, at most %d kept, no timeline).' % KEEP, flush=True)
    subprocess.run(('sudo', 'snapper', '-c', 'root', 'create-config', '/'), check=True)
    subprocess.run(('sudo', 'snapper', '-c', 'root', 'set-config', 'TIMELINE_CREATE=no', f'NUMBER_LIMIT={KEEP}',
                    f'NUMBER_LIMIT_IMPORTANT={KEEP}'), check=True)


def before():
    """The number of the pre snapshot, or '' when none was taken (no snapper, no btrfs, snap-pac, or a failure,
    which never stops the update)."""
    if not available():
        return ''
    try:
        ensure_config()
        if SNAP_PAC.exists():
            return ''
        result = subprocess.run(('sudo', 'snapper', '-c', 'root', 'create', '--type', 'pre', '--print-number',
                                 '--cleanup-algorithm', 'number', '--description', DESCRIPTION),
                                capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        print(f'Snapshots: none taken ({error}).', flush=True)
        return ''
    number = result.stdout.strip()
    if result.returncode != 0 or not number.isdigit():
        print('Snapshots: none taken (' + (result.stderr.strip() or 'snapper failed') + ').', flush=True)
        return ''
    print(f'Snapshots: #{number} before the update.', flush=True)
    return number


def after(number):
    if not number:
        return
    result = subprocess.run(('sudo', 'snapper', '-c', 'root', 'create', '--type', 'post', '--pre-number', number, '--print-number',
                             '--cleanup-algorithm', 'number', '--description', DESCRIPTION), capture_output=True, text=True, check=False)
    if result.returncode == 0:
        post = result.stdout.strip()
        print(f'Snapshots: #{post} after it; to undo the update: sudo snapper -c root undochange {number}..{post}, then restart.', flush=True)
