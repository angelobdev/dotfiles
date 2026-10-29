pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import ".."

Singleton {
    id: root
    // Per-screen state keyed by monitor name; objects are replaced so bindings notice.
    property var requested: ({})
    property var peeks: ({})
    property var shown: ({})
    property var previousUrgent: []
    // Pinned entries in Config order, then running apps that are not pinned, in window creation order.
    readonly property var items: {
        const result = [];
        const byKey = {};
        DesktopEntries.applications.values; // Re-resolve once desktop entries finish loading.
        for (const id of Config.dockPinned) {
            const entry = DesktopEntries.byId(id);
            if (!entry || byKey[entry.id])
                continue;
            byKey[entry.id] = {
                key: entry.id,
                entry: entry,
                appId: entry.id,
                pinned: true,
                toplevels: []
            };
            result.push(byKey[entry.id]);
        }
        for (const toplevel of Hyprland.toplevels.values) {
            const appId = appIdOf(toplevel);
            if (appId === "")
                continue;
            // Window classes rarely equal desktop-entry IDs (zen → zen-browser).
            const entry = DesktopEntries.heuristicLookup(appId);
            const key = entry?.id ?? appId;
            if (!byKey[key]) {
                byKey[key] = {
                    key: key,
                    entry: entry,
                    appId: appId,
                    pinned: false,
                    toplevels: []
                };
                result.push(byKey[key]);
            }
            byKey[key].toplevels.push(toplevel);
        }
        const firstRunning = result.findIndex(item => !item.pinned);
        return result.map((item, index) => Object.assign(item, {
                separatorBefore: index > 0 && index === firstRunning,
                running: item.toplevels.length > 0,
                active: item.toplevels.some(t => t.activated),
                urgent: item.toplevels.some(t => t.urgent)
            }));
    }
    readonly property var urgentKeys: items.filter(item => item.urgent).map(item => item.key)
    function appIdOf(toplevel) {
        return toplevel.wayland?.appId || toplevel.lastIpcObject?.class || "";
    }
    function focusedName() {
        return Hyprland.focusedMonitor?.name ?? "";
    }
    function assigned(map, name, value) {
        const copy = Object.assign({}, map);
        if (value === undefined)
            delete copy[name];
        else
            copy[name] = value;
        return copy;
    }
    // show/hide/toggle on the focused monitor. true forces the dock up, false keeps it down even on an
    // empty workspace; either lasts until the pointer has visited the dock or an item is activated.
    function request(action) {
        const name = focusedName();
        if (name === "" || !["show", "hide", "toggle"].includes(action))
            return false;
        const visible = action === "show" || action === "toggle" && !shown[name];
        requested = assigned(requested, name, visible);
        if (!visible)
            peeks = assigned(peeks, name, undefined);
        return true;
    }
    function release(name) {
        requested = assigned(requested, name, undefined);
    }
    function peek(name, duration) {
        if (name === "")
            return;
        peeks = assigned(peeks, name, Date.now() + duration);
        peekClock.restart();
    }
    function setShown(name, value) {
        if (!!shown[name] !== value)
            shown = assigned(shown, name, value ? true : undefined);
    }
    function activate(item) {
        requested = ({});
        if (!item.running) {
            Apps.launch(item.entry);
            return;
        }
        const windows = item.toplevels;
        const current = windows.findIndex(t => t.activated);
        // A second click on the focused app cycles through its windows.
        const target = current === -1 ? preferred(windows) : windows[(current + 1) % windows.length];
        if (target.wayland)
            target.wayland.activate();
        else if (target.workspace)
            Hyprland.dispatch("hl.dsp.focus({ workspace = " + target.workspace.id + " })");
    }
    // Prefer a window already visible on the focused monitor so focusing does not switch workspaces.
    function preferred(windows) {
        const workspace = Hyprland.focusedMonitor?.activeWorkspace;
        return windows.find(t => t.workspace === workspace) ?? windows[0];
    }
    function launchNew(item) {
        if (item.entry)
            Apps.launch(item.entry);
    }
    function launchIndex(index) {
        const item = items[index - 1];
        if (!item)
            return false;
        activate(item);
        peek(focusedName(), 1000);
        return true;
    }
    onUrgentKeysChanged: {
        for (const key of urgentKeys) {
            if (previousUrgent.includes(key))
                continue;
            const item = items.find(i => i.key === key);
            const window = item?.toplevels.find(t => t.urgent);
            peek(window?.monitor?.name ?? focusedName(), 3000);
        }
        previousUrgent = urgentKeys;
    }
    Timer {
        id: peekClock
        interval: 100
        repeat: true
        onTriggered: {
            const now = Date.now();
            const remaining = {};
            for (const name in root.peeks) {
                if (root.peeks[name] > now)
                    remaining[name] = root.peeks[name];
            }
            if (Object.keys(remaining).length !== Object.keys(root.peeks).length)
                root.peeks = remaining;
            if (Object.keys(remaining).length === 0)
                stop();
        }
    }
}
