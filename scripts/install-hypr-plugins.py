#!/usr/bin/env python3
"""Install the tested plugin set with hyprpm, using matching Fedora RPM headers."""
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
import bundle  # noqa: E402
from build import PLUGINS, run  # noqa: E402

# The headers' pkg-config file, copied into the hyprpm cache with its prefix pointed there.
HYPRLAND_PC = Path('/usr/share/pkgconfig/hyprland.pc')
# Swapping a loaded plugin crashed Hyprland once (dlclose leaves hyprgrass mapped): only a session without them changes them.
AT_LOGIN = 'The plugins in use come from another build. They are rebuilt at the next login, before they load: log out and back in.'


# JSON from hyprctl or Hyprland, with the command and the start of its output when it is not JSON.
def json_of(*command):
    output = subprocess.check_output(command, text=True)
    try:
        return json.loads(output)
    except ValueError:
        sys.exit(f'{" ".join(command)} did not return JSON: {output.strip()[:200] or "(no output)"}')


def loaded():
    # With nothing loaded, hyprctl answers in words, not JSON.
    output = subprocess.check_output(('hyprctl', '-j', 'plugin', 'list'), text=True)
    try:
        return {plugin['name'] for plugin in json.loads(output)} & set(PLUGINS)
    except (ValueError, TypeError, KeyError):
        return set()


def reset_cache(cache):
    # The cache belongs to one ABI. Only this repository may be lost with it: others would need their own rebuild.
    others = sorted(path.name for path in cache.iterdir() if path.is_dir() and path.name not in ('headersRoot', bundle.REPOSITORY))
    if others:
        sys.exit(f'The hyprpm cache is for another Hyprland and also holds {", ".join(others)}: '
                 f'rebuild those after resetting it with sudo rm -rf {cache}, then run this again.')
    run('sudo', 'rm', '-rf', '--', str(cache))


def main():
    if os.geteuid() == 0:
        sys.exit('Run as a regular user: the script requests sudo only for the hyprpm cache.')
    signature = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if not signature:
        sys.exit('Run this from inside the Hyprland session: HYPRLAND_INSTANCE_SIGNATURE is not set.')
    bundle.verify()
    running = json_of('hyprctl', '-j', 'version')
    installed = json_of('Hyprland', '--version-json')
    for key in ('version', 'commit', 'abiHash'):
        if running.get(key) != installed.get(key):
            sys.exit('The session does not match the installed package: log out and back in first.')
    # COPR reports commit "unknown"; also detect an RPM upgrade during this session.
    instances = json_of('hyprctl', '-j', 'instances')
    instance = next((x for x in instances if x.get('instance') == signature), None)
    if instance is None:
        sys.exit('hyprctl does not list the running Hyprland instance: log out and back in, then retry.')
    if not os.path.samefile('/proc/' + str(instance['pid']) + '/exe', shutil.which('Hyprland')):
        sys.exit('The running compositor uses the old binary: log in again.')
    in_use = loaded()
    if bundle.status() == bundle.CURRENT and in_use == set(PLUGINS):
        print('The plugins are built from this packaging for this Hyprland, and loaded: nothing to do.')
        return
    cache = bundle.CACHE
    headers = cache / 'headersRoot'
    if cache.exists():
        state = cache / 'state.toml'
        if state.exists() and tomllib.loads(state.read_text()).get('state', {}).get('hash') != running['abiHash']:
            if in_use:
                sys.exit(AT_LOGIN)
            reset_cache(cache)
    # Preserve any existing repositories; seed only a missing matching-RPM header cache.
    if not (headers / 'share/pkgconfig/hyprland.pc').exists():
        with tempfile.TemporaryDirectory(prefix='dotfiles-hyprpm-') as staging:
            stage = Path(staging)
            pc = HYPRLAND_PC.read_text()
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
    source = Path.home() / '.local/share/dotfiles/hyprpm' / bundle.digest()
    if not (source / '.git').exists():
        source.mkdir(parents=True, exist_ok=True)
        for name in bundle.FILES:
            shutil.copy2(PACKAGING / name, source / name)
        run('git', 'init', '-q', str(source))
        run('git', '-C', str(source), 'add', *bundle.FILES)
        run('git', '-C', str(source), '-c', 'user.name=Dotfiles packaging', '-c', 'user.email=dotfiles@localhost', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Package tested Hyprland plugins')
    repo_state = cache / bundle.REPOSITORY / 'state.toml'
    if repo_state.exists():
        existing = tomllib.loads(repo_state.read_text())
        # Another packaging, or a build that stopped halfway: replaced whole, while nothing of it is loaded.
        if existing['repository']['url'] != source.as_uri() or any(existing.get(name, {}).get('failed', True) for name in PLUGINS):
            if in_use:
                sys.exit(AT_LOGIN)
            run('hyprpm', 'remove', bundle.REPOSITORY)
    if not repo_state.exists():
        run('hyprpm', 'add', source.as_uri())
    existing = tomllib.loads(repo_state.read_text())
    if any(existing.get(name, {}).get('failed', True) for name in PLUGINS):
        sys.exit('One or more plugins failed to build: check the log before enabling them.')
    for name in PLUGINS:
        run('hyprpm', 'enable', name)
    # Autoload refuses stale COPR builds, even though their Git hash is "unknown".
    stamp = {'rpm': bundle.rpm_version('hyprland'), 'version': running['version'], 'abiHash': running['abiHash']}
    bundle.STAMP.parent.mkdir(parents=True, exist_ok=True)
    bundle.STAMP.write_text(json.dumps(stamp) + '\n')
    run(str(REPO / 'scripts/stow.py'), 'apply')
    run(str(REPO / 'shell/.local/bin/desktop-plugins'), 'reload')
    run('hyprctl', 'reload')
    missing = set(PLUGINS) - loaded()
    if missing:
        sys.exit('Plugins not loaded: ' + ', '.join(sorted(missing)))
    run('hyprctl', 'plugin', 'list')
    errors = subprocess.check_output(['hyprctl', 'configerrors'], text=True).strip()
    if errors:
        sys.exit(errors)
    print('Four plugins installed and loaded; configuration has no errors.')


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
        sys.exit(str(error))
    except KeyError as error:
        sys.exit(f'Unexpected reply from Hyprland or hyprpm: no {error} field.')
