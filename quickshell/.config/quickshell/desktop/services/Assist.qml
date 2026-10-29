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
    // Every action the menu can offer; Config.assistPages groups and orders them. An action opens a panel,
    // sends a Hyprland dispatcher (to the active window, which the button never takes the focus from),
    // runs a command, or runs Lua in Hyprland once the menu has gone (screenshots); the others are below.
    readonly property var catalog: ({
            keyboard: {
                icon: "keyboard",
                label: I18n.tr("assist.actions.keyboard"),
                active: Keyboard.shown
            },
            assistant: {
                icon: "assistant",
                label: I18n.tr("assist.actions.assistant")
            },
            window: {
                icon: "window",
                label: I18n.tr("assist.actions.window")
            },
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
            },
            hints: {
                icon: "help",
                label: I18n.tr("assist.actions.hints"),
                panel: "hints"
            },
            windowClose: {
                icon: "close",
                label: I18n.tr("assist.actions.windowClose"),
                dispatch: "hl.dsp.window.close()"
            },
            windowFullscreen: {
                icon: "fullscreen",
                label: I18n.tr("assist.actions.windowFullscreen"),
                dispatch: "hl.dsp.window.fullscreen()"
            },
            windowFloating: {
                icon: "pip",
                label: I18n.tr("assist.actions.windowFloating"),
                dispatch: "hl.dsp.window.float({ action = \"toggle\" })"
            },
            windowLeft: {
                icon: "arrow-left",
                label: I18n.tr("assist.actions.windowLeft"),
                dispatch: "hl.dsp.window.move({ direction = \"left\" })"
            },
            windowRight: {
                icon: "arrow-right",
                label: I18n.tr("assist.actions.windowRight"),
                dispatch: "hl.dsp.window.move({ direction = \"right\" })"
            },
            windowToPrevious: {
                icon: "chevron-left",
                label: I18n.tr("assist.actions.windowToPrevious"),
                dispatch: "hl.dsp.window.move({ workspace = \"r-1\" })"
            },
            windowToNext: {
                icon: "chevron-right",
                label: I18n.tr("assist.actions.windowToNext"),
                dispatch: "hl.dsp.window.move({ workspace = \"r+1\" })"
            },
            windowSplit: {
                icon: "split",
                label: I18n.tr("assist.actions.windowSplit"),
                dispatch: "hl.dsp.layout(\"togglesplit\")"
            },
            screenshotArea: {
                icon: "screenshot",
                label: I18n.tr("assist.actions.screenshotArea"),
                lua: "local capture = (hl.plugin or {}).hyprcapture if capture then capture.open_editor(\"region\") end"
            },
            screenshotDisplay: {
                icon: "monitor",
                label: I18n.tr("assist.actions.screenshotDisplay"),
                lua: "local capture = (hl.plugin or {}).hyprcapture if capture then capture.open_editor(\"fullscreen\") end"
            },
            recording: {
                icon: "record",
                label: I18n.tr("assist.actions.recording"),
                panel: "recording"
            },
            clipboard: {
                icon: "clipboard",
                label: I18n.tr("assist.actions.clipboard"),
                panel: "clipboard"
            },
            theming: {
                icon: "palette",
                label: I18n.tr("assist.actions.theming"),
                panel: "theming"
            },
            wallpaper: {
                icon: "image",
                label: I18n.tr("assist.actions.wallpaper"),
                panel: "wallpaper"
            },
            nextWallpaper: {
                icon: "next",
                label: I18n.tr("assist.actions.nextWallpaper"),
                exec: [Quickshell.env("HOME") + "/.local/bin/desktop-wallpaper", "--next"]
            },
            lock: {
                icon: "lock",
                label: I18n.tr("assist.actions.lock"),
                exec: [Quickshell.env("HOME") + "/.local/bin/desktop-power", "lock"]
            },
            session: {
                icon: "power",
                label: I18n.tr("assist.actions.session"),
                panel: "power"
            }
        })
    // The pages of the menu, each with its available actions; page is the one shown (the first by default).
    readonly property var pages: Config.assistPages.map(page => ({
                name: page.name,
                actions: page.actions.filter((name, index, all) => catalog[name] && catalog[name].available !== false && all.indexOf(name) === index).map(name => Object.assign({
                            name: name
                        }, catalog[name]))
            })).filter(page => page.actions.length > 0)
    property string page: ""
    readonly property var currentPage: pages.find(p => p.name === page) ?? pages[0] ?? {
        name: "",
        actions: []
    }
    readonly property var actions: currentPage.actions
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
        const action = catalog[name];
        if (action?.panel) {
            ShellState.toggle(action.panel);
            return true;
        }
        if (action?.dispatch) {
            Hyprland.dispatch(action.dispatch);
            return true;
        }
        if (action?.exec) {
            Quickshell.execDetached(action.exec);
            return true;
        }
        if (action?.lua) {
            deferred.lua = action.lua;
            deferred.restart();
            return true;
        }
        if (name === "keyboard")
            Keyboard.request("toggle");
        else if (name === "window")
            ShellState.requestWindowMenu();
        else if (name === "assistant")
            Quickshell.execDetached([Quickshell.env("HOME") + "/.local/bin/desktop-ai"]);
        else if (name === "launcher" || name === "controls" || name === "notifications")
            ShellState.toggle(name);
        else if (name === "dock")
            Dock.request(Tablet.active ? "touch" : "toggle");
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
    // Lets the menu leave the screen before a screenshot editor captures it.
    Timer {
        id: deferred
        property string lua: ""
        interval: 250
        onTriggered: Quickshell.execDetached(["hyprctl", "eval", lua])
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
        // Read at once: a write before the first read would save the defaults over the saved values.
        blockLoading: true
        atomicWrites: true
        printErrors: false
        adapter: JsonAdapter {
            id: places
            property var positions: ({})
        }
    }
}
