"""The install steps, in order (STEPS): each one says what is still to do (pending), does it (apply) and first notes
in the record what it is about to change (remember)."""
from collections import namedtuple
import functools
import getpass
import hashlib
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request

import install_paths
import bundle  # noqa: E402  (after install_paths, which puts scripts/hyprpm on the path)
import install_plan
import install_record


# remember(plan, items, record) notes in the record what apply is about to change, and what was there before.
Step = namedtuple('Step', 'title pending apply remember', defaults=(None,))


def repos_pending(plan):
    return [name for name in install_plan.merged(plan, 'repos') if plan.distro.repo_missing(plan.table['repos'][name])]


# What the repositories still to add need first (the manifest's needs, dnf5-plugins for a copr): in the preview
# and the record like any package, instead of installed quietly by the repos step.
def repo_tools_pending(plan):
    needed = [tool for name in repos_pending(plan) for tool in plan.table['repos'][name].get('needs', ())]
    return plan.distro.missing(list(dict.fromkeys(needed))) if needed else []


def repo_tools_apply(plan, tools):
    plan.distro.install(tools)


def repos_apply(plan, names):
    for name in names:
        plan.distro.add_repo(plan.table['repos'][name], plan.release)


def upgrade_pending(plan):
    return ['installed packages'] if plan.distro.upgrades_pending() else []


def upgrade_apply(plan, items):
    plan.distro.upgrade()


def swaps(plan):
    return [tuple(pair) for pair in install_plan.merged(plan, 'swaps')]


def wanted_packages(plan):
    # A swapped package is replaced, never installed: its replacement takes its place.
    old = {pair[0] for pair in swaps(plan)}
    return [package for package in install_plan.merged(plan, 'packages') + [pair[1] for pair in swaps(plan)] if package not in old]


def swaps_pending(plan):
    return [f'{old} -> {new}' for old, new in swaps(plan) if plan.distro.installed(old)]


def swaps_apply(plan, items):
    for old, new in swaps(plan):
        if f'{old} -> {new}' in items:
            plan.distro.swap(old, new)


def packages_pending(plan):
    missing = plan.distro.missing(list(dict.fromkeys(wanted_packages(plan))))
    compositor_guard(plan, missing)
    return missing


def compositor_guard(plan, missing):
    # The plugins accept only the Hyprland builds they were verified against, and dnf or pacman installs the newest
    # one the repository has: say so before installing, not at the first login. Once the repositories are there, so
    # the build is the one that will come (apply adds them before this step).
    wanted = [name for name in ('hyprland', 'hyprland-devel') if name in missing]
    if 'plugins' not in plan.profiles or not wanted or repos_pending(plan):
        return
    for name, build in sorted(plan.distro.candidates(wanted).items()):
        if build not in bundle.VERIFIED:
            print(f'Warning: {name} {build} is newer than the build the plugins were verified against '
                  f'({", ".join(bundle.VERIFIED)}): they will not be built at the first login until it is verified.')


def packages_apply(plan, packages):
    plan.distro.install(packages, install_plan.merged(plan, 'exclude'))


def files_pending(plan):
    return [item['path'] for item in install_plan.merged(plan, 'files') if plan.distro.file_differs(item['path'], item['content'].lstrip())]


def files_apply(plan, paths):
    for item in install_plan.merged(plan, 'files'):
        if item['path'] in paths:
            plan.distro.write_file(item['path'], item['content'].lstrip(), item.get('mode', '0644'))


def groups_pending(plan):
    return [group for group in install_plan.merged(plan, 'groups') if not install_plan.member(getpass.getuser(), group)]


def groups_apply(plan, groups):
    for group in groups:
        plan.distro.sudo('usermod', '-aG', group, getpass.getuser())


def login_shell():
    return pwd.getpwnam(getpass.getuser()).pw_shell


def shell_pending(plan):
    shell = install_plan.setting(plan, 'login_shell')
    return [shell] if shell and login_shell() != shell else []


def shell_apply(plan, shells):
    # usermod, not chsh: chsh is not on every edition, and it asks for the password again.
    plan.distro.sudo('usermod', '--shell', shells[0], getpass.getuser())


def clone_path(item):
    return Path.home() / item['path']


def clone_head(path):
    result = install_plan.query('git', '-C', str(path), 'rev-parse', 'HEAD')
    return result.stdout.strip() if result.returncode == 0 else ''


def clone_clean(path):
    result = install_plan.query('git', '-C', str(path), 'status', '--porcelain')
    return result.returncode == 0 and not result.stdout.strip()


# A folder the user has there already is updated only when it is a clone without local changes: never a plain
# folder or edited files (apply checks out with --force).
def clone_ours(path):
    return not path.exists() or path.is_dir() and not any(path.iterdir()) or (path / '.git').exists() and clone_clean(path)


def clones_pending(plan):
    return [item['path'] for item in install_plan.merged(plan, 'clones')
            if clone_head(clone_path(item)) != item['commit'] and clone_ours(clone_path(item))]


def clones_kept(plan):
    return [item['path'] for item in install_plan.merged(plan, 'clones')
            if clone_head(clone_path(item)) != item['commit'] and not clone_ours(clone_path(item))]


def checkout(path, repo, commit):
    # Only that commit, fetched into path (a clone, or a new one).
    if not (path / '.git').exists():
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(('git', '-C', str(path), 'init', '-q'), check=True)
    subprocess.run(('git', '-C', str(path), 'fetch', '-q', '--depth', '1', repo, commit), check=True)
    subprocess.run(('git', '-C', str(path), '-c', 'advice.detachedHead=false', 'checkout', '-q', '--force', commit), check=True)


def clones_apply(plan, paths):
    # As the desktop user, into the home: pinned commits of what the distribution does not package.
    for item in install_plan.merged(plan, 'clones'):
        if item['path'] in paths:
            checkout(clone_path(item), item['repo'], item['commit'])


# Release archives: a tarball pinned by version and sha256 per architecture, unpacked into the home as the user, for
# programs that ship that way and then update themselves (herdr). Only one still missing installs: an update the
# program made itself is never taken back.
ARCHES = {'x86_64': 'x86_64', 'amd64': 'x86_64', 'aarch64': 'aarch64', 'arm64': 'aarch64'}


def machine():
    return ARCHES.get(platform.machine().lower(), '')


def archive_label(item):
    return f'{item["name"]} {item["version"]}'


def archive_paths(item):
    # What apply puts in the home: the unpacked files and folders, the links, the written files.
    return list(item['unpack'].values()) + list(item.get('links', {})) + list(item.get('entries', {}))


def archive_missing(item):
    return not any((Path.home() / path).exists() for path in item['unpack'].values())


def archives_pending(plan):
    return [archive_label(item) for item in install_plan.merged(plan, 'archives') if machine() in item['sha256'] and archive_missing(item)]


def archives_unsupported(plan):
    return [item['name'] for item in install_plan.merged(plan, 'archives') if machine() not in item['sha256']]


def open_url(url, timeout):
    # With a name of its own: releases.herdr.dev refuses urllib's default User-Agent (403).
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'install-desktop.py (dotfiles)'}), timeout=timeout)


def archive_url(item):
    return item['url'].format(version=item['version'], arch=machine())


def unpack_archive(item):
    home = Path.home()
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        tarball = folder / 'archive.tar.gz'
        with open_url(archive_url(item), 60) as response, tarball.open('wb') as out:
            shutil.copyfileobj(response, out)
        if sha256(tarball) != item['sha256'][machine()]:
            sys.exit(f'{archive_label(item)}: the download does not match its sha256 in the manifest.')
        with tarfile.open(tarball) as archive:
            archive.extractall(folder / 'unpacked', filter='data')
        for member, path in item['unpack'].items():
            # Next to its place first, then renamed into it: never half a program where it runs from.
            target = home / path
            staged = target.with_name(target.name + '.new')
            target.parent.mkdir(parents=True, exist_ok=True)
            if staged.is_dir():
                shutil.rmtree(staged)
            staged.unlink(missing_ok=True)
            shutil.move(folder / 'unpacked' / member, staged)
            staged.replace(target)
    # A link or file already there (a program of the same name, a launcher entry of its own) stays.
    for link, target in item.get('links', {}).items():
        path = home / link
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.unlink(missing_ok=True)
            path.symlink_to(home / target)
    for path, content in item.get('entries', {}).items():
        target = home / path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content.lstrip().replace('{home}', str(home)), encoding='utf-8')


def archives_apply(plan, items):
    for item in install_plan.merged(plan, 'archives'):
        if archive_label(item) in items:
            unpack_archive(item)


def aur_cache():
    return Path.home() / '.cache/dotfiles/aur'


def aur_path(item):
    return aur_cache() / item['package']


def aur_pending(plan):
    # Missing, or another version than the pinned one: updating is a new pin (pins --update), then apply.
    items = []
    for item in install_plan.merged(plan, 'aur'):
        now = plan.distro.version(item['package'])
        if now != item['version']:
            items.append(f'{item["package"]} {now} -> {item["version"]}' if now else f'{item["package"]} {item["version"]}')
    return items


def srcinfo_version(text):
    # The version a PKGBUILD builds, from its .SRCINFO, as pacman prints it: [EPOCH:]PKGVER-PKGREL.
    fields = {}
    for line in text.splitlines():
        key, separator, value = line.strip().partition(' = ')
        if separator and key in ('epoch', 'pkgver', 'pkgrel'):
            fields.setdefault(key, value)
    version = f'{fields.get("pkgver", "")}-{fields.get("pkgrel", "")}'
    return f'{fields["epoch"]}:{version}' if fields.get('epoch') else version


def import_key(url):
    # Which key may sign the sources is the PKGBUILD's validpgpkeys: this only gives makepkg's gpg a copy of it.
    with urllib.request.urlopen(url, timeout=60) as response:
        key = response.read()
    subprocess.run(('gpg', '--batch', '--quiet', '--import'), input=key, check=True)


def aur_apply(plan, items):
    # As the desktop user: makepkg refuses root, and asks sudo for pacman itself.
    names = {item.split()[0] for item in items}
    for item in install_plan.merged(plan, 'aur'):
        if item['package'] not in names:
            continue
        path = aur_path(item)
        checkout(path, install_paths.AUR + item['package'] + '.git', item['commit'])
        built = srcinfo_version((path / '.SRCINFO').read_text(encoding='utf-8'))
        if built != item['version']:
            raise RuntimeError(f'{item["package"]} at {item["commit"][:12]} builds {built}, '
                               f'not the {item["version"]} the manifest names: correct the manifest.')
        if item.get('key'):
            import_key(item['key'])
        plan.distro.build_package(path)
        # The PKGBUILD stays, for the next update; the sources and the built package go.
        subprocess.run(('git', '-C', str(path), 'clean', '-q', '-d', '-x', '--force'), check=True)


def dmi(field):
    try:
        return Path('/sys/class/dmi/id', field).read_text(encoding='utf-8').strip()
    except OSError:
        return ''


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as file:
        for block in iter(lambda: file.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def firmware_needed(plan):
    # Only for the model each blob belongs to, and only where it is missing or different.
    return [item for item in install_plan.merged(plan, 'firmware') if dmi('product_name') == item['product']
            and not (Path(item['target']).is_file() and sha256(item['target']) == item['sha256'])]


def firmware_source(plan, item):
    # By hash, not by name: the vendor package names it differently from the kernel.
    if not plan.firmware:
        return None
    return found_firmware(str(Path(plan.firmware).expanduser()), item['size'], item['sha256'])


# Searched once per run (preflight, pending and apply each ask, the guided installer more often): the directory
# can be a whole backup disk. The guided installer forgets it at each new check.
@functools.lru_cache(maxsize=None)
def found_firmware(directory, size, digest):
    # The size check first: only files that can match get hashed.
    for path in sorted(Path(directory).rglob('*')):
        if path.is_file() and path.stat().st_size == size and sha256(path) == digest:
            return path
    return None


def firmware_pending(plan):
    return [item['target'] for item in firmware_needed(plan) if firmware_source(plan, item)]


def firmware_apply(plan, targets):
    for item in firmware_needed(plan):
        if item['target'] in targets:
            plan.distro.install_firmware(firmware_source(plan, item), item['target'])
    # The ISH loader runs from the initramfs, before the root file system: every kernel needs it there.
    plan.distro.rebuild_initramfs()


def services_pending(plan):
    enable = [unit for unit in install_plan.merged(plan, 'services') if install_plan.unit_state(unit) not in ('enabled', 'static', 'alias')]
    disable = [unit for unit in install_plan.merged(plan, 'disable') if install_plan.unit_state(unit) == 'enabled']
    # For every user: a Workstation preset turns these on, and an edition without a desktop leaves them off.
    users = [unit for unit in install_plan.merged(plan, 'user_services') if install_plan.query('systemctl', '--global', 'is-enabled', unit).stdout.strip() != 'enabled']
    return ['enable ' + unit for unit in enable] + ['disable ' + unit for unit in disable] + ['enable --global ' + unit for unit in users]


def services_apply(plan, items):
    # Never --now: stopping sshd or the network here could cut the session running this script.
    for item in items:
        plan.distro.sudo('systemctl', *item.split())


def firewall_pending(plan):
    zone = install_plan.setting(plan, 'firewall_zone')
    if not zone or not install_plan.booted() or not shutil.which('firewall-cmd'):
        return []
    return [] if install_plan.query('firewall-cmd', '--get-default-zone').stdout.strip() == zone else [zone]


def firewall_apply(plan, zones):
    plan.distro.sudo('firewall-cmd', '--set-default-zone=' + zones[0])


def auth_pending(plan):
    # The authselect items the units ask for: with-fingerprint (hardware.fingerprint, tablet), the tablet profile (tablet).
    wanted = install_plan.merged(plan, 'auth')
    return plan.distro.auth_pending(wanted) if wanted else []


def auth_apply(plan, items):
    plan.distro.auth_apply(items, install_paths.REPO / 'scripts/tablet-auth.sh')


def stow_command(plan, action):
    extra = [argument for name in install_plan.merged(plan, 'stow') for argument in ('--with', name)]
    return (str(install_paths.REPO / 'scripts/stow.py'), action, *extra)


def stow_pending(plan):
    if not shutil.which('stow'):
        return ['every package: GNU Stow is not installed yet']
    result = install_plan.query(*stow_command(plan, 'dry-run'))
    if result.returncode:
        raise RuntimeError('stow.py dry-run failed: ' + (result.stderr or result.stdout).strip()[-300:])
    lines = (result.stdout + result.stderr).splitlines()
    return [line for line in lines if line.startswith(('LINK:', 'MKDIR:', 'Will back up'))]


def stow_apply(plan, items):
    # Never with sudo: the links belong to the desktop user.
    subprocess.run(stow_command(plan, 'apply'), check=True)


def flatpak_pending(plan):
    apps = install_plan.merged(plan, 'flatpaks')
    if not apps or not install_plan.booted():
        return []
    present = install_plan.query('flatpak', 'list', '--app', '--columns=application').stdout.split() if shutil.which('flatpak') else []
    return [app for app in apps if app not in present]


def flatpak_apply(plan, apps):
    plan.distro.sudo('flatpak', 'remote-add', '--if-not-exists', 'flathub', install_paths.FLATHUB)
    plan.distro.sudo('flatpak', 'install', '-y', '--noninteractive', 'flathub', *apps)


def plugin_guard():
    # Early warning: post would refuse this Hyprland build, after a reboot.
    try:
        bundle.verify()
    except RuntimeError as error:
        print(f'Warning: {error}')


def verify_pending(plan):
    if 'plugins' in plan.profiles and not plan.distro.missing(list(dict.fromkeys(['hyprland', bundle.headers_package()]))):
        plugin_guard()
    return ['command not found: ' + command for command in plan.commands if not shutil.which(command)]


def verify_apply(plan, problems):
    raise RuntimeError('The desktop is incomplete, so the system keeps booting to the console.')


def boot_pending(plan):
    items = []
    if install_plan.booted() and install_paths.SESSION not in install_plan.session():
        items.append(install_paths.BOOT_SESSION)
    if install_plan.unit_state('gdm.service') != 'enabled':
        items.append(install_paths.BOOT_GDM)
    if install_plan.query('systemctl', 'get-default').stdout.strip() != 'graphical.target':
        items.append(install_paths.BOOT_TARGET)
    if 'plugins' in plan.profiles and not install_paths.STAMP.exists() and not install_paths.AUTOSTART.exists():
        items.append(install_paths.BOOT_AUTOSTART)
    return items


# One Exec= argument, by the Desktop Entry rules: plain ones as they are; others quoted, with ", `, $ and \ escaped
# by a backslash that the string escaping doubles again, and % doubled (it starts a field code).
def exec_argument(text):
    if re.fullmatch(r'[A-Za-z0-9_./,:=+-]+', text):
        return text
    # The quoting rule first, then the string escaping, which doubles every backslash.
    quoted = ''.join('\\' + char if char in '"`$\\' else char for char in text).replace('\\', '\\\\')
    return '"' + quoted.replace('%', '%%') + '"'


def autostart_entry(plan):
    profiles = ','.join(plan.profiles)
    command = ['kitty', '--hold', str(install_paths.REPO / 'scripts/install-desktop.py'), 'post', '--profiles', profiles]
    return ('[Desktop Entry]\nType=Application\nName=Finish the desktop installation\n'
            f'Exec={" ".join(exec_argument(part) for part in command)}\n')


def boot_apply(plan, items):
    if install_paths.BOOT_SESSION in items:
        plan.distro.sudo('busctl', 'call', install_paths.ACCOUNTS, install_plan.user_object(), install_paths.ACCOUNTS + '.User', 'SetSession', 's', install_paths.SESSION)
    if install_paths.BOOT_GDM in items:
        plan.distro.sudo('systemctl', 'enable', 'gdm.service')
    if install_paths.BOOT_TARGET in items:
        plan.distro.sudo('systemctl', 'set-default', 'graphical.target')
    if install_paths.BOOT_AUTOSTART in items:
        install_paths.AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
        install_paths.AUTOSTART.write_text(autostart_entry(plan), encoding='utf-8')


def repos_remember(plan, items, record):
    install_record.keep(record, 'repos', items)


def repo_tools_remember(plan, items, record):
    install_record.keep(record, 'packages', items)


def swaps_remember(plan, items, record):
    install_record.keep(record, 'swaps', [[old, new] for old, new in swaps(plan) if f'{old} -> {new}' in items])


def packages_remember(plan, items, record):
    install_record.keep(record, 'packages', items)


def text_digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def files_remember(plan, items, record):
    # What apply is about to write, by digest: a later manifest change must not make it look edited by hand.
    written = record.setdefault('written', {})
    for item in install_plan.merged(plan, 'files'):
        if item['path'] in items:
            written[item['path']] = text_digest(item['content'].lstrip())
    files = record.setdefault('files', {})
    for path in items:
        if path not in files:
            try:
                files[path] = install_record.read_or_none(path)
            except OSError:
                pass  # There but unreadable: uninstall leaves it alone.


def firmware_remember(plan, items, record):
    firmware = record.setdefault('firmware', {})
    for target in items:
        firmware.setdefault(target, Path(target).exists())


def groups_remember(plan, items, record):
    install_record.keep(record, 'groups', items)


def shell_remember(plan, items, record):
    record.setdefault('login_shell', login_shell())


def services_remember(plan, items, record):
    services = record.setdefault('services', {})
    for item in items:
        words = item.split()
        install_record.keep(services, 'global' if '--global' in words else words[0] + 'd', [words[-1]])


def firewall_remember(plan, items, record):
    record.setdefault('firewall_zone', install_record.default_zone_now())


def auth_remember(plan, items, record):
    install_record.keep(record, 'auth', items)


def stow_remember(plan, items, record):
    install_record.keep(record, 'stow', install_plan.merged(plan, 'stow'))


def clones_remember(plan, items, record):
    # Only folders apply creates are undone; one that was there before stays the user's.
    install_record.keep(record, 'clones', [path for path in items if not (Path.home() / path).exists()])


def archives_remember(plan, items, record):
    # Only what apply creates; uninstall leaves what was there before.
    install_record.keep(record, 'archives', [path for item in install_plan.merged(plan, 'archives') if archive_label(item) in items
                              for path in archive_paths(item) if not os.path.lexists(Path.home() / path)])


def aur_remember(plan, items, record):
    # With the other packages: uninstall removes them alike. One installed before, which apply updates, stays.
    install_record.keep(record, 'packages', [name for name in (item.split()[0] for item in items) if not plan.distro.installed(name)])


def flatpak_remember(plan, items, record):
    install_record.keep(record, 'flatpaks', items)


def boot_remember(plan, items, record):
    boot = record.setdefault('boot', {})
    if install_paths.BOOT_SESSION in items:
        boot.setdefault('session', install_record.current_session())
    if install_paths.BOOT_GDM in items:
        boot.setdefault('gdm', install_plan.unit_state('gdm.service') or 'disabled')
    if install_paths.BOOT_TARGET in items:
        boot.setdefault('target', install_record.default_target())


# In order. boot stays last: a run that stops earlier leaves a system that still starts on the console.
STEPS = (
    Step('repo tools', repo_tools_pending, repo_tools_apply, repo_tools_remember),
    Step('repos', repos_pending, repos_apply, repos_remember),
    Step('upgrade', upgrade_pending, upgrade_apply),
    # Before packages: a package that needs the replacement would conflict with what it replaces.
    Step('swaps', swaps_pending, swaps_apply, swaps_remember),
    Step('packages', packages_pending, packages_apply, packages_remember),
    # After the packages: makepkg needs base-devel and git.
    Step('aur', aur_pending, aur_apply, aur_remember),
    Step('files', files_pending, files_apply, files_remember),
    Step('firmware', firmware_pending, firmware_apply, firmware_remember),
    Step('groups', groups_pending, groups_apply, groups_remember),
    Step('shell', shell_pending, shell_apply, shell_remember),
    Step('services', services_pending, services_apply, services_remember),
    Step('firewall', firewall_pending, firewall_apply, firewall_remember),
    Step('auth', auth_pending, auth_apply, auth_remember),
    Step('stow', stow_pending, stow_apply, stow_remember),
    Step('clones', clones_pending, clones_apply, clones_remember),
    Step('archives', archives_pending, archives_apply, archives_remember),
    Step('flatpak', flatpak_pending, flatpak_apply, flatpak_remember),
    Step('verify', verify_pending, verify_apply),
    Step('boot', boot_pending, boot_apply, boot_remember),
)
