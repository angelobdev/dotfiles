#!/usr/bin/env python3
"""The release channel of this repository: its version, the branch it follows, and the changelog since the last one seen.

whats-new: the CHANGELOG.md sections of the versions installed since the last one seen, as JSON (services/Release.qml).
whats-new --current: the section of the installed version, for About, seen or not.
seen: record the installed version as seen.

A clone follows the stable branch, which every release moves to its tag (scripts/release.py). A clone on main moves
to stable at the first update that is a fast-forward from where it is, and so does one whose branch is gone from the
remote. A maintainer (git config desktop.maintainer true) stays on the branch they track (develop).
"""
from common import write_atomic
from i18n import tr
import json
import os
from pathlib import Path
import re
import subprocess
import sys

# The clone this helper is linked from (Stow links every file, so the path resolves into it).
REPO = Path(__file__).resolve().parents[4]
STABLE = 'stable'
CHANGELOG = 'CHANGELOG.md'
STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-shell/whats-new.json'
# Written by every update check: a shell that finds it has run before releases began.
CHECKED = STATE.with_name('updates.json')
SECTION = re.compile(r'^## (v\d+\.\d+\.\d+)(?:\s+-\s+(\S+))?\s*$', re.M)
VERSION = re.compile(r'^v(\d+)\.(\d+)\.(\d+)$')
# Below every release: between() from it lists them all.
FIRST = 'v0.0.0'


def version_key(version):
    found = VERSION.match(version or '')
    return tuple(int(part) for part in found.groups()) if found else ()


def default_git(*arguments):
    environment = dict(os.environ, GIT_TERMINAL_PROMPT='0', LC_ALL='C')
    return subprocess.run(['git', '-C', str(REPO), *arguments], capture_output=True, text=True, env=environment, timeout=30)


def version(git, revision='HEAD'):
    # The newest release tag reachable from the revision, '' before the first one.
    found = git('describe', '--tags', '--abbrev=0', '--match', 'v[0-9]*', revision)
    name = found.stdout.strip() if found.returncode == 0 else ''
    return name if version_key(name) else ''


def maintainer(git):
    # Who publishes the releases: `git config desktop.maintainer true` in this clone. They follow their own branch.
    return git('config', '--bool', 'desktop.maintainer').stdout.strip() == 'true'


def upstream(git):
    """(upstream, remote): the branch this one tracks and its remote; ('', 'origin') when the branch it tracked is
    gone from the remote but origin has stable (main, once deleted); (None, None) with nothing to follow."""
    found = git('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}')
    name = found.stdout.strip() if found.returncode == 0 else ''
    if name:
        return name, name.split('/', 1)[0]
    if git('rev-parse', '--verify', '--quiet', f'refs/remotes/origin/{STABLE}').returncode == 0:
        return '', 'origin'
    return None, None


def target(git, upstream, remote=None):
    """The branch to follow, after a fetch: the remote's stable branch, or the upstream for a maintainer and for a
    remote without one yet."""
    remote = remote or upstream.split('/', 1)[0]
    stable = f'{remote}/{STABLE}'
    if upstream == stable or (upstream and maintainer(git)):
        return upstream
    found = git('rev-parse', '--verify', '--quiet', f'refs/remotes/{stable}')
    return stable if found.returncode == 0 else upstream


def update_command(followed, upstream):
    # A clone that moves to stable takes the branch of that name; one already on it fast-forwards.
    if followed != upstream:
        return ('switch', '-C', STABLE, '--track', followed)
    return ('merge', '--ff-only', followed)


def sections(text):
    """[{version, date, notes}] of a changelog, newest first as written: '## v1.2.0 - 2026-12-01' headings, the
    Markdown under each up to the next."""
    found = list(SECTION.finditer(text or ''))
    result = []
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(text)
        result.append({'version': match[1], 'date': match[2] or '', 'notes': text[match.end():end].strip()})
    return result


def between(text, since, until):
    # The sections after since up to until; with no since, the one of until alone.
    upper = version_key(until)
    if not upper:
        return []
    lower = version_key(since)
    picked = [section for section in sections(text)
              if version_key(section['version']) <= upper and (version_key(section['version']) > lower if lower else
                                                                 section['version'] == until)]
    return sorted(picked, key=lambda section: version_key(section['version']), reverse=True)


def changelog_at(git, revision):
    found = git('show', f'{revision}:{CHANGELOG}')
    return found.stdout if found.returncode == 0 else ''


def read_changelog(repo=None):
    try:
        return ((repo or REPO) / CHANGELOG).read_text(encoding='utf-8')
    except OSError:
        return ''


def seen_version(path=STATE):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return value.get('seen') if isinstance(value, dict) and isinstance(value.get('seen'), str) else None


def record_seen(name, path=STATE):
    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, json.dumps({'seen': name}) + '\n')


def whats_new(git=default_git, current_only=False, path=STATE, checked=CHECKED):
    """{version, sections}: the notes not seen yet. With nothing recorded, a shell that ran before releases began
    (it has checked for updates) sees the notes of every release up to its version once, since it may come straight
    to a later one, and a new install starts from its version."""
    installed = version(git)
    text = read_changelog()
    if current_only:
        return {'version': installed, 'sections': between(text, '', installed)}
    seen = seen_version(path)
    if not installed or seen == installed:
        return {'version': installed, 'sections': []}
    if seen is None and not checked.exists():
        record_seen(installed, path)
        return {'version': installed, 'sections': []}
    # A version older than the one seen (a downgrade) has nothing new to say.
    if seen and version_key(seen) > version_key(installed):
        return {'version': installed, 'sections': []}
    return {'version': installed, 'sections': between(text, seen or FIRST, installed)}


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments in (['whats-new'], ['whats-new', '--current']):
        print(json.dumps(whats_new(current_only=len(arguments) == 2), ensure_ascii=False))
        return 0
    if arguments == ['seen']:
        installed = version(default_git)
        if installed:
            record_seen(installed)
        return 0
    print(tr('release.errors.usage'), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
