"""Uninstall: the install steps backwards (UNSTEPS), from the record, each undoing only what is still the way apply
left it; and the record rebuilt from the package history for an install made before records."""
import ast
import getpass
import os
from pathlib import Path
import shutil
import subprocess

import install_paths
import bundle  # noqa: E402  (after install_paths, which puts scripts/hyprpm on the path)
import install_plan
import install_record
import install_steps


def desktop_present():
    # Installed before: Stow links into this repository, or plugins already built.
    return bool(linked_files()) or install_paths.STAMP.exists()


def every_profile(plan):
    return plan._replace(profiles=install_plan.units(plan.table))


def reconstruct(plan):
    # No record: an install made before there was one. Only what the manifest names and the package history shows
    # arrived after the system was installed; values from before that the system cannot tell are left alone.
    every = every_profile(plan)
    distro = plan.distro
    base = distro.base_packages(distro.history())
    # Without the transactions that installed the system, nobody can tell its packages from the desktop's: they stay.
    swapped = [[old, new] for old, new in install_steps.swaps(every) if distro.installed(new) and not distro.installed(old)
               and any(name.rsplit('.', 1)[0] == old for name in base)]
    news = {new for _, new in swapped}
    aur = [item['package'] for item in install_plan.merged(every, 'aur')]
    wanted = [package for package in dict.fromkeys(install_steps.wanted_packages(every) + aur) if package not in news]
    packages = [name for name in distro.installed_names(wanted) if name not in base] if base else []
    record = {'reconstructed': True, 'packages': packages, 'swaps': swapped,
              'repos': [name for name in install_plan.merged(every, 'repos') if not distro.repo_missing(every.table['repos'][name])],
              'files': {item['path']: None for item in install_plan.merged(every, 'files')
                        if not distro.file_differs(item['path'], item['content'].lstrip()) and not distro.owned(item['path'])},
              'firmware': {item['target']: False for item in install_plan.merged(every, 'firmware') if Path(item['target']).is_file()
                           and install_steps.sha256(item['target']) == item['sha256'] and not distro.owned(item['target'])},
              'groups': [group for group in install_plan.merged(every, 'groups') if install_plan.member(getpass.getuser(), group)],
              'clones': [item['path'] for item in install_plan.merged(every, 'clones') if (install_steps.clone_path(item) / '.git').exists()],
              'stow': install_plan.merged(every, 'stow'), 'auth': distro.auth_reconstruct(packages)}
    shell = install_plan.setting(every, 'login_shell')
    if shell and install_steps.login_shell() == shell:
        record['login_shell'] = '/bin/bash'
    zone = install_plan.setting(every, 'firewall_zone')
    if zone and install_plan.booted() and shutil.which('firewall-cmd') and install_record.default_zone_now() == zone != distro.default_zone():
        record['firewall_zone'] = distro.default_zone()
    if not base:
        record['base_unknown'] = True
    boot = record['boot'] = {}
    if install_plan.booted() and install_record.current_session() == install_paths.SESSION:
        boot['session'] = ''
    # The display manager came with the desktop: the system started on the console before it.
    if any(name.rsplit('.', 1)[0] == 'gdm' for name in packages):
        boot['gdm'] = 'disabled'
        if install_record.default_target() == 'graphical.target' != distro.BASE_TARGET:
            boot['target'] = distro.BASE_TARGET
    return record


def uninstall_plan(plan, preview=True):
    record = install_record.load_record(set_aside=not preview)
    return plan._replace(record=record if install_record.knows_changes(record) else reconstruct(plan))


def hyprland_running():
    return install_plan.query('pgrep', '-u', str(os.getuid()), '-x', 'Hyprland').returncode == 0


def plugin_paths():
    home = Path.home()
    return [home / '.local/share/dotfiles/hyprpm', home / '.cache/dotfiles/hyprpm-build', home / '.local/bin/hyprcapture-ui',
            home / '.local/share/licenses/hyprcapture', bundle.STAMP]


def unplugins_pending(plan):
    repository = bundle.CACHE / bundle.REPOSITORY
    return ([str(repository)] if repository.exists() else []) + [str(path) for path in plugin_paths() if path.exists() or path.is_symlink()]


def unplugins_apply(plan, items):
    # Files only: no Hyprland runs, so nothing is unloaded. The cache goes whole unless it holds other repositories.
    if str(bundle.CACHE / bundle.REPOSITORY) in items:
        others = [path for path in bundle.CACHE.iterdir() if path.is_dir() and path.name not in ('headersRoot', bundle.REPOSITORY)]
        plan.distro.sudo('rm', '-rf', '--', str(bundle.CACHE / bundle.REPOSITORY) if others else str(bundle.CACHE))
    for path in plugin_paths():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif path.exists() or path.is_symlink():
            path.unlink()


UNBOOT_AUTOSTART = 'remove the first-login autostart'


def unboot_pending(plan):
    boot, items = plan.record.get('boot', {}), []
    # Only what is still the way apply left it: a session or target chosen since then stays.
    if 'session' in boot and install_plan.booted() and install_record.current_session() == install_paths.SESSION != boot['session']:
        items.append('default session ' + (boot['session'] or 'chosen by GDM'))
    if boot.get('gdm', 'enabled') != 'enabled' and install_plan.unit_state('gdm.service') == 'enabled':
        items.append('disable gdm.service')
    if 'target' in boot and install_record.default_target() == 'graphical.target' != boot['target']:
        items.append('boot into ' + boot['target'])
    if install_paths.AUTOSTART.exists():
        items.append(UNBOOT_AUTOSTART)
    return items


def unboot_apply(plan, items):
    boot = plan.record.get('boot', {})
    if any(item.startswith('default session ') for item in items):
        plan.distro.sudo('busctl', 'call', install_paths.ACCOUNTS, install_plan.user_object(), install_paths.ACCOUNTS + '.User', 'SetSession', 's', boot['session'])
    if 'disable gdm.service' in items:
        plan.distro.sudo('systemctl', 'disable', 'gdm.service')
    if any(item.startswith('boot into ') for item in items):
        plan.distro.sudo('systemctl', 'set-default', boot['target'])
    if UNBOOT_AUTOSTART in items:
        install_paths.AUTOSTART.unlink(missing_ok=True)


# A recorded clone is removed only while it is what apply left: a folder the manifest names, at its commit, with no
# local changes. The record is a file in the home, so a path from it is never trusted on its own.
def clones_undoable(plan):
    named = {item['path']: item for item in install_plan.merged(every_profile(plan), 'clones')}
    undoable, changed = [], []
    for path in plan.record.get('clones', ()):
        item = named.get(path)
        if not item or not (Path.home() / path).exists():
            continue
        target = install_steps.clone_path(item)
        (undoable if install_steps.clone_head(target) == item['commit'] and install_steps.clone_clean(target) else changed).append(path)
    return undoable, changed


def unclones_pending(plan):
    return clones_undoable(plan)[0]


def unclones_apply(plan, paths):
    for path in paths:
        shutil.rmtree(Path.home() / path)


def unarchives_pending(plan):
    # What apply unpacked, as it is now: these programs update themselves, so a newer version goes too.
    return [path for path in plan.record.get('archives', ()) if os.path.lexists(Path.home() / path)]


def unarchives_apply(plan, paths):
    for path in paths:
        target = Path.home() / path
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)


def unaur_pending(plan):
    # The PKGBUILDs; the packages built from them go with the others.
    return [str(install_steps.aur_cache())] if install_steps.aur_cache().exists() else []


def unaur_apply(plan, items):
    shutil.rmtree(install_steps.aur_cache())


def stow_packages():
    # The lists of stow.py, read without running it.
    values = {}
    for node in ast.parse((install_paths.REPO / 'scripts/stow.py').read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') in ('PACKAGES', 'OPTIONAL'):
            values[node.targets[0].id] = ast.literal_eval(node.value)
    return values['PACKAGES'] + values['OPTIONAL']


def linked_files():
    links = []
    for package in stow_packages():
        root = install_paths.REPO / package
        for source in sorted(root.rglob('*')):
            target = Path.home() / source.relative_to(root)
            if source.is_file() and target.is_symlink() and target.resolve() == source.resolve():
                links.append(target)
    return links


def backups():
    # Files Stow moved aside, newest backup first: the latest copy of a file wins.
    root = install_paths.STATE / 'backups'
    return [(folder, path) for folder in sorted(root.iterdir(), reverse=True) if folder.is_dir()
            for path in sorted(folder.rglob('*')) if path.is_file() or path.is_symlink()] if root.is_dir() else []


def unstow_pending(plan):
    items = []
    links = linked_files()
    if links:
        items.append(f'unlink {len(links)} files linked into {install_paths.REPO}')
    # Put back where nothing is, or where a link of ours is that the unlinking removes first; the newest copy of
    # each file counts once.
    linked = set(links)
    restorable = {Path.home() / path.relative_to(folder) for folder, path in backups()}
    restorable = [target for target in restorable if target in linked or not (target.exists() or target.is_symlink())]
    if restorable:
        items.append(f'put back {len(restorable)} files Stow had moved to {install_paths.STATE / "backups"}')
    return items


def unstow_apply(plan, items):
    if linked_files():
        # Never with sudo, as apply. stow.py --delete unlinks every package, the optional ones too.
        subprocess.run((str(install_paths.REPO / 'scripts/stow.py'), 'remove'), check=True)
    for folder, path in backups():
        target = Path.home() / path.relative_to(folder)
        if not target.exists() and not target.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))


def unsettings_pending(plan):
    return [f'GNOME interface settings saved in {install_paths.INTERFACE.name}'] if install_paths.INTERFACE.exists() and install_plan.booted() else []


def unsettings_apply(plan, items):
    # Saved by theme.py before its first change: one "schema key value" per line, in GVariant text.
    environment = dict(os.environ)
    environment.setdefault('DBUS_SESSION_BUS_ADDRESS', f'unix:path=/run/user/{os.getuid()}/bus')
    for line in install_paths.INTERFACE.read_text(encoding='utf-8').splitlines():
        schema, key, value = (line.split(' ', 2) + ['', ''])[:3]
        if schema and key:
            subprocess.run(('gsettings', 'set', schema, key, value), env=environment, check=False)
    install_paths.INTERFACE.unlink()


def unflatpak_pending(plan):
    apps = plan.record.get('flatpaks', [])
    present = install_plan.query('flatpak', 'list', '--app', '--columns=application').stdout.split() if apps and shutil.which('flatpak') else []
    return [app for app in apps if app in present]


def unflatpak_apply(plan, apps):
    plan.distro.sudo('flatpak', 'uninstall', '-y', '--noninteractive', *apps)


def unauth_pending(plan):
    # Before the packages: PAM would point at modules that are gone.
    recorded = plan.record.get('auth', [])
    return [item for item in recorded if item not in plan.distro.auth_pending(recorded)] if recorded else []


def unauth_apply(plan, items):
    plan.distro.auth_revert(items, install_paths.REPO / 'scripts/tablet-auth.sh')


def unfirewall_pending(plan):
    zone = plan.record.get('firewall_zone')
    if not zone or not install_plan.booted() or not shutil.which('firewall-cmd'):
        return []
    now = install_record.default_zone_now()
    return [] if now == zone or now != install_plan.setting(every_profile(plan), 'firewall_zone') else [zone]


def unfirewall_apply(plan, zones):
    plan.distro.sudo('firewall-cmd', '--set-default-zone=' + zones[0])


def unservices_pending(plan):
    # Units apply turned off come back only with a record: without one, nobody knows they were ever on.
    services = plan.record.get('services', {})
    disable = [unit for unit in services.get('enabled', ()) if install_plan.unit_state(unit) == 'enabled']
    enable = [unit for unit in services.get('disabled', ()) if install_plan.unit_state(unit) == 'disabled']
    users = [unit for unit in services.get('global', ()) if install_plan.query('systemctl', '--global', 'is-enabled', unit).stdout.strip() == 'enabled']
    return ['disable ' + unit for unit in disable] + ['enable ' + unit for unit in enable] + ['disable --global ' + unit for unit in users]


def unshell_pending(plan):
    # Before the packages: a login shell that is gone locks the user out. One chosen since the install stays.
    shell = plan.record.get('login_shell')
    if not shell or install_steps.login_shell() == shell or install_steps.login_shell() != install_plan.setting(every_profile(plan), 'login_shell'):
        return []
    return [shell if Path(shell).exists() else '/bin/bash']


def ungroups_pending(plan):
    return [group for group in plan.record.get('groups', ()) if install_plan.member(getpass.getuser(), group)]


def ungroups_apply(plan, groups):
    for group in groups:
        plan.distro.sudo('gpasswd', '-d', getpass.getuser(), group)


def written_files(plan):
    return {item['path']: item['content'].lstrip() for item in install_plan.merged(every_profile(plan), 'files')}


def changed_files(plan):
    # Recorded files apply would undo, split by whether they still hold what apply wrote or were edited since.
    # What apply wrote is told by its digest in the record; records from before it compare with the manifest.
    written, digests, ours, edited = written_files(plan), plan.record.get('written', {}), [], []
    for path, before in plan.record.get('files', {}).items():
        try:
            now = install_record.read_or_none(path)
        except OSError:
            continue
        if now != before:
            mine = now is not None and (install_steps.text_digest(now) == digests[path] if path in digests else now == written.get(path))
            (ours if mine else edited).append(path)
    return ours, edited


def unfiles_pending(plan):
    return changed_files(plan)[0]


def unfiles_apply(plan, paths):
    for path in paths:
        before = plan.record['files'][path]
        if before is None:
            plan.distro.sudo('rm', '-f', '--', path)
        else:
            plan.distro.write_file(path, before)


def unfirmware_pending(plan):
    # Only a blob still as apply put it: the manifest's file, by hash, that no package has taken over since.
    named = {item['target']: item for item in install_plan.merged(every_profile(plan), 'firmware')}
    return [target for target, existed in plan.record.get('firmware', {}).items()
            if not existed and target in named and Path(target).is_file()
            and install_steps.sha256(target) == named[target]['sha256'] and not plan.distro.owned(target)]


def unfirmware_apply(plan, targets):
    for target in targets:
        plan.distro.sudo('rm', '-f', '--', target)
    plan.distro.rebuild_initramfs()


def removal_split(plan):
    # What apply installed and is still there: swapped packages go back by swap, prerequisites stay. A package
    # someone installed by hand would go with them as a dependent: it stays, and so does everything of ours it needs.
    # Removing some profiles, the packages of those that stay count as installed by hand.
    news = {new for _, new in plan.record.get('swaps', ())}
    names = plan.distro.installed_names([package for package in plan.record.get('packages', ()) if package not in news])
    names = [name for name in names if name.rsplit('.', 1)[0] not in plan.distro.PROTECTED + tuple(news)]
    staying = set(plan.distro.installed_names(plan.record['staying'])) if plan.record.get('staying') else set()
    names = [name for name in names if name not in staying]
    kept = []
    for _ in range(5):  # Each round keeps more; dnf's answer settles in one or two.
        rows = plan.distro.removal(names)
        others = [row for row in rows if row not in names]
        theirs = plan.distro.installed_by_hand(others) | (staying & set(others))
        needed = plan.distro.requirements(sorted(theirs)) if theirs else set()
        if not needed & set(names):
            return names, kept, rows, theirs
        kept += [name for name in names if name in needed]
        names = [name for name in names if name not in needed]
    return names, kept, rows, theirs


def removed_names(plan):
    return removal_split(plan)[0]


def unpackages_pending(plan):
    # dnf's own answer: what depends on them goes too, and so do the dependencies nothing else needs. A package
    # installed by hand that still goes needs one of them in a way dnf did not tell: it is marked, for the review.
    names, kept, rows, theirs = removal_split(plan)
    marked = [row + ('  (installed by hand: it needs one of the others)' if row in theirs else '') for row in rows]
    # A package kept because one that stays (or one installed by hand) needs it is no work of its own: it is listed
    # only beside what goes, so an uninstall run again over what it had to keep has nothing to do.
    if plan.record.get('removing'):
        return marked + [f'keep {name}  (a package that stays needs it)' for name in kept] if rows else []
    return marked + [f'keep {name}  (a package installed by hand needs it)' for name in kept] if rows else []


def unpackages_apply(plan, items):
    plan.distro.remove(removed_names(plan))


def unswaps_pending(plan):
    return [f'{new} -> {old}' for old, new in plan.record.get('swaps', ()) if plan.distro.installed(new) and not plan.distro.installed(old)]


def unswaps_apply(plan, items):
    for old, new in plan.record.get('swaps', ()):
        if f'{new} -> {old}' in items:
            plan.distro.swap(new, old)


def repos_in_use(plan, names):
    # Of these repositories, the ones packages that stay still come from: removing them would stop their updates.
    sources = {name: plan.distro.packages_from(plan.table['repos'][name]) for name in names}
    if not any(sources.values()):
        return {}
    going = {row.rsplit('.', 1)[0] for row in plan.distro.removal(removed_names(plan))}
    going |= {new for old, new in plan.record.get('swaps', ()) if plan.distro.installed(new) and not plan.distro.installed(old)}
    staying = {name: sorted(package for package in packages if package.rsplit('.', 1)[0] not in going) for name, packages in sources.items()}
    return {name: packages for name, packages in staying.items() if packages}


def recorded_repos(plan):
    return [name for name in plan.record.get('repos', ()) if name in plan.table['repos'] and not plan.distro.repo_missing(plan.table['repos'][name])]


def unrepos_pending(plan):
    names = recorded_repos(plan)
    in_use = repos_in_use(plan, names)
    return [name for name in names if name not in in_use]


def unrepos_apply(plan, names):
    for name in names:
        plan.distro.remove_repo(plan.table['repos'][name])


# What uninstall left on purpose and is still there: packages something installed by hand needs, repositories
# that still provide packages. Kept in the record, so a later uninstall can finish once they are free.
def leftovers(plan):
    packages = [name for name in plan.record.get('packages', ()) if plan.distro.installed(name)]
    repos = recorded_repos(plan)
    return {key: value for key, value in (('packages', packages), ('repos', repos)) if value}


def unstate_pending(plan):
    if not plan.record.get('uninstalled'):
        return [f'mark {install_paths.RECORD} as undone']
    left = leftovers(plan)
    current = {key: plan.record[key] for key in ('packages', 'repos') if plan.record.get(key)}
    return [] if left == current else [f'note in {install_paths.RECORD} what is still left']


def unstate_apply(plan, items):
    # Kept, emptied of what is undone: a second uninstall finds only what was left, instead of rebuilding a record
    # from the history.
    install_record.save_record({'uninstalled': True, 'version': 1, **leftovers(plan)})


# In order: the plugins, the login and the links while their tools are installed; PAM and the login shell before
# the packages they point at; the packages before the swaps and repositories they came from; the record last.
UNSTEPS = (
    install_steps.Step('plugins', unplugins_pending, unplugins_apply),
    install_steps.Step('boot', unboot_pending, unboot_apply),
    install_steps.Step('clones', unclones_pending, unclones_apply),
    install_steps.Step('archives', unarchives_pending, unarchives_apply),
    install_steps.Step('aur', unaur_pending, unaur_apply),
    install_steps.Step('stow', unstow_pending, unstow_apply),
    install_steps.Step('settings', unsettings_pending, unsettings_apply),
    install_steps.Step('flatpak', unflatpak_pending, unflatpak_apply),
    install_steps.Step('auth', unauth_pending, unauth_apply),
    install_steps.Step('firewall', unfirewall_pending, unfirewall_apply),
    install_steps.Step('services', unservices_pending, install_steps.services_apply),
    install_steps.Step('shell', unshell_pending, install_steps.shell_apply),
    install_steps.Step('groups', ungroups_pending, ungroups_apply),
    install_steps.Step('files', unfiles_pending, unfiles_apply),
    install_steps.Step('firmware', unfirmware_pending, unfirmware_apply),
    install_steps.Step('packages', unpackages_pending, unpackages_apply),
    install_steps.Step('swaps', unswaps_pending, unswaps_apply),
    install_steps.Step('repos', unrepos_pending, unrepos_apply),
    install_steps.Step('record', unstate_pending, unstate_apply),
)
