pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."

// The global menu of the bar (bar/widgets/GlobalMenuWidget.qml), after Oma Top Menu: each monitor shows the menu of
// its window (the focused window on the focused monitor; elsewhere the window last used on the workspace it shows).
// The menu of a window is the one of its app, read by globalmenu.py watch (the registrar for X11 apps, org.gtk.Menus,
// dbusmenu, the accessibility tree), or a generic one the shell builds (bar/GlobalMenuWindow.qml). All of it runs
// only while the widget is on a bar: the registrar service (desktop-globalmenu.service), the reader (which keeps
// accessibility on), the apps chosen for it under X11, and the focus option.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/globalmenu.py"
    // The widget is on a bar (the saved layout, not a draft being edited).
    readonly property bool placed: Object.values(BarLayout.saved).some(ids => Array.isArray(ids) && ids.includes("globalMenu"))
    // Monitor name -> its window ({address, class, title, pid, xwayland, floating}), absent for an empty one.
    property var targets: ({})
    // Window address -> what the reader answered: {source, menu: [{id, label}], key (class and title asked about)}.
    property var menus: ({})
    signal opened(string address, string id, var items)

    function target(screenName) {
        return targets[screenName] ?? null;
    }
    function menuOf(window) {
        return window ? menus[window.address] ?? null : null;
    }
    function entryOf(window) {
        return window && window.class ? DesktopEntries.heuristicLookup(window.class) : null;
    }
    function nameOf(window) {
        return entryOf(window)?.name ?? window?.class ?? "";
    }
    function send(request) {
        if (reader.running)
            reader.write(JSON.stringify(request) + "\n");
    }
    // The entries of a menu of a window; opened(address, id, items) answers (twice for a menu an app fills late).
    function open(window, id) {
        send({
            cmd: "open",
            address: window.address,
            id: id
        });
    }
    // An entry runs once the menu has closed and the app has its keyboard back: an Electron app runs a command only
    // in its focused window.
    function click(window, id) {
        clickDelay.pending = {
            cmd: "click",
            address: window.address,
            id: id
        };
        clickDelay.restart();
    }
    Timer {
        id: clickDelay
        property var pending: null
        interval: 150
        onTriggered: if (pending)
            root.send(pending)
    }
    // Every window of an app closes (the generic menu: Quit).
    function closeAll(window) {
        for (const client of clients)
            if (client.class === window.class)
                Hyprland.dispatch("hl.dsp.window.close({ window = \"address:" + client.address + "\" })");
    }

    // Started once at login with the widget there. Added later, the apps to start under X11 are asked for by
    // BarLayout.save, where the user places it: here the layout of shell.json can arrive after the start.
    property bool ready: false
    Component.onCompleted: {
        sync();
        ready = true;
        refresh();
    }
    onPlacedChanged: sync()
    // At start only started: the registrar keeps the menus of the apps already open, so a shell restart must never
    // stop it; it stops when the widget leaves the bar.
    function sync() {
        if (placed || ready)
            Quickshell.execDetached(["systemctl", "--user", placed ? "start" : "stop", "desktop-globalmenu.service"]);
        // The apps chosen for it go back to Wayland without it, their settings as they were (and to X11 with it
        // again).
        if (ready)
            Quickshell.execDetached(["python3", helper, "apply"]);
        if (!placed)
            menus = {};
        applyFocus();
        refresh();
    }
    // The focus option: the live input:follow_mouse of Hyprland, again after every reload of its config.
    readonly property var followMouse: ({
            hover: 1,
            click: 2,
            off: 0
        })
    function applyFocus() {
        const value = followMouse[Config.globalMenuFocus];
        if (placed && value !== undefined)
            Quickshell.execDetached(["hyprctl", "eval", "hl.config({ input = { follow_mouse = " + value + " } })"]);
    }
    Connections {
        target: Config
        function onGlobalMenuFocusChanged() {
            root.applyFocus();
        }
    }

    // The windows of every monitor, from Hyprland, read again a moment after each change.
    property var clients: []
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "configreloaded")
                root.applyFocus();
            if (["activewindowv2", "openwindow", "closewindow", "movewindowv2", "workspacev2", "focusedmonv2", "windowtitlev2", "changefloatingmode", "fullscreen", "configreloaded"].includes(event.name))
                refreshDelay.restart();
        }
    }
    Timer {
        id: refreshDelay
        interval: 80
        onTriggered: root.refresh()
    }
    function refresh() {
        if (!placed)
            return;
        if (windowReader.running)
            windowReader.again = true;
        else
            windowReader.running = true;
    }
    Process {
        id: windowReader
        property bool again: false
        command: ["sh", "-c", "hyprctl -j clients; echo; echo @@@; hyprctl -j monitors; echo; echo @@@; hyprctl -j activewindow"]
        stdout: StdioCollector {
            onStreamFinished: {
                const parts = text.split("\n@@@\n");
                try {
                    root.plan(JSON.parse(parts[0]), JSON.parse(parts[1]), JSON.parse(parts[2] || "{}"));
                } catch (failure) {}
            }
        }
        onExited: if (again) {
            again = false;
            running = true;
        }
    }
    // The window of each monitor, and a menu asked for each one whose app or title changed.
    function plan(all, monitors, active) {
        clients = all.filter(client => client.mapped !== false && ((client.workspace?.id ?? -1) > 0 || client.address === active.address));
        const next = {};
        for (const monitor of monitors) {
            let window = null;
            if (monitor.focused && active.address)
                window = clients.find(client => client.address === active.address) ?? null;
            if (!window) {
                // Elsewhere, the window last used on the workspace it shows.
                const shown = clients.filter(client => client.workspace?.id === monitor.activeWorkspace?.id && client.monitor === monitor.id);
                shown.sort((a, b) => a.focusHistoryID - b.focusHistoryID);
                window = shown[0] ?? null;
            }
            if (window)
                next[monitor.name] = {
                    address: window.address,
                    class: window.class ?? "",
                    title: window.title ?? "",
                    pid: window.pid ?? 0,
                    xwayland: window.xwayland === true,
                    floating: window.floating === true
                };
        }
        targets = next;
        for (const name in next) {
            const window = next[name];
            const key = window.class + "\n" + window.title;
            if (menus[window.address]?.key !== key)
                ask(window, key);
        }
        // Windows gone: their menus too.
        const kept = {};
        for (const address in menus)
            if (clients.some(client => client.address === address))
                kept[address] = menus[address];
        if (Object.keys(kept).length !== Object.keys(menus).length)
            menus = kept;
    }
    function ask(window, key) {
        const next = Object.assign({}, menus);
        next[window.address] = Object.assign({}, menus[window.address] ?? {
            source: "",
            menu: []
        }, {
            key: key
        });
        menus = next;
        send({
            cmd: "menu",
            address: window.address,
            pid: window.pid,
            xwayland: window.xwayland,
            title: window.title
        });
    }

    Process {
        id: reader
        running: root.placed
        command: ["python3", root.helper, "watch"]
        stdinEnabled: true
        onRunningChanged: {
            if (running) {
                root.menus = {};
                root.refresh();
            }
        }
        stdout: SplitParser {
            onRead: line => {
                let value;
                try {
                    value = JSON.parse(line);
                } catch (failure) {
                    return;
                }
                if (value.registered) {
                    // An X11 app registered a menu: the windows of X11 apps are asked again.
                    const next = Object.assign({}, root.menus);
                    for (const name in root.targets)
                        if (root.targets[name].xwayland)
                            delete next[root.targets[name].address];
                    root.menus = next;
                    root.refresh();
                } else if (Array.isArray(value.menu)) {
                    const next = Object.assign({}, root.menus);
                    next[value.address] = {
                        source: value.source,
                        menu: value.menu,
                        key: root.menus[value.address]?.key ?? ""
                    };
                    root.menus = next;
                } else if (value.open !== undefined) {
                    root.opened(value.address, String(value.open), value.items ?? []);
                }
            }
        }
        // A reader that stops (the registrar restarted) starts again while the widget is there.
        onExited: if (root.placed)
            restartTimer.restart()
    }
    Timer {
        id: restartTimer
        interval: 2000
        onTriggered: if (root.placed && !reader.running)
            reader.running = true
    }
}
