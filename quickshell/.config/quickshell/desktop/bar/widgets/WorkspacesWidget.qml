import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import "../.."
import ".."
import "../WorkspaceModel.js" as WorkspaceModel

WorkspaceStrip {
    id: root
    property var bar
    property bool shown: true
    // The strip takes the full bar height, so the wheel works anywhere above and below the pills.
    readonly property bool fillHeight: true
    readonly property var slots: WorkspaceModel.fromHyprland(Hyprland, Config.minimumWorkspaces)
    workspaces: slots[root.bar.screen.name] || []
    activeId: root.bar.monitor?.activeWorkspace?.id ?? -1
    newId: WorkspaceModel.newId(slots, root.bar.screen.name)
    scrollEnabled: Config.workspaceScroll
    // The layout of each workspace not on tiling (config/workspace_layouts.lua): its file, then its events.
    layouts: layoutsFile.modes
    // A click on the workspace already focused changes its layout.
    onActivated: id => {
        if (id === activeId)
            Quickshell.execDetached(["hyprctl", "eval", "if desktop_workspace_layout_cycle then desktop_workspace_layout_cycle() end"]);
        else
            root.bar.focusWorkspace(id);
    }
    FileView {
        id: layoutsFile
        property var modes: ({})
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session/workspace-layouts.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                const value = JSON.parse(text());
                modes = value && typeof value === "object" ? value : {};
            } catch (failure) {
                modes = {};
            }
        }
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name !== "custom" || !event.data.startsWith("desktop-workspace-layout "))
                return;
            const words = event.data.split(" ");
            const next = Object.assign({}, layoutsFile.modes);
            if (words[2] === "dwindle")
                delete next[words[1]];
            else
                next[words[1]] = words[2];
            layoutsFile.modes = next;
        }
    }
}
