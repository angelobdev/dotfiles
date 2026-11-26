import QtQuick
import Quickshell.Hyprland
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
    onActivated: id => root.bar.focusWorkspace(id)
}
