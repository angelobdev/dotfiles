#!/usr/bin/env python3
"""The coding agents the AI assistant can run, declared one per JSON file.

Each agent is a file in ~/.local/share/desktop/agents/<id>.json (shipped) or ~/.config/desktop/agents/<id>.json
(the user's own, which wins for the same id): its name, the program that tells it is installed (binary), the
command the console runs, how it installs (a shell command, run in a terminal the user sees), what it needs for
that (needs), how an image path is passed at its prompt (image, with {path}), the name herdr gives it (herdr)
and, for Claude Code, the hooks desktop-ai adds (hooks: "claude").

The primary agent, the one Super + A opens: DESKTOP_AI_AGENT, else "aiPrimary" in ~/.config/desktop/shell.json
when it is installed, else the first installed by order.

list: every agent as JSON, with installed, path and what install still needs, and the primary.
primary: the primary agent's id ("" when none is installed).
argv ID: its command as JSON, the program resolved to a path.
image ID PATH: the text to type at its prompt for an image.
hooks ID: the hooks desktop-ai adds for it ("claude", or nothing).
install ID: runs its install command in a Kitty window and waits until the window closes.
"""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

from i18n import tr

HOME = Path.home()
SHIPPED = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'desktop/agents'
OWN = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'desktop/agents'
SHELL_JSON = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'desktop/shell.json'
ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,31}$')
BINARY = re.compile(r'^[A-Za-z0-9._+-]{1,64}$')
# Where agent installers put their programs, which Hyprland's exec PATH lacks.
LOCAL_BIN = HOME / '.local/bin'


def search_path():
    parts = os.environ.get('PATH', '').split(os.pathsep)
    return os.pathsep.join([str(LOCAL_BIN)] + [part for part in parts if part and part != str(LOCAL_BIN)])


def valid(entry):
    """The agent as used here, or None when the file does not describe one."""
    if not isinstance(entry, dict):
        return None
    name, binary, command = entry.get('name'), entry.get('binary'), entry.get('command')
    if not isinstance(name, str) or not name.strip() or not isinstance(binary, str) or not BINARY.match(binary):
        return None
    if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
        return None
    image = entry.get('image', '{path}')
    if not isinstance(image, str) or '{path}' not in image:
        return None
    install = entry.get('install')
    needs = entry.get('needs', [])
    if install is not None and not isinstance(install, str):
        return None
    if not isinstance(needs, list) or not all(isinstance(need, str) and BINARY.match(need) for need in needs):
        return None
    return {
        'name': name.strip(), 'vendor': str(entry.get('vendor') or ''), 'homepage': str(entry.get('homepage') or ''),
        'binary': binary, 'command': command, 'install': install or '', 'needs': needs, 'image': image,
        'herdr': str(entry.get('herdr') or ''), 'hooks': str(entry.get('hooks') or ''),
        'order': entry.get('order') if isinstance(entry.get('order'), (int, float)) else 100,
    }


def agents(folders=None):
    found = {}
    for folder in folders or (SHIPPED, OWN):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob('*.json')):
            if not ID.match(path.stem):
                continue
            try:
                entry = valid(json.loads(path.read_text(encoding='utf-8')))
            except (OSError, ValueError):
                entry = None
            if entry:
                found[path.stem] = dict(entry, id=path.stem)
    return sorted(found.values(), key=lambda agent: (agent['order'], agent['name'].lower()))


def where(binary):
    return shutil.which(binary, path=search_path()) or ''


def chosen():
    try:
        value = json.loads(SHELL_JSON.read_text(encoding='utf-8')).get('aiPrimary', '')
    except (OSError, ValueError, AttributeError):
        value = ''
    return value if isinstance(value, str) else ''


def primary(listed=None):
    listed = listed if listed is not None else agents()
    installed = [agent for agent in listed if where(agent['binary'])]
    for wanted in (os.environ.get('DESKTOP_AI_AGENT', ''), chosen()):
        match = next((agent for agent in installed if wanted in (agent['id'], agent['binary'])), None) if wanted else None
        if match:
            return match
    return installed[0] if installed else None


def find(name):
    agent = next((agent for agent in agents() if agent['id'] == name), None)
    if not agent:
        raise ValueError(tr('assistant.errors.unknownAgent', [name]))
    return agent


def command_list():
    listed = agents()
    lead = primary(listed)
    print(json.dumps({
        'agents': [dict(agent, path=where(agent['binary']), missing=[need for need in agent['needs'] if not where(need)])
                   for agent in listed],
        'primary': lead['id'] if lead else '',
        'chosen': chosen(),
        'override': os.environ.get('DESKTOP_AI_AGENT', ''),
    }, ensure_ascii=False))


def command_argv(name):
    agent = find(name)
    path = where(agent['binary'])
    if not path:
        raise ValueError(tr('assistant.errors.agentMissing', [agent['name']]))
    argv = list(agent['command'])
    if argv[0] == agent['binary']:
        argv[0] = path
    print(json.dumps(argv))


def command_image(name, path):
    print(find(name)['image'].replace('{path}', path))


def command_install(name):
    agent = find(name)
    if not agent['install']:
        raise ValueError(tr('assistant.errors.noInstall', [agent['name']]))
    missing = [need for need in agent['needs'] if not where(need)]
    if missing:
        raise ValueError(tr('assistant.errors.installNeeds', [agent['name'], ', '.join(missing)]))
    # The installer runs where the user sees it (it may print a login link or ask something); the window stays
    # until Enter, with the result.
    script = (
        f'printf "%s\\n\\n" {shlex.quote(tr("assistant.install.running", [agent["name"]]))}\n'
        f'{agent["install"]}\n'
        'status=$?\n'
        f'if [ $status -eq 0 ]; then printf "\\n%s\\n" {shlex.quote(tr("assistant.install.done", [agent["name"]]))}; '
        f'else printf "\\n%s\\n" {shlex.quote(tr("assistant.install.failed", [agent["name"]]))}; fi\n'
        f'printf "%s" {shlex.quote(tr("assistant.install.close"))}\n'
        'read -r _\n'
    )
    environment = dict(os.environ, PATH=search_path())
    # desktop-updates: the window rule that floats a terminal in the middle (hypr/config/rules.lua).
    subprocess.run(['kitty', '--class', 'desktop-updates', '--title', tr('assistant.install.title', [agent['name']]),
                    'sh', '-c', script], env=environment, check=False)


def main(arguments):
    if not arguments:
        raise ValueError(__doc__)
    command, rest = arguments[0], arguments[1:]
    if command == 'list' and not rest:
        command_list()
    elif command == 'primary' and not rest:
        lead = primary()
        print(lead['id'] if lead else '')
    elif command == 'argv' and len(rest) == 1:
        command_argv(rest[0])
    elif command == 'hooks' and len(rest) == 1:
        print(find(rest[0])['hooks'])
    elif command == 'image' and len(rest) == 2:
        command_image(*rest)
    elif command == 'install' and len(rest) == 1:
        command_install(rest[0])
    else:
        raise ValueError(__doc__)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
