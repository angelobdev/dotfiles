pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."
import "../bar/WorkspaceModel.js" as WorkspaceModel

// The floating assist button: a touch shortcut to the panels and actions of the shell. It appears with tablet
// mode and goes away with it; a three-finger long press or `desktop-shell assist` shows or hides it at any
// time, until the posture changes again. Its place is saved per monitor and orientation.
Singleton {
    id: root
    property bool shown: false
    property bool menuOpen: false
    readonly property string stateFile: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell/assist.json"
    // Every action the menu can offer; Config.assistActions picks and orders them.
    readonly property var catalog: ({
            launcher: {
                icon: "apps",
                label: I18n.tr("assist.actions.apps")
            },
            dock: {
                icon: "dock",
                label: I18n.tr("assist.actions.dock")
            },
            controls: {
                icon: "controls",
                label: I18n.tr("assist.actions.controls")
            },
            notifications: {
                icon: "bell",
                label: I18n.tr("assist.actions.notifications")
            },
            overview: {
                icon: "overview",
                label: I18n.tr("assist.actions.overview")
            },
            workspacePrevious: {
                icon: "chevron-left",
                label: I18n.tr("assist.actions.workspacePrevious")
            },
            workspaceNext: {
                icon: "chevron-right",
                label: I18n.tr("assist.actions.workspaceNext")
            },
            rotationLock: {
                icon: Tablet.locked ? "rotate-lock" : "rotate",
                label: I18n.tr("tablet.rotationLock"),
                available: Tablet.available,
                active: Tablet.locked
            }
        })
    readonly property var actions: Config.assistActions.filter((name, index, all) => catalog[name] && catalog[name].available !== false && all.indexOf(name) === index).map(name => Object.assign({
                name: name
            }, catalog[name]))
    function positionFor(key) {
        const saved = places.positions?.[key];
        return saved && ["left", "right"].includes(saved.side) && typeof saved.fraction === "number" ? {
            side: saved.side,
            fraction: saved.fraction
        } : {
            side: "right",
            fraction: 0.62
        };
    }
    function savePosition(key, position) {
        const positions = JSON.parse(JSON.stringify(places.positions ?? {}));
        positions[key] = position;
        places.positions = positions;
        placesFile.writeAdapter();
    }
    // IPC and the three-finger long press: "show", "hide" or "toggle"; "menu" shows it with the menu open.
    function request(action) {
        if (!["show", "hide", "toggle", "menu"].includes(action))
            return false;
        shown = action === "show" || action === "menu" || action === "toggle" && !shown;
        menuOpen = action === "menu";
        return true;
    }
    function run(name) {
        menuOpen = false;
        if (name === "launcher" || name === "controls" || name === "notifications")
            ShellState.toggle(name);
        else if (name === "dock")
            Dock.request("toggle");
        else if (name === "overview")
            Quickshell.execDetached(["hyprctl", "eval", "local overview = (hl.plugin or {}).overview if overview then overview.toggle() end"]);
        else if (name === "workspacePrevious" || name === "workspaceNext")
            stepWorkspace(name === "workspaceNext" ? 1 : -1);
        else if (name === "rotationLock")
            Tablet.requestLock("toggle");
        else
            return false;
        return true;
    }
    // Like scrolling over the bar: one slot along the workspaces of the focused monitor, empty ones included,
    // stopping at either end.
    function stepWorkspace(direction) {
        const monitor = Hyprland.focusedMonitor;
        if (!monitor)
            return;
        const slots = WorkspaceModel.build(Hyprland.workspaces.values.map(w => ({
                    id: w.id,
                    monitor: w.monitor?.name,
                    count: w.toplevels.values.length,
                    urgent: w.urgent
                })), Hyprland.monitors.values.map(m => ({
                    name: m.name,
                    activeId: m.activeWorkspace?.id
                })), Config.minimumWorkspaces)[monitor.name] || [];
        const current = slots.findIndex(w => w.id === monitor.activeWorkspace?.id);
        const next = current + direction;
        if (current >= 0 && next >= 0 && next < slots.length)
            Hyprland.dispatch("hl.dsp.focus({ workspace = " + slots[next].id + " })");
    }
    Connections {
        target: Tablet
        function onActiveChanged() {
            root.shown = Tablet.active;
            root.menuOpen = false;
        }
    }
    Component.onCompleted: shown = Tablet.active
    FileView {
        id: placesFile
        path: root.stateFile
        atomicWrites: true
        printErrors: false
        adapter: JsonAdapter {
            id: places
            property var positions: ({})
        }
    }
}
