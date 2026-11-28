"""The menus of windows for the global menu of the bar (globalmenu.py watch, services/GlobalMenu.qml).

For each window the shell asks about, the menu of its app comes from the first source that has one:
1. dbusmenu through the registrar (desktop-globalmenu.service): X11 apps, Electron under XWayland (VS Code);
2. org.gtk.Menus: GTK apps that publish their menu bar (GtkApplication);
3. dbusmenu the app publishes itself (Qt apps);
4. the accessibility tree (AT-SPI): the menu bar of the window as screen readers see it (Firefox and its family,
   Qt, GTK 3). While this runs it keeps accessibility on for the session, as a screen reader does: an app that was
   already open before shows its menu once restarted.
Without one the shell draws a generic menu. The cascade and the AT-SPI walk follow Oma Top Menu
(github.com/Somnius/oma.top.menu, based on primo.global-menu by PrimoGameStudio; MIT).

Protocol, one JSON object per line. In: {"cmd": "menu", "address", "pid", "xwayland", "title"}, {"cmd": "open",
"address", "id"}, {"cmd": "click", "address", "id"}, {"cmd": "forget", "address"}. Out: {"address", "source",
"menu": [{"id", "label"}]}, {"address", "open": id, "items": [entries]}, {"address", "changed": true} when a menu
it read changed, {"error"}. Entry ids are strings: "d:N" (dbusmenu), "g:GROUP:MENU" and "ga:N" (GTK), "a:I/J/…" (an
AT-SPI path below the menu bar).
"""
import json
import os
import re
import sys

from globalmenu import BUS, MENU, PROPERTIES, REGISTRAR, entries, label

# Roles of an AT-SPI menu, by name (Atspi.Role values differ between versions).
SUBMENU = {'MENU', 'POPUP_MENU'}
ITEMS = {'MENU_ITEM', 'CHECK_MENU_ITEM', 'RADIO_MENU_ITEM', 'MENU'}
FRAMES = {'FRAME', 'WINDOW', 'DIALOG'}


def gi_modules():
    import gi
    gi.require_version('Gio', '2.0')
    gi.require_version('Atspi', '2.0')
    from gi.repository import Atspi, Gio, GLib
    return Atspi, Gio, GLib


def parents(pid, count=4):
    """pid and its ancestors: a GTK app forks, its D-Bus connection can be the parent's."""
    found = []
    while pid and len(found) < count:
        found.append(pid)
        try:
            with open(f'/proc/{pid}/stat') as stat:
                pid = int(stat.read().rsplit(')', 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            break
    return found


def norm(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip().lower()


def shortcut_text(binding):
    """An AT-SPI key binding ("<Control>n", "n;<Control>n;…", "Ctrl+N") as "Ctrl+N"; "" without one."""
    parts = [part for part in str(binding or '').split(';') if part]
    if not parts:
        return ''
    text = parts[-1]
    if '<' in text:
        mods = re.findall(r'<([^>]+)>', text)
        key = re.sub(r'<[^>]+>', '', text)
        names = {'Control': 'Ctrl', 'Primary': 'Ctrl', 'Shift': 'Shift', 'Alt': 'Alt', 'Mod1': 'Alt', 'Super': 'Super', 'Meta': 'Super'}
        key = key.upper() if len(key) == 1 else key
        if ':' in key:
            return ''
        return '+'.join([names.get(mod, mod) for mod in mods] + ([key] if key else []))
    # "Alt+V:T" (Firefox) is the way to the entry by its access keys, not a shortcut.
    return text if len(text) <= 24 and ':' not in text else ''


def item_label(text):
    """A menu label: its mnemonic out, and a shortcut some toolkits append after a tab cut off."""
    return label(str(text or '').split('\t', 1)[0])


class Source:
    name = ''

    def menu(self):
        return []

    def open(self, entry_id):
        return []

    def click(self, entry_id):
        pass


class Dbusmenu(Source):
    name = 'dbusmenu'

    def __init__(self, reader, service, path):
        self.reader, self.service, self.path = reader, service, path

    def call(self, method, signature=None, arguments=()):
        _, Gio, GLib = self.reader.modules
        return self.reader.bus.call_sync(self.service, self.path, MENU, method, GLib.Variant(signature, arguments) if signature else None,
                                         None, Gio.DBusCallFlags.NONE, 3000, None).unpack()

    def children(self, parent):
        _, _, GLib = self.reader.modules
        # The top level is never told it is about to show: an Electron app answers by rebuilding its menu and
        # withdrawing the window from the registrar.
        if parent != 0:
            try:
                self.call('AboutToShow', '(i)', (parent,))
            except GLib.Error:
                pass
        return self.call('GetLayout', '(iias)', (parent, 1, PROPERTIES))[1][2]

    def convert(self, items):
        for item in items:
            item['id'] = 'd:' + str(item['id'])
        return items

    def menu(self):
        return [item for item in self.convert(entries(self.children(0))) if item.get('kind') != 'separator']

    def open(self, entry_id):
        return self.convert(entries(self.children(int(entry_id[2:]))))

    def click(self, entry_id):
        _, _, GLib = self.reader.modules
        self.call('Event', '(isvu)', (int(entry_id[2:]), 'clicked', GLib.Variant('i', 0), 0))


class GtkMenus(Source):
    """org.gtk.Menus: a GMenuModel in groups of menus, items linked to sections and submenus, actions run
    through org.gtk.Actions on the application (app.) or its window (win.)."""
    name = 'gtk'

    def __init__(self, reader, service, app_path, menubar_path):
        self.reader, self.service, self.app_path, self.menubar_path = reader, service, app_path, menubar_path
        self.menus = {}
        self.actions = []

    def load(self, groups):
        _, Gio, GLib = self.reader.modules
        wanted = [group for group in groups if not any(key[0] == group for key in self.menus)]
        if not wanted:
            return
        reply = self.reader.bus.call_sync(self.service, self.menubar_path, 'org.gtk.Menus', 'Start', GLib.Variant('(au)', (wanted,)),
                                          None, Gio.DBusCallFlags.NONE, 3000, None)
        for group, menu, items in reply.unpack()[0]:
            self.menus[(group, menu)] = items
        try:
            self.reader.bus.call_sync(self.service, self.menubar_path, 'org.gtk.Menus', 'End', GLib.Variant('(au)', (wanted,)),
                                      None, Gio.DBusCallFlags.NONE, 1000, None)
        except GLib.Error:
            pass

    def items(self, key, depth=0):
        """The entries of a menu, its sections inline between separators."""
        self.load([key[0]])
        result = []
        for item in self.menus.get(key, []):
            if ':section' in item and depth < 6:
                section = self.items(tuple(item[':section']), depth + 1)
                if section:
                    if result and result[-1].get('kind') != 'separator':
                        result.append({'id': 'gs', 'kind': 'separator'})
                    result += section
                continue
            text = item_label(item.get('label', ''))
            if not text:
                continue
            if ':submenu' in item:
                group, menu = item[':submenu']
                result.append({'id': f'g:{group}:{menu}', 'label': text, 'enabled': True, 'submenu': True})
                continue
            self.actions.append((item.get('action', ''), item.get('target')))
            entry = {'id': f'ga:{len(self.actions) - 1}', 'label': text, 'enabled': bool(item.get('action'))}
            if item.get('accel'):
                entry['shortcut'] = shortcut_text(item['accel'])
            result.append(entry)
        while result and result[-1].get('kind') == 'separator':
            result.pop()
        return result

    def menu(self):
        top = []
        for item in self.items((0, 0)):
            if item.get('submenu'):
                top.append({'id': item['id'], 'label': item['label']})
        return top

    def open(self, entry_id):
        _, group, menu = entry_id.split(':')
        return self.items((int(group), int(menu)))

    def click(self, entry_id):
        _, Gio, GLib = self.reader.modules
        action, target = self.actions[int(entry_id[3:])]
        if '.' not in action:
            return
        scope, name = action.split('.', 1)
        path = self.app_path
        if scope == 'win':
            windows = self.reader.children_of(self.service, self.app_path.rstrip('/') + '/window')
            if not windows:
                return
            path = self.app_path.rstrip('/') + '/window/' + windows[0]
        parameters = []
        if target is not None:
            kinds = {bool: 'b', int: 'i', float: 'd', str: 's'}
            parameters = [GLib.Variant(kinds.get(type(target), 's'), target)]
        self.reader.bus.call_sync(self.service, path, 'org.gtk.Actions', 'Activate', GLib.Variant('(sava{sv})', (name, parameters, {})),
                                  None, Gio.DBusCallFlags.NONE, 3000, None)


class Accessible(Source):
    """The menu bar of the window in the accessibility tree; an entry is the path of child indices below it, found
    again when it opens or runs."""
    name = 'atspi'

    def __init__(self, reader, menubar):
        self.reader, self.menubar = reader, menubar

    def role(self, node):
        try:
            return self.reader.modules[0].Role(node.get_role()).value_nick.upper().replace('-', '_')
        except Exception:  # noqa: BLE001
            return ''

    def node(self, path):
        node = self.menubar
        for index in path:
            node = node.get_child_at_index(index)
            if node is None:
                raise ValueError('gone')
        return node

    def kids(self, node):
        try:
            return [node.get_child_at_index(index) for index in range(min(node.get_child_count(), 200))]
        except Exception:  # noqa: BLE001
            return []

    def popup(self, node, path):
        """Where the entries of a menu are: a popup child (GTK, Qt), or the menu itself (Firefox)."""
        children = self.kids(node)
        for index, child in enumerate(children):
            if child is not None and self.role(child) == 'POPUP_MENU':
                return child, path + [index]
        return node, path

    def describe(self, node, path):
        Atspi = self.reader.modules[0]
        role = self.role(node)
        if role == 'SEPARATOR':
            return {'id': 'a:sep', 'kind': 'separator'}
        if role not in ITEMS:
            return None
        text = item_label(node.get_name())
        if not text:
            return None
        try:
            states = node.get_state_set()
            enabled = states.contains(Atspi.StateType.ENABLED) or states.contains(Atspi.StateType.SENSITIVE)
            checked = states.contains(Atspi.StateType.CHECKED)
        except Exception:  # noqa: BLE001
            enabled, checked = True, False
        entry = {'id': 'a:' + '/'.join(map(str, path)), 'label': text, 'enabled': enabled}
        if role == 'MENU':
            entry['submenu'] = True
        elif role in ('CHECK_MENU_ITEM', 'RADIO_MENU_ITEM'):
            entry['checked'] = checked
        try:
            keys = shortcut_text(node.get_key_binding(0)) if node.get_n_actions() else ''
        except Exception:  # noqa: BLE001
            keys = ''
        if keys:
            entry['shortcut'] = keys
        return entry

    def list(self, parent, path):
        result = []
        for index, child in enumerate(self.kids(parent)):
            entry = self.describe(child, path + [index]) if child is not None else None
            if entry is None or entry.get('kind') == 'separator' and (not result or result[-1].get('kind') == 'separator'):
                continue
            result.append(entry)
        while result and result[-1].get('kind') == 'separator':
            result.pop()
        return result

    def menu(self):
        return [{'id': entry['id'], 'label': entry['label']} for entry in self.list(self.menubar, []) if entry.get('kind') != 'separator']

    def open(self, entry_id):
        path = [int(index) for index in entry_id[2:].split('/') if index != '']
        node = self.node(path)
        parent, parent_path = self.popup(node, path)
        items = self.list(parent, parent_path)
        if not items and node.get_n_actions():
            # Firefox fills a menu only once it has been open: opened in the app, read again a moment later, the
            # app's own copy closed (Escape to its window), and the entries sent on; from then on it opens at once.
            node.do_action(0)
            address = self.reader.current
            GLib = self.reader.modules[2]

            def again():
                found = self.list(*self.popup(node, path))
                if found:
                    # Twice: the first closes the menu, the second the menu bar Firefox shows while one is open.
                    self.reader.send_key(address, 'Escape')
                    self.reader.send_key(address, 'Escape')
                    self.reader.emit({'address': address, 'open': entry_id, 'items': found})
                return False

            GLib.timeout_add(500, again)
        return items

    def click(self, entry_id):
        node = self.node([int(index) for index in entry_id[2:].split('/') if index != ''])
        if node.get_n_actions():
            node.do_action(0)


class Reader:
    def __init__(self, modules):
        self.modules = modules
        Atspi, Gio, GLib = modules
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.windows = {}
        self.current = ''
        self.a11y = None
        self.registered = {}

    def emit(self, value):
        print(json.dumps(value), flush=True)

    def send_key(self, address, key):
        import subprocess
        subprocess.run(['hyprctl', 'dispatch', 'hl.dsp.send_shortcut({ mods = "", key = "%s", window = "address:%s" })' % (key, address)],
                       capture_output=True, timeout=2)

    # Accessibility on: registered as a listener of one event, as a screen reader is, while the reader runs.
    def enable_accessibility(self):
        _, Gio, GLib = self.modules
        try:
            if self.a11y is None or self.a11y.is_closed():
                address = self.bus.call_sync('org.a11y.Bus', '/org/a11y/bus', 'org.a11y.Bus', 'GetAddress', None, None,
                                             Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
                self.a11y = Gio.DBusConnection.new_for_address_sync(
                    address, Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
            self.a11y.call_sync('org.a11y.atspi.Registry', '/org/a11y/atspi/registry', 'org.a11y.atspi.Registry', 'RegisterEvent',
                                GLib.Variant('(sass)', ('object:state-changed:focused', [], self.a11y.get_unique_name())), None,
                                Gio.DBusCallFlags.NONE, 2000, None)
        except GLib.Error:
            self.a11y = None
        return True

    def names_of(self, pid):
        _, Gio, GLib = self.modules
        wanted = set(parents(pid))
        try:
            names = self.bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'ListNames', None, None,
                                       Gio.DBusCallFlags.NONE, 2000, None).unpack()[0]
        except GLib.Error:
            return []
        owned = []
        for name in names:
            if not name.startswith(':'):
                continue
            try:
                owner = self.bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'GetConnectionUnixProcessID',
                                           GLib.Variant('(s)', (name,)), None, Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            except GLib.Error:
                continue
            if owner in wanted:
                owned.append(name)
        return owned

    def introspect(self, service, path):
        _, Gio, GLib = self.modules
        try:
            return self.bus.call_sync(service, path, 'org.freedesktop.DBus.Introspectable', 'Introspect', None, None,
                                      Gio.DBusCallFlags.NONE, 500, None).unpack()[0]
        except GLib.Error:
            return ''

    def children_of(self, service, path):
        return re.findall(r'<node name="([^"/]+)"', self.introspect(service, path))

    def objects(self, service, interface, budget=40):
        """Object paths of service implementing interface, a bounded walk from /."""
        found, queue = [], ['/']
        while queue and budget > 0:
            path = queue.pop(0)
            budget -= 1
            xml = self.introspect(service, path)
            if 'interface name="' + interface + '"' in xml:
                found.append(path)
            queue += [path.rstrip('/') + '/' + child for child in re.findall(r'<node name="([^"/]+)"', xml)]
        return found

    def registrar_menu(self, window):
        _, Gio, GLib = self.modules
        try:
            listed = self.bus.call_sync(BUS, REGISTRAR, BUS, 'ListWindows', None, None, Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
        except GLib.Error:
            return None
        wanted = set(parents(window['pid'], 2))
        matches = []
        for xid, service, path in listed:
            try:
                owner = self.bus.call_sync('org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus', 'GetConnectionUnixProcessID',
                                           GLib.Variant('(s)', (service,)), None, Gio.DBusCallFlags.NONE, 1000, None).unpack()[0]
            except GLib.Error:
                continue
            if owner in wanted:
                matches.append((xid, service, path))
        if len(matches) > 1:
            # Windows of one process: the one whose title is this window's.
            for xid, service, path in matches:
                if norm(self.x11_title(xid)) == norm(window.get('title')):
                    return Dbusmenu(self, service, path)
        return Dbusmenu(self, matches[0][1], matches[0][2]) if matches else None

    def x11_title(self, xid):
        import subprocess
        try:
            out = subprocess.run(['xprop', '-id', hex(xid), '_NET_WM_NAME'], capture_output=True, text=True, timeout=2).stdout
        except (OSError, subprocess.SubprocessError):
            return ''
        found = re.search(r'= "(.*)"', out)
        return found[1] if found else ''

    def gtk_menu(self, window):
        for service in self.names_of(window['pid']):
            for app_path in self.objects(service, 'org.gtk.Application', 30):
                menubar = app_path.rstrip('/') + '/menus/menubar'
                if 'org.gtk.Menus' in self.introspect(service, menubar):
                    return GtkMenus(self, service, app_path, menubar)
        return None

    def own_dbusmenu(self, window):
        for service in self.names_of(window['pid']):
            for path in self.objects(service, MENU, 30):
                return Dbusmenu(self, service, path)
        return None

    def accessible_menu(self, window):
        Atspi = self.modules[0]
        try:
            desktop = Atspi.get_desktop(0)
            apps = [desktop.get_child_at_index(index) for index in range(desktop.get_child_count())]
        except Exception:  # noqa: BLE001
            return None
        wanted = set(parents(window['pid'], 2))
        source = None
        for app in apps:
            try:
                if app is None or app.get_process_id() not in wanted:
                    continue
            except Exception:  # noqa: BLE001
                continue
            probe = Accessible(self, None)
            frames = [child for child in probe.kids(app) if child is not None and probe.role(child) in FRAMES]
            title = norm(window.get('title'))
            # Two windows of one app have two frames: the one named as this window, else the longest name inside it.
            ordered = sorted(frames, key=lambda frame: (norm(frame.get_name()) != title, -len(norm(frame.get_name()))
                                                        if norm(frame.get_name()) and norm(frame.get_name()) in title else 0))
            for frame in ordered:
                menubar = self.find(probe, frame, 'MENU_BAR')
                if menubar is not None and probe.kids(menubar):
                    return Accessible(self, menubar)
        return source

    def find(self, probe, node, role, depth=0, budget=None):
        budget = budget if budget is not None else [400]
        if node is None or depth > 10 or budget[0] <= 0:
            return None
        budget[0] -= 1
        if probe.role(node) == role:
            return node
        for child in probe.kids(node):
            found = self.find(probe, child, role, depth + 1, budget)
            if found is not None:
                return found
        return None

    def source(self, window):
        if window.get('xwayland'):
            found = self.registrar_menu(window)
            if found:
                return found
        for finder in (self.gtk_menu, self.own_dbusmenu, self.accessible_menu):
            try:
                found = finder(window)
            except Exception:  # noqa: BLE001
                found = None
            if found:
                return found
        return None

    def handle(self, request):
        command, address = request.get('cmd'), str(request.get('address', ''))
        self.current = address
        if command == 'menu':
            source = self.source(request)
            top = []
            if source:
                try:
                    top = source.menu()
                except Exception:  # noqa: BLE001
                    source, top = None, []
            self.windows[address] = source if top else None
            self.emit({'address': address, 'source': source.name if source and top else 'none', 'menu': top})
        elif command == 'open':
            source = self.windows.get(address)
            self.emit({'address': address, 'open': request.get('id'), 'items': source.open(str(request.get('id'))) if source else []})
        elif command == 'click':
            source = self.windows.get(address)
            if source:
                source.click(str(request.get('id')))
        elif command == 'forget':
            self.windows.pop(address, None)


def run():
    modules = gi_modules()
    Atspi, Gio, GLib = modules
    reader = Reader(modules)
    reader.enable_accessibility()
    # Again now and then: the accessibility bus or its registry may have restarted.
    GLib.timeout_add_seconds(30, reader.enable_accessibility)

    def on_registered(connection, sender, path, interface, signal, parameters):
        reader.emit({'registered': True})

    reader.bus.signal_subscribe(None, BUS, 'WindowRegistered', REGISTRAR, None, Gio.DBusSignalFlags.NONE, on_registered)

    def on_line(channel, condition):
        line = sys.stdin.readline()
        if not line:
            loop.quit()
            return False
        try:
            reader.handle(json.loads(line))
        except Exception as error:  # noqa: BLE001
            reader.emit({'error': str(error)})
        return True

    GLib.io_add_watch(GLib.IOChannel.unix_new(sys.stdin.fileno()), GLib.PRIORITY_DEFAULT, GLib.IOCondition.IN | GLib.IOCondition.HUP, on_line)
    loop = GLib.MainLoop()
    loop.run()
