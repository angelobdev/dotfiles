#!/usr/bin/env python3
"""Install the tested plugin set with hyprpm, using matching Fedora RPM headers."""
import getpass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

REPO = Path(__file__).resolve().parent.parent
PACKAGING = REPO / 'scripts/hyprpm'
sys.dont_write_bytecode = True
sys.path.insert(0, str(PACKAGING))
from build import PLUGINS, fingerprint, rpm_version


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    if os.geteuid() == 0:
        sys.exit('Run as a regular user: the script requests sudo only for the hyprpm cache.')
    fingerprint()  # Refuse unreviewed compositor builds and mismatched headers.
    running = json.loads(subprocess.check_output(['hyprctl', '-j', 'version'], text=True))
    installed = json.loads(subprocess.check_output(['Hyprland', '--version-json'], text=True))
    for key in ('version', 'commit', 'abiHash'):
        if running.get(key) != installed.get(key):
            sys.exit('The session does not match the installed package: log out and back in first.')
    # COPR reports commit "unknown"; also detect an RPM upgrade during this session.
    instances = json.loads(subprocess.check_output(['hyprctl', '-j', 'instances'], text=True))
    instance = next(x for x in instances if x['instance'] == os.environ['HYPRLAND_INSTANCE_SIGNATURE'])
    if not os.path.samefile('/proc/' + str(instance['pid']) + '/exe', shutil.which('Hyprland')):
        sys.exit('The running compositor uses the old binary: log in again.')
    cache = Path('/var/cache/hyprpm') / getpass.getuser()
    headers = cache / 'headersRoot'
    if cache.exists():
        state = cache / 'state.toml'
        if state.exists() and tomllib.loads(state.read_text()).get('state', {}).get('hash') != running['abiHash']:
            sys.exit('The hyprpm cache uses a different ABI: verify/rebuild existing plugins first.')
    # Preserve any existing repositories; seed only a missing matching-RPM header cache.
    if not (headers / 'share/pkgconfig/hyprland.pc').exists():
        with tempfile.TemporaryDirectory(prefix='dotfiles-hyprpm-') as staging:
            stage = Path(staging)
            pc = Path('/usr/share/pkgconfig/hyprland.pc').read_text()
            if 'prefix=/usr/include' not in pc:
                sys.exit('The pkg-config layout differs from the verified layout.')
            (stage / 'hyprland.pc').write_text(pc.replace('prefix=/usr/include', 'prefix=' + str(headers / 'include')))
            run('sudo', 'install', '-d', '-m755', str(headers / 'include'), str(headers / 'share/pkgconfig'))
            run('sudo', 'cp', '-a', '/usr/include/hyprland', str(headers / 'include'))
            run('sudo', 'install', '-m644', str(stage / 'hyprland.pc'), str(headers / 'share/pkgconfig/hyprland.pc'))
    if not (cache / 'state.toml').exists():
        with tempfile.TemporaryDirectory(prefix='dotfiles-hyprpm-state-') as staging:
            state_file = Path(staging) / 'state.toml'
            state_file.write_text('[state]\nhash = ' + json.dumps(running['abiHash']) + '\ndont_warn_install = false\n')
            run('sudo', 'install', '-m644', str(state_file), str(cache / 'state.toml'))
    # A local packaging repository keeps upstream pins and the Lua compatibility
    # patch reproducible. hyprpm still builds, installs, enables and loads each plugin.
    digest = hashlib.sha256(b''.join((PACKAGING / f).read_bytes() for f in ('build.py', 'hyprpm.toml'))).hexdigest()[:16]
    bundle = Path.home() / '.local/share/dotfiles/hyprpm' / digest
    if not (bundle / '.git').exists():
        bundle.mkdir(parents=True, exist_ok=True)
        for name in ('build.py', 'hyprpm.toml'):
            shutil.copy2(PACKAGING / name, bundle / name)
        run('git', 'init', '-q', str(bundle))
        run('git', '-C', str(bundle), 'add', 'build.py', 'hyprpm.toml')
        run('git', '-C', str(bundle), '-c', 'user.name=Dotfiles packaging', '-c', 'user.email=dotfiles@localhost', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Package tested Hyprland plugins')
    repo_state = cache / 'dotfiles-desktop/state.toml'
    if repo_state.exists():
        existing = tomllib.loads(repo_state.read_text())
        if existing['repository']['url'] != bundle.as_uri():
            sys.exit('Packaging has changed. Run hyprpm remove dotfiles-desktop and rerun this script.')
        if any(existing.get(name, {}).get('failed', True) for name in PLUGINS):
            sys.exit('The previous build is incomplete. Run hyprpm remove dotfiles-desktop and rerun this script.')
    else:
        run('hyprpm', 'add', bundle.as_uri())
    existing = tomllib.loads(repo_state.read_text())
    if any(existing.get(name, {}).get('failed', True) for name in PLUGINS):
        sys.exit('One or more plugins failed to build: check the log before enabling them.')
    for name in PLUGINS:
        run('hyprpm', 'enable', name)
    # Autoload refuses stale COPR builds, even though their Git hash is "unknown".
    stamp = {'rpm': rpm_version('hyprland'), 'version': running['version'], 'abiHash': running['abiHash']}
    stamp_dir = Path.home() / '.local/state/dotfiles'
    stamp_dir.mkdir(parents=True, exist_ok=True)
    (stamp_dir / 'hypr-plugins.json').write_text(json.dumps(stamp) + '\n')
    run(str(REPO / 'scripts/stow.py'), 'apply')
    run(str(REPO / 'shell/.local/bin/desktop-plugins'), 'reload')
    run('hyprctl', 'reload')
    loaded = json.loads(subprocess.check_output(['hyprctl', '-j', 'plugin', 'list'], text=True))
    missing = set(PLUGINS) - {plugin['name'] for plugin in loaded}
    if missing:
        sys.exit('Plugins not loaded: ' + ', '.join(sorted(missing)))
    run('hyprctl', 'plugin', 'list')
    errors = subprocess.check_output(['hyprctl', 'configerrors'], text=True).strip()
    if errors:
        sys.exit(errors)
    print('Five plugins installed and loaded; configuration has no errors.')


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError, OSError, KeyError, StopIteration) as error:
        sys.exit(str(error))
