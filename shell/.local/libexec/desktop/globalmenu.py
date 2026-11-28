#!/usr/bin/env python3
"""The global menu of the bar (bar/widgets/GlobalMenuWidget.qml, services/GlobalMenu.qml): the menus X11 apps
export over D-Bus, read for the focused window and run from the bar.

An app that has a menu (Electron under X11: VS Code, Obsidian…) hands it to com.canonical.AppMenu.Registrar when
its window opens, by the window's X11 id, and serves it as com.canonical.dbusmenu. Fedora packages no registrar, so
this is one. An app registers only with a registrar already there, so it runs as its own user service
(desktop-globalmenu.service), started by the shell while the widget is on a bar and kept across shell restarts.
Native Wayland apps export no such menu; the apps chosen for the global menu start under X11 (electron.py).

registrar: own the registrar name and keep the windows that register (the service).
watch: for the shell, the menus of the windows it asks about, from the app's own menu where it publishes one
  (the registrar, org.gtk.Menus, dbusmenu, the accessibility tree); globalmenu_reader.py has the protocol.
apps: the installed Electron apps, and which are chosen to start under X11 ({"apps": [{"id", "name", "chosen"}]}).
choose [ID...]: the apps to start under X11 (~/.config/desktop/global-menu-apps.conf), then apply.
apply: their launchers (electron.py: X11 while the widget is on a bar) and the settings an app needs to hand its
  menu over: VS Code only exports it with its native title bar and menus ("window.titleBarStyle" and
  "window.menuStyle": "native"; its own menu bar then shows on Alt, "window.menuBarVisibility": "toggle"). The values found before are kept in
  ~/.local/state/desktop-shell/globalmenu.json and put back when the app leaves the global menu.
"""
from i18n import tr
import configparser
import json
import os
from pathlib import Path
import re
import subprocess
import sys

BUS = 'com.canonical.AppMenu.Registrar'
REGISTRAR = '/com/canonical/AppMenu/Registrar'
MENU = 'com.canonical.dbusmenu'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config')
CHOSEN = CONFIG / 'desktop/global-menu-apps.conf'
STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'desktop-shell/globalmenu.json'
# What an app needs in its own settings to hand its menu over, by desktop ID: the file and the values.
APP_SETTINGS = {
    'com.microsoft.VSCode': (CONFIG / 'Code/User/settings.json',
                             {'window.titleBarStyle': 'native', 'window.menuStyle': 'native', 'window.menuBarVisibility': 'toggle'}),
}
PROPERTIES = ['label', 'type', 'enabled', 'visible', 'shortcut', 'toggle-type', 'toggle-state', 'children-display']
REGISTRAR_XML = '''<node><interface name="com.canonical.AppMenu.Registrar">
<method name="RegisterWindow"><arg type="u" name="windowId" direction="in"/><arg type="o" name="menuObjectPath" direction="in"/></method>
<method name="UnregisterWindow"><arg type="u" name="windowId" direction="in"/></method>
<method name="GetMenuForWindow"><arg type="u" name="windowId" direction="in"/><arg type="s" name="service" direction="out"/><arg type="o" name="menuObjectPath" direction="out"/></method>
<method name="ListWindows"><arg type="a(uso)" name="windows" direction="out"/></method>
<signal name="WindowRegistered"><arg type="u" name="windowId"/><arg type="s" name="service"/><arg type="o" name="menuObjectPath"/></signal>
<signal name="WindowUnregistered"><arg type="u" name="windowId"/></signal>
</interface></node>'''
# Shortcut keys as dbusmenu names them, as the bar shows them.
KEYS = {'Control': 'Ctrl', 'Super': 'Super', 'Shift': 'Shift', 'Alt': 'Alt', 'Return': 'Enter', 'Escape': 'Esc',
        'BackSpace': 'Backspace', 'Delete': 'Del', 'Page_Up': 'PgUp', 'Page_Down': 'PgDn', 'plus': '+', 'minus': '-',
        'comma': ',', 'period': '.', 'slash': '/', 'backslash': '\\', 'grave': '`', 'bracketleft': '[',
        'bracketright': ']', 'semicolon': ';', 'apostrophe': "'", 'equal': '='}


def label(text):
    """A menu label without its mnemonic: "_File" is File, "Save __As" is Save _As."""
    return re.sub(r'_(.)', r'\1', str(text or '')).strip()


def shortcut(value):
    """dbusmenu's shortcut, a list of key lists ([["Control", "Shift", "p"]]), as "Ctrl+Shift+P" (the first)."""
    if not value or not isinstance(value[0], (list, tuple)):
        return ''
    keys = [KEYS.get(key, key.upper() if len(key) == 1 else key) for key in value[0]]
    return '+'.join(keys)


def entry(item):
    """One child of GetLayout (id, properties, children) as the shell draws it; None for one that is hidden."""
    identifier, properties, children = item[0], item[1], item[2]
    if properties.get('visible', True) is False:
        return None
    if properties.get('type') == 'separator':
        return {'id': identifier, 'kind': 'separator'}
    result = {'id': identifier, 'label': label(properties.get('label', '')), 'enabled': properties.get('enabled', True) is not False}
    keys = shortcut(properties.get('shortcut'))
    if keys:
        result['shortcut'] = keys
    if properties.get('children-display') == 'submenu' or children:
        result['submenu'] = True
    toggle = properties.get('toggle-type', '')
    if toggle in ('checkmark', 'radio'):
        result['checked'] = properties.get('toggle-state', 0) == 1
    return result


def entries(children):
    """The children of a menu, hidden ones left out and runs of separators (or one at an end) folded."""
    result = []
    for child in children:
        shown = entry(child)
        if shown is None or shown.get('kind') == 'separator' and (not result or result[-1].get('kind') == 'separator'):
            continue
        result.append(shown)
    while result and result[-1].get('kind') == 'separator':
        result.pop()
    return result


# The apps to choose from: installed desktop entries whose program is an Electron app (its folder holds
# resources/app.asar or resources/app, which a plain Chromium browser does not have).
def data_dirs():
    home = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')
    system = [Path(path) for path in (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if path]
    return [home] + [path for path in system if 'flatpak' not in str(path)]


def resolve(program):
    found = program if '/' in program else next((str(Path(folder) / program) for folder in os.environ.get('PATH', '').split(':')
                                                 if folder and (Path(folder) / program).is_file()), '')
    return os.path.realpath(found) if found else ''


def electron(path):
    folder = Path(path).parent
    return bool(path) and ((folder / 'resources/app.asar').is_file() or (folder / 'resources/app').is_dir())


def program(exec_line):
    words = exec_line.split()
    while words and (words[0] == 'env' or '=' in words[0] and not words[0].startswith('-')):
        words.pop(0)
    return words[0].strip('"') if words else ''


def candidates():
    seen = {}
    # Two entries of one program (1Password ships two) are one app: the first is kept.
    programs = set()
    for folder in data_dirs():
        for path in sorted((folder / 'applications').glob('*.desktop')):
            app_id = path.stem
            if app_id in seen:
                continue
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding='utf-8')
                section = parser['Desktop Entry']
            except (configparser.Error, KeyError, UnicodeDecodeError):
                continue
            seen[app_id] = None
            if section.get('NoDisplay', 'false') == 'true' or section.get('Type', 'Application') != 'Application':
                continue
            path = resolve(program(section.get('Exec', '')))
            if electron(path) and path not in programs:
                programs.add(path)
                seen[app_id] = section.get('Name', app_id)
    return [{'id': app_id, 'name': name} for app_id, name in seen.items() if name]


def chosen():
    try:
        text = CHOSEN.read_text(encoding='utf-8')
    except OSError:
        return []
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith('#')]


def choose(app_ids):
    CHOSEN.parent.mkdir(parents=True, exist_ok=True)
    CHOSEN.write_text('# ' + tr('globalMenu.conf.header') + '\n' + ''.join(app_id + '\n' for app_id in app_ids), encoding='utf-8')
    apply()


# VS Code reads its settings as JSON with comments and trailing commas: the same text without them, for json.
def jsonc(text):
    out = []
    at = 0
    pattern = re.compile(r'"(?:[^"\\]|\\.)*"|//[^\n]*|/\*.*?\*/', re.S)
    for match in pattern.finditer(text):
        out.append(text[at:match.start()])
        out.append(match[0] if match[0].startswith('"') else ' ')
        at = match.end()
    out.append(text[at:])
    return json.loads(re.sub(r',(\s*[}\]])', r'\1', ''.join(out)))


# Targeted edits of VS Code's settings, keeping its order, comments and formatting: a string value set, or a key
# taken out. Each result must still read (as VS Code reads it).
def set_setting(text, key, value):
    encoded = json.dumps(value, ensure_ascii=False)
    pattern = re.compile('(' + re.escape(json.dumps(key)) + r'\s*:\s*)"(?:[^"\\]|\\.)*"')
    if pattern.search(text):
        updated = pattern.sub(lambda match: match[1] + encoded, text, count=1)
    else:
        opening = text.index('{') + 1
        separator = '' if text[opening:].lstrip().startswith('}') else ','
        updated = text[:opening] + '\n    ' + json.dumps(key) + ': ' + encoded + separator + text[opening:]
    jsonc(updated)
    return updated


def drop_setting(text, key):
    item = re.escape(json.dumps(key)) + r'\s*:\s*"(?:[^"\\]|\\.)*"'
    # First as set_setting writes one (a line of its own before the others), so a set and a drop give the file back.
    for pattern in (r'\n[ \t]*' + item + r'[ \t]*,', r'[ \t]*' + item + r'\s*,[ \t]*\n?', r',\s*' + item, r'\n[ \t]*' + item, item):
        updated = re.sub(pattern, '', text, count=1)
        if updated != text:
            try:
                jsonc(updated)
                return updated
            except ValueError:
                continue
    return text


def apply():
    import electron as electron_entries
    from common import write_atomic
    active = electron_entries.x11_apps()
    try:
        saved = json.loads(STATE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        saved = {}
    for app_id, (path, values) in APP_SETTINGS.items():
        try:
            text = path.read_text(encoding='utf-8')
            current = jsonc(text)
        except (OSError, ValueError):
            # No settings file, or one VS Code itself could not read: left alone.
            continue
        updated = text
        if app_id in active:
            # A key set for the first time keeps the value it had; one set before keeps the value saved then.
            before = saved.setdefault(app_id, {})
            for key, value in values.items():
                if key not in before:
                    before[key] = current.get(key)
                    updated = set_setting(updated, key, value)
        elif app_id in saved:
            for key, before in saved.pop(app_id).items():
                updated = set_setting(updated, key, before) if isinstance(before, str) else drop_setting(updated, key)
        if updated != text:
            write_atomic(path, updated)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(STATE, json.dumps(saved, indent=2) + '\n')
    electron_entries.main(['apply'])


def registrar():
    import gi
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio, GLib
    windows = {}
    node = Gio.DBusNodeInfo.new_for_xml(REGISTRAR_XML).interfaces[0]
    state = {}

    def forget(window):
        if windows.pop(window, None) is not None:
            state['connection'].emit_signal(None, REGISTRAR, BUS, 'WindowUnregistered', GLib.Variant('(u)', (window,)))

    def on_call(connection, sender, path, interface, method, parameters, invocation):
        if method == 'RegisterWindow':
            window, menu = parameters.unpack()
            windows[window] = (sender, menu)
            invocation.return_value(None)
            connection.emit_signal(None, REGISTRAR, BUS, 'WindowRegistered', GLib.Variant('(uso)', (window, sender, menu)))
        elif method == 'UnregisterWindow':
            invocation.return_value(None)
            forget(parameters.unpack()[0])
        elif method == 'GetMenuForWindow':
            sender, menu = windows.get(parameters.unpack()[0], ('', '/'))
            invocation.return_value(GLib.Variant('(so)', (sender, menu)))
        elif method == 'ListWindows':
            # Not in the registrar of Unity: every window registered, so the reader finds them by process.
            invocation.return_value(GLib.Variant('(a(uso))', ([(window, owner, menu) for window, (owner, menu) in windows.items()],)))

    # An app that goes away takes its windows with it.
    def on_owner(connection, sender, path, interface, signal, parameters):
        name, _, new = parameters.unpack()
        if not new:
            for window in [window for window, (owner, _) in windows.items() if owner == name]:
                forget(window)

    def on_bus(connection, name):
        state['connection'] = connection
        connection.register_object(REGISTRAR, node, on_call, None, None)
        connection.signal_subscribe('org.freedesktop.DBus', 'org.freedesktop.DBus', 'NameOwnerChanged', '/org/freedesktop/DBus',
                                    None, Gio.DBusSignalFlags.NONE, on_owner)

    Gio.bus_own_name(Gio.BusType.SESSION, BUS, Gio.BusNameOwnerFlags.NONE, on_bus, None, lambda *_: sys.exit(1))
    GLib.MainLoop().run()


def watch():
    # The reader of the menus of windows (globalmenu_reader.py), for the shell.
    import globalmenu_reader
    globalmenu_reader.run()


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    if arguments == ['registrar']:
        registrar()
    elif arguments == ['watch']:
        watch()
    elif arguments == ['apps']:
        picked = set(chosen())
        print(json.dumps({'apps': [dict(app, chosen=app['id'] in picked) for app in candidates()]}))
    elif arguments[:1] == ['choose']:
        choose(arguments[1:])
    elif arguments == ['apply']:
        apply()
    else:
        print(tr('globalMenu.errors.usage'), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
