#!/usr/bin/env python3
"""Releases of this repository: a draft of the changelog section from the commits, then the tag, the stable branch
and the GitHub release.

draft VERSION: print a CHANGELOG.md section for VERSION from the commits since the last release, to edit and commit.
publish VERSION: check main (clean, pushed, its CHANGELOG.md section, CI green), then tag it, move stable to the tag
and create the GitHub release with that section. It asks before pushing anything.
"""
from argparse import ArgumentParser
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'shell/.local/libexec/desktop'))
import channel  # noqa: E402

BRANCH = 'main'
REMOTE = 'origin'
WORKFLOW = 'check.yml'
# Commit types and the changelog heading their subjects go under; the rest (docs, chore, ci, test…) only with --all.
GROUPS = (('feat', 'Added'), ('fix', 'Fixed'), ('perf', 'Changed'), ('refactor', 'Changed'))
SUBJECT = re.compile(r'^(\w+)(?:\([^)]*\))?!?:\s*(.+)$')


def git(*arguments):
    return subprocess.run(('git', '-C', str(REPO), *arguments), capture_output=True, text=True, timeout=120)


def checked(*arguments):
    found = git(*arguments)
    if found.returncode:
        sys.exit(f'git {" ".join(arguments)} failed: {(found.stderr or found.stdout).strip()}')
    return found.stdout.strip()


def valid(version, last):
    if not channel.version_key(version):
        sys.exit(f'{version}: a release is vMAJOR.MINOR.PATCH, as v1.2.0.')
    if last and channel.version_key(version) <= channel.version_key(last):
        sys.exit(f'{version} is not newer than {last}, the last release.')


def draft(subjects, version, today, everything=False):
    # One heading per group, in GROUPS order; a subject's own (#123) stays, as GitHub links it.
    grouped = {}
    for subject in subjects:
        found = SUBJECT.match(subject)
        kind, text = (found[1], found[2]) if found else ('', subject)
        heading = dict(GROUPS).get(kind) or ('Other' if everything else None)
        if heading:
            grouped.setdefault(heading, []).append(text[:1].upper() + text[1:])
    lines = [f'## {version} - {today}', '']
    for heading in dict.fromkeys([heading for _, heading in GROUPS] + ['Other']):
        if grouped.get(heading):
            lines += [f'### {heading}', '', *[f'- {entry}' for entry in grouped[heading]], '']
    return '\n'.join(lines).rstrip() + '\n'


def section(text, version):
    found = [entry for entry in channel.sections(text) if entry['version'] == version]
    return found[0] if found else None


def ci_state(commit):
    # The conclusion of the check workflow on this commit, or why it is unknown.
    if not shutil.which('gh'):
        return 'gh is not installed'
    found = subprocess.run(('gh', 'run', 'list', '--workflow', WORKFLOW, '--commit', commit, '--json', 'status,conclusion',
                            '--limit', '1'), capture_output=True, text=True, cwd=REPO, timeout=60)
    if found.returncode:
        return 'gh run list failed: ' + (found.stderr or found.stdout).strip()
    runs = json.loads(found.stdout or '[]')
    if not runs:
        return 'no run of ' + WORKFLOW
    return runs[0].get('conclusion') or runs[0].get('status') or 'unknown'


def publish(version, skip_ci):
    last = channel.version(git)
    valid(version, last)
    if checked('rev-parse', '--abbrev-ref', 'HEAD') != BRANCH:
        sys.exit(f'Releases are made from {BRANCH}.')
    if git('status', '--porcelain', '--untracked-files=no').stdout.strip():
        sys.exit('The tree has local changes: commit them first.')
    checked('fetch', '--quiet', REMOTE)
    head = checked('rev-parse', 'HEAD')
    if head != checked('rev-parse', f'{REMOTE}/{BRANCH}'):
        sys.exit(f'{BRANCH} differs from {REMOTE}/{BRANCH}: push it (or pull) first.')
    entry = section(channel.changelog_at(git, 'HEAD'), version)
    if not entry or not entry['notes']:
        sys.exit(f'CHANGELOG.md has no section for {version}: draft {version} prints one to edit and commit.')
    stable = git('rev-parse', '--verify', '--quiet', f'refs/remotes/{REMOTE}/{channel.STABLE}')
    if stable.returncode == 0 and git('merge-base', '--is-ancestor', stable.stdout.strip(), head).returncode:
        sys.exit(f'{REMOTE}/{channel.STABLE} is not an ancestor of {BRANCH}: a release only moves it forward.')
    state = ci_state(head)
    if state != 'success' and not skip_ci:
        sys.exit(f'{WORKFLOW} on {head[:7]}: {state}. Wait for it, or pass --skip-ci.')
    print(f'Release {version} (after {last or "none"}) at {head[:7]}, {WORKFLOW}: {state}.')
    print(f'It tags {head[:7]}, pushes the tag, moves {REMOTE}/{channel.STABLE} to it and creates the GitHub release:\n')
    print(entry['notes'] + '\n')
    if input('Publish? [y/N] ').strip().lower() != 'y':
        return 1
    checked('tag', '--annotate', version, '--message', f'{version}\n\n{entry["notes"]}', head)
    checked('push', REMOTE, f'refs/tags/{version}')
    checked('push', REMOTE, f'{head}:refs/heads/{channel.STABLE}')
    if shutil.which('gh'):
        subprocess.run(('gh', 'release', 'create', version, '--title', version, '--notes-file', '-', '--verify-tag'),
                       input=entry['notes'] + '\n', text=True, cwd=REPO, check=True, timeout=120)
    else:
        print('gh is not installed: create the GitHub release by hand.')
    print(f'Published {version}.')
    return 0


def main(argv=None):
    parser = ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action', choices=('draft', 'publish'))
    parser.add_argument('version', help='vMAJOR.MINOR.PATCH')
    parser.add_argument('--all', action='store_true', help='with draft: every commit, not only feat, fix, perf and refactor')
    parser.add_argument('--skip-ci', action='store_true', help='with publish: do not wait for a green check workflow')
    args = parser.parse_args(argv)
    if args.action == 'publish':
        return publish(args.version, args.skip_ci)
    last = channel.version(git)
    valid(args.version, last)
    subjects = checked('log', '--format=%s', f'{last}..HEAD' if last else 'HEAD').splitlines()
    print(draft(subjects, args.version, datetime.date.today().isoformat(), args.all), end='')
    return 0


if __name__ == '__main__':
    sys.exit(main())
