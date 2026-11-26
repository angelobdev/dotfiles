#!/usr/bin/env python3
"""The default apps the shortcuts open: terminal, browser, password manager and file manager.

launch ROLE: start the app chosen for ROLE in Settings → Apps ("defaultApps" in ~/.config/desktop/shell.json), else
its default; an app that is not installed gives way to the first installed one of its kind, and with none a
notification says so.
list: as JSON, per role the choice, the default and the installed apps of its kind, for Settings → Apps.

A choice is a desktop entry id ("kitty.desktop") or a command line ("1password --quick-access").
"""
from i18n import tr
import configparser
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'desktop/shell.json'
# Role -> (default, desktop entry category of its kind). Password managers share no category: the known ones are listed.
ROLES = {
    'terminal': ('kitty.desktop', 'TerminalEmulator'),
    'browser': ('firefox.desktop', 'WebBrowser'),
    'passwords': ('1password --quick-access', None),
    'files': ('org.gnome.Nautilus.desktop', 'FileManager'),
}
PASSWORD_MANAGERS = ('1password.desktop', 'bitwarden.desktop', 'com.bitwarden.desktop.desktop', 'org.keepassxc.KeePassXC.desktop',
                     'proton-pass.desktop', 'me.proton.Pass.desktop', 'enpass.desktop')


def application_dirs():
    # Highest priority first: the user's own entries, then XDG_DATA_DIRS (Flatpak exports are in it in a session).
    home = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    dirs = [home] + [Path(path) for path in (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if path]
    for extra in (Path.home() / '.local/share/flatpak/exports/share', Path('/var/lib/flatpak/exports/share')):
        if extra not in dirs:
            dirs.append(extra)
    return [path / 'applications' for path in dirs]


def read_entry(path):
    parser = configparser.RawConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        parser.read(path, encoding='utf-8')
    except (OSError, configparser.Error, UnicodeDecodeError):
        return None
    if not parser.has_section('Desktop Entry'):
        return None
    entry = parser['Desktop Entry']
    if entry.get('Type', 'Application') != 'Application' or entry.get('Hidden', '').lower() == 'true':
        return None
    return {'name': entry.get('Name', path.stem), 'icon': entry.get('Icon', ''),
            'categories': [part for part in entry.get('Categories', '').split(';') if part],
            'shown': entry.get('NoDisplay', '').lower() != 'true'}


def entries(dirs=None):
    # Desktop entry id -> {path, name, icon, categories, shown}; the first directory that has an id wins, as in XDG.
    found = {}
    for directory in dirs or application_dirs():
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob('*.desktop')):
            identifier = str(path.relative_to(directory)).replace('/', '-')
            if identifier in found:
                continue
            entry = read_entry(path)
            found[identifier] = dict(entry, path=str(path)) if entry else None
    return {identifier: entry for identifier, entry in found.items() if entry}


def chosen(role, path=CONFIG):
    try:
        value = json.loads(path.read_text(encoding='utf-8')).get('defaultApps', {})
    except (OSError, ValueError, AttributeError):
        value = {}
    choice = value.get(role) if isinstance(value, dict) else None
    return choice.strip() if isinstance(choice, str) and choice.strip() else ROLES[role][0]


def of_kind(role, known):
    category = ROLES[role][1]
    if not category:
        return sorted((identifier for identifier in PASSWORD_MANAGERS if identifier in known), key=lambda identifier: known[identifier]['name'].lower())
    return sorted((identifier for identifier, entry in known.items() if category in entry['categories'] and entry['shown']),
                  key=lambda identifier: known[identifier]['name'].lower())


def available(choice, known):
    if choice.endswith('.desktop'):
        return choice in known
    try:
        words = shlex.split(choice)
    except ValueError:
        return False
    return bool(words) and shutil.which(words[0]) is not None


def resolve(role, known=None, path=CONFIG):
    """What launch starts: the choice, else the default, else the first installed app of its kind; None for none."""
    known = entries() if known is None else known
    for choice in (chosen(role, path), ROLES[role][0], *of_kind(role, known)):
        if available(choice, known):
            return choice
    return None


def command(choice, known):
    if choice.endswith('.desktop'):
        return ['gio', 'launch', known[choice]['path']]
    return shlex.split(choice)


def launch(role):
    known = entries()
    choice = resolve(role, known)
    if not choice:
        subprocess.run(['notify-send', '--app-name=' + tr('apps.title'), '--app-icon=dialog-warning', tr('apps.title'),
                        tr('apps.missing', [tr(f'apps.roles.{role}')])], check=False)
        return 1
    arguments = command(choice, known)
    os.execvp(arguments[0], arguments)


def listing():
    known = entries()
    result = {}
    for role, (default, category) in ROLES.items():
        kinds = of_kind(role, known)
        result[role] = {'choice': chosen(role), 'default': default, 'resolved': resolve(role, known) or '',
                        'apps': [{'id': identifier, 'name': known[identifier]['name'], 'icon': known[identifier]['icon']}
                                 for identifier in kinds],
                        'names': {identifier: entry['name'] for identifier, entry in known.items()
                                  if identifier in (default, chosen(role))}}
    return result


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) == 2 and arguments[0] == 'launch' and arguments[1] in ROLES:
        return launch(arguments[1])
    if arguments == ['list']:
        print(json.dumps(listing(), ensure_ascii=False))
        return 0
    print(tr('apps.errors.usage'), file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
