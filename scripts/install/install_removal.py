"""Removing profiles or parts one at a time (PROFILE_UNSTEPS): only what no unit that stays needs goes, and the
record keeps the rest."""
import getpass
import os
from pathlib import Path
import shutil

import install_paths
import install_plan
import install_record
import install_steps
import install_undo


def removable_profiles(profiles):
    return bool(profiles) and 'core' not in profiles and not set(profiles) - set(install_plan.manifest_units())


def recorded_profiles(record):
    # The profiles the record says are installed: None without such a list (no record yet, an install from before
    # records had one, or one undone by an uninstall), which callers take as "nobody can tell".
    profiles = record.get('profiles')
    return profiles if isinstance(profiles, list) and not record.get('uninstalled') else None


def staying_profiles(record, removed):
    # The profiles the record says are installed, but those; without a record of them, every other profile, so that
    # nothing another one may need goes.
    recorded = recorded_profiles(record)
    return tuple(name for name in install_plan.manifest_units() if name not in removed and (recorded is None or name in recorded or name == 'core'))


def profile_record(plan, record, removed, keep=()):
    """The part of record that only the removed profiles set up, as a record for the steps of PROFILE_UNSTEPS.

    keep: units on the system without a record of them (Herdr from its own installer, say). They stay, so nothing
    they need goes, and the record names them from now on: the units file it writes never leaves them out."""
    real = install_record.load_record()
    # Only profiles still installed by the record's account: one removed already has nothing left to undo, and what of
    # it stayed (a package core needs) is core's now.
    recorded = recorded_profiles(real)
    undone = [name for name in install_plan.units(plan.table) if name in removed and (recorded is None or name in recorded)]
    keeping = [name for name in install_plan.manifest_units() if name in keep and name not in removed and recorded is not None and name not in recorded]
    going = plan._replace(profiles=tuple(undone))
    staying = plan._replace(profiles=tuple(name for name in staying_profiles(real, removed) + tuple(keeping) if name in plan.table))

    def only(key):
        kept = install_plan.merged(staying, key)
        return [item for item in install_plan.merged(going, key) if item not in kept]

    def aur(part):
        return [item['package'] for item in install_plan.merged(part, 'aur')]
    wanted = set(install_steps.wanted_packages(staying) + aur(staying))
    packages = set(install_steps.wanted_packages(going) + aur(going)) - wanted
    swapped = [list(pair) for pair in install_steps.swaps(going) if pair not in install_steps.swaps(staying)]
    files = {item['path'] for item in only('files')}
    firmware = {item['target'] for item in only('firmware')}
    archives = {path for item in only('archives') for path in install_steps.archive_paths(item)}
    clones = {item['path'] for item in only('clones')}
    services = record.get('services', {})
    narrowed = {
        'removing': [name for name in install_plan.manifest_units() if name in removed], 'undone': undone, 'keeping': keeping,
        'staying': sorted(wanted),
        'packages': [name for name in record.get('packages', ()) if name in packages],
        'swaps': [pair for pair in record.get('swaps', ()) if list(pair) in swapped],
        'repos': [name for name in record.get('repos', ()) if name in only('repos')],
        'files': {path: before for path, before in record.get('files', {}).items() if path in files},
        'written': {path: digest for path, digest in record.get('written', {}).items() if path in files},
        'firmware': {target: existed for target, existed in record.get('firmware', {}).items() if target in firmware},
        'groups': [group for group in record.get('groups', ()) if group in only('groups')],
        'services': {'enabled': [unit for unit in services.get('enabled', ()) if unit in only('services')],
                     'disabled': [unit for unit in services.get('disabled', ()) if unit in only('disable')],
                     'global': [unit for unit in services.get('global', ()) if unit in only('user_services')]},
        'flatpaks': [app for app in record.get('flatpaks', ()) if app in only('flatpaks')],
        'archives': [path for path in record.get('archives', ()) if path in archives],
        'clones': [path for path in record.get('clones', ()) if path in clones],
        'aur': only('aur'), 'stow': only('stow'),
    }
    for key in ('firewall_zone', 'login_shell'):
        if key in record and install_plan.setting(going, key) and not install_plan.setting(staying, key):
            narrowed[key] = record[key]
    # The authselect items only the removed units asked for: removing tablet keeps with-fingerprint for hardware.fingerprint.
    leaving = [item for item in install_plan.merged(going, 'auth') if item not in install_plan.merged(staying, 'auth')]
    if [item for item in record.get('auth', ()) if item in leaving]:
        narrowed['auth'] = [item for item in record['auth'] if item in leaving]
    if record.get('reconstructed'):
        narrowed['reconstructed'] = True
    return narrowed


def removal_plan(plan, removed, preview=True, keep=()):
    whole = install_undo.uninstall_plan(plan, preview)
    return plan._replace(record=profile_record(plan, whole.record, removed, keep))


def removing_plugins(plan):
    return 'plugins' in plan.record.get('undone', ())


def unprofile_plugins_pending(plan):
    # Without the plugins profile the login check cannot read the headers' version, and nothing can rebuild them.
    return install_undo.unplugins_pending(plan) if removing_plugins(plan) else []


def unprofile_aur_pending(plan):
    return [str(install_steps.aur_path(item)) for item in plan.record.get('aur', ()) if install_steps.aur_path(item).exists()]


def unprofile_aur_apply(plan, paths):
    for path in paths:
        shutil.rmtree(path)


def profile_links(plan):
    # The links of the profile's own Stow packages (steam-hidpi), and the files Stow moved aside for them.
    links, restorable = [], []
    for package in plan.record.get('stow', ()):
        root = install_paths.REPO / package
        for source in sorted(root.rglob('*')) if root.is_dir() else ():
            target = Path.home() / source.relative_to(root)
            if source.is_file() and target.is_symlink() and target.resolve() == source.resolve():
                links.append(target)
        relative = {source.relative_to(root) for source in root.rglob('*')} if root.is_dir() else set()
        restorable += [(folder, path) for folder, path in install_undo.backups() if path.relative_to(folder) in relative]
    return links, restorable


def unprofile_stow_pending(plan):
    links, restorable = profile_links(plan)
    return [f'unlink {link}' for link in links] + [f'put back {Path.home() / path.relative_to(folder)}' for folder, path in restorable
                                                     if not (Path.home() / path.relative_to(folder)).is_file()]


def unprofile_stow_apply(plan, items):
    links, restorable = profile_links(plan)
    for link in links:
        link.unlink()
    for folder, path in restorable:
        target = Path.home() / path.relative_to(folder)
        if not target.exists() and not target.is_symlink():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))


def unprofile_record_pending(plan):
    recorded = install_record.load_record().get('profiles')
    listed = [name for name in plan.record['removing'] if isinstance(recorded, list) and name in recorded]
    keeping = plan.record.get('keeping', ())
    items = [f'note in {install_paths.RECORD} that {", ".join(listed)} ' + ('is' if len(listed) == 1 else 'are') + ' no longer installed'] if listed else []
    if keeping:
        items.append(f'note in {install_paths.RECORD} that {", ".join(keeping)} ' + ('is' if len(keeping) == 1 else 'are') + ' installed, without a record so far')
    return items


def unprofile_record_apply(plan, items):
    # The record without the profiles, and without what is undone: a package installed again later by hand is the
    # user's, and the full uninstall leaves it. What stays (a package something needs, a repository in use) stays there.
    record = install_record.load_record()
    if not record or record.get('uninstalled'):
        return
    narrowed = plan.record
    if isinstance(record.get('profiles'), list):
        record['profiles'] = [name for name in record['profiles'] if name not in narrowed['removing']]
        record['profiles'] += [name for name in narrowed.get('keeping', ()) if name not in record['profiles']]
    gone = {
        'packages': plan.distro.missing(narrowed['packages']) if narrowed['packages'] else [],
        'swaps': [pair for pair in narrowed['swaps'] if not plan.distro.installed(pair[1])],
        'repos': [name for name in narrowed['repos'] if name not in install_undo.recorded_repos(plan)],
        'groups': [group for group in narrowed['groups'] if not install_plan.member(getpass.getuser(), group)],
        'flatpaks': [app for app in narrowed['flatpaks'] if app not in install_undo.unflatpak_pending(plan)],
        'archives': [path for path in narrowed['archives'] if not os.path.lexists(Path.home() / path)],
        'clones': [path for path in narrowed['clones'] if not (Path.home() / path).exists()],
    }
    for key, values in gone.items():
        if key in record:
            record[key] = [value for value in record[key] if value not in values]
    ours = set(install_undo.changed_files(plan)[0])
    for path in narrowed['files']:
        if path not in ours:
            record.get('files', {}).pop(path, None)
            record.get('written', {}).pop(path, None)
    for target in narrowed['firmware']:
        if target not in install_undo.unfirmware_pending(plan):
            record.get('firmware', {}).pop(target, None)
    for kind, units in narrowed['services'].items():
        if kind in record.get('services', {}):
            record['services'][kind] = [unit for unit in record['services'][kind] if unit not in units]
    if 'firewall_zone' in narrowed and not install_undo.unfirewall_pending(plan):
        record.pop('firewall_zone', None)
    if narrowed.get('auth'):
        still = install_undo.unauth_pending(plan)
        record['auth'] = [item for item in record.get('auth', ()) if item not in narrowed['auth'] or item in still]
        if not record['auth']:
            record.pop('auth')
    install_record.save_record(record)


# In the order of UNSTEPS; the boot, the clones of core, the GNOME settings and the login shell belong to core.
PROFILE_UNSTEPS = (
    install_steps.Step('plugins', unprofile_plugins_pending, install_undo.unplugins_apply),
    install_steps.Step('clones', install_undo.unclones_pending, install_undo.unclones_apply),
    install_steps.Step('archives', install_undo.unarchives_pending, install_undo.unarchives_apply),
    install_steps.Step('aur', unprofile_aur_pending, unprofile_aur_apply),
    install_steps.Step('stow', unprofile_stow_pending, unprofile_stow_apply),
    install_steps.Step('flatpak', install_undo.unflatpak_pending, install_undo.unflatpak_apply),
    install_steps.Step('auth', install_undo.unauth_pending, install_undo.unauth_apply),
    install_steps.Step('firewall', install_undo.unfirewall_pending, install_undo.unfirewall_apply),
    install_steps.Step('services', install_undo.unservices_pending, install_steps.services_apply),
    install_steps.Step('groups', install_undo.ungroups_pending, install_undo.ungroups_apply),
    install_steps.Step('files', install_undo.unfiles_pending, install_undo.unfiles_apply),
    install_steps.Step('firmware', install_undo.unfirmware_pending, install_undo.unfirmware_apply),
    install_steps.Step('packages', install_undo.unpackages_pending, install_undo.unpackages_apply),
    install_steps.Step('swaps', install_undo.unswaps_pending, install_undo.unswaps_apply),
    install_steps.Step('repos', install_undo.unrepos_pending, install_undo.unrepos_apply),
    install_steps.Step('record', unprofile_record_pending, unprofile_record_apply),
)
