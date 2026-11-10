"""Newer pins for the manifest: the clones, AUR packages and release archives it pins to a commit or a version,
checked against their remotes, and written back into the manifest on request."""
from collections import namedtuple
import json
import re
import tomllib
import urllib.parse
import urllib.request

import install_paths
import install_plan
import install_steps


# Pins: manifest entries fixed to a commit, AUR packages and clones, or to a version, release archives. Newer is the
# AUR's latest commit, a clone's latest release tag (track = 'tags'), or else the head of its default branch, and an
# archive's version in its release manifest (latest). version is what the new commit of a PKGBUILD builds, tag the
# release a clone moves to, hashes the sha256 of each architecture of an archive; url shows the changes to review.
Pin = namedtuple('Pin', 'kind name old new label url version tag hashes', defaults=(None,))


def remote_head(repo):
    result = install_plan.query('git', 'ls-remote', repo, 'HEAD', timeout=install_plan.REMOTE_TIMEOUT)
    fields = result.stdout.split()
    return fields[0] if result.returncode == 0 and fields else ''


def aur_head(package):
    return remote_head(install_paths.AUR + package + '.git')


def aur_srcinfo(package, commit):
    url = f'{install_paths.AUR}cgit/aur.git/plain/.SRCINFO?' + urllib.parse.urlencode({'h': package, 'id': commit})
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode('utf-8')


def version_key(name):
    # Natural order, digits as numbers: 26.10.1 after 26.9.30. Splitting on a group alternates text and numbers.
    return [int(part) if index % 2 else part for index, part in enumerate(re.split(r'(\d+)', name))]


def remote_tags(repo):
    # {tag: commit}. An annotated tag stands for the commit it points to, its ^{} line.
    result = install_plan.query('git', 'ls-remote', '--tags', repo, timeout=install_plan.REMOTE_TIMEOUT)
    tags = {}
    for line in result.stdout.splitlines() if result.returncode == 0 else ():
        commit, _, ref = line.partition('\t')
        name = ref.removeprefix('refs/tags/')
        if name.endswith('^{}'):
            tags[name[:-3]] = commit
        elif name:
            tags.setdefault(name, commit)
    return tags


def pin_name(kind, item):
    if kind == 'archives':
        return item['name']
    return item['package'] if kind == 'aur' else item['path'].rstrip('/').rsplit('/', 1)[-1]


def pin_entries(tables, profiles=None):
    # Every pinned entry of these tables, once: the same clone pinned on two distributions moves for both.
    entries = {}
    for table in tables:
        table = install_plan.flatten_parts(table)
        for profile in profiles or install_plan.units(table):
            for kind in ('aur', 'clones', 'archives'):
                for item in table.get(profile, {}).get(kind, ()):
                    key = (kind, item.get('package') or item.get('repo') or item['name'], item.get('commit') or item['version'])
                    entries.setdefault(key, (kind, item))
    return list(entries.values())


def newer_archive(item):
    try:
        with install_steps.open_url(item['latest'], 30) as response:
            latest = json.load(response)
        new, targets = latest['version'], latest['targets']
        hashes = {arch: targets[f'linux-{arch}']['sha256'] for arch in item['sha256']}
        # The download URL must still be the one the manifest builds, or apply would fetch something else.
        urls = [targets[f'linux-{arch}']['url'] for arch in item['sha256']]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    if any(url != item['url'].format(version=new, arch=arch) for arch, url in zip(item['sha256'], urls)):
        return False
    if new == item['version']:
        return None
    return Pin('archives', item['name'], item['version'], new, f'{item["version"]} -> {new}', item.get('changes') or item['latest'],
               '', '', hashes)


def newer_pin(kind, item):
    # The Pin to move to; None when the entry is at its latest; False when its remote did not answer.
    if kind == 'archives':
        return newer_archive(item)
    if kind == 'aur':
        new = aur_head(item['package'])
        if not new or new == item['commit']:
            return None if new else False
        version = install_steps.srcinfo_version(aur_srcinfo(item['package'], new))
        url = f'{install_paths.AUR}cgit/aur.git/diff/?' + urllib.parse.urlencode({'h': item['package'], 'id': new, 'id2': item['commit']})
        return Pin(kind, item['package'], item['commit'], new, f'{item["version"]} -> {version}', url, version, '')
    if item.get('track') == 'tags':
        tags = remote_tags(item['repo'])
        if not tags:
            return False
        tag = max(tags, key=version_key)
        new = tags[tag]
        old = next((name for name in sorted(tags, key=version_key) if tags[name] == item['commit']), item['commit'][:12])
        label = f'{old} -> {tag}'
    else:
        new, tag = remote_head(item['repo']), ''
        if not new:
            return False
        label = f'{item["commit"][:12]} -> {new[:12]}'
    if new == item['commit']:
        return None
    url = f'{item["repo"]}/compare/{item["commit"]}...{new}' if item['repo'].startswith('https://github.com/') else item['repo']
    return Pin(kind, pin_name(kind, item), item['commit'], new, label, url, '', tag)


def repin(text, old, new, version='', tag=''):
    # Each manifest table pinned to old, rewritten in place: its commit line, with the release it is at as a comment
    # for a clone that follows tags, and for an AUR package the version line of the same table.
    lines = text.splitlines(keepends=True)
    pinned = re.compile(r"commit = '" + re.escape(old) + r"'(\s*#.*)?")
    for index, line in enumerate(lines):
        if not pinned.fullmatch(line.strip()):
            continue
        lines[index] = f"commit = '{new}'" + (f'  # {tag}' if tag else '') + '\n'
        if not version:
            continue
        start, end = index, index + 1
        while start > 0 and not lines[start].startswith('['):
            start -= 1
        while end < len(lines) and not lines[end].startswith('['):
            end += 1
        for other in range(start, end):
            if lines[other].startswith('version = '):
                lines[other] = f"version = '{version}'\n"
    return ''.join(lines)


def repin_archive(text, name, old, new, hashes):
    # Each archive table of that name at version old: its version and sha256 lines.
    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.startswith('[')] + [len(lines)]
    for start, end in zip(starts, starts[1:]):
        block = [line.strip() for line in lines[start:end]]
        if f"name = '{name}'" not in block or f"version = '{old}'" not in block:
            continue
        for index in range(start, end):
            if lines[index].strip() == f"version = '{old}'":
                lines[index] = f"version = '{new}'\n"
            elif lines[index].startswith('sha256 = {'):
                lines[index] = 'sha256 = { ' + ', '.join(f"{arch} = '{digest}'" for arch, digest in hashes.items()) + ' }\n'
    return ''.join(lines)


def apply_pin(text, pin):
    if pin.kind == 'archives':
        return repin_archive(text, pin.name, pin.old, pin.new, pin.hashes)
    return repin(text, pin.old, pin.new, pin.version, pin.tag)


def pins(update):
    # The pins of every distribution, not only this one: they can be moved from any machine.
    path = install_paths.INSTALL / 'manifest.toml'
    text = path.read_text(encoding='utf-8')
    tables = [table for table in tomllib.loads(text).values() if isinstance(table, dict)]
    newer, failed = [], 0
    for kind, item in pin_entries(tables):
        # One remote that fails (the AUR's .SRCINFO, a release page) is that entry's failure, not the listing's.
        try:
            pin = newer_pin(kind, item)
        except OSError as error:
            pin = False
            print(f'{pin_name(kind, item)}: {error}')
        if pin is False:
            where = 'the AUR' if kind == 'aur' else item.get('repo') or item['latest']
            print(f'{pin_name(kind, item)}: {where} did not answer.')
            failed += 1
        elif pin:
            newer.append(pin)
            print(f'{pin.name} {pin.label}')
            print(f'  review the changes: {pin.url}')
            if update:
                text = apply_pin(text, pin)
    if update and newer:
        path.write_text(text, encoding='utf-8')
        print(f'Pinned in {path.relative_to(install_paths.REPO)}: install-desktop.py apply builds and checks them out.')
    elif newer:
        print('install-desktop.py pins --update pins them.')
    elif not failed:
        print('Every pin is at its latest commit.')
    return 1 if failed else 0
