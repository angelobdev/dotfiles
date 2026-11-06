import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import ".."
import "../components"
import "../services"

// Alt + Tab: the windows from the most recently used, as thumbnails on the focused monitor. Hyprland drives it
// (binds.lua: a submap holds Tab, Shift + Tab, Escape and the Alt release while it is open), so the app keeps
// the keyboard and the shell only draws; a click on a thumbnail picks it.
PanelWindow {
    id: root
    property bool open: false
    property int selected: 0
    property var windows: []
    // Window addresses, the focused one first: Hyprland reports no focus order to Quickshell.
    property var recent: []
    // Each bind runs its own desktop-shell process, so a quick Alt + Tab can deliver the Alt release before
    // the Tab that opens the switcher: an end that comes first is kept for a moment and applied on opening.
    property string early: ""
    property real earlyAt: 0

    function candidates() {
        const all = Hyprland.toplevels.values.filter(t => !(t.workspace?.name ?? "").startsWith("special:"));
        const rank = t => {
            const index = recent.indexOf(t.address);
            return index === -1 ? recent.length : index;
        };
        return all.slice().sort((a, b) => rank(a) - rank(b));
    }
    function request(action) {
        if (action === "next" || action === "previous") {
            if (!open) {
                if (Date.now() - earlyAt >= 1000)
                    early = "";
                windows = candidates();
                if (windows.length === 0) {
                    // Nothing to switch to: leave the submap rather than wait for the Alt release.
                    Quickshell.execDetached(["hyprctl", "dispatch", "hl.dsp.submap(\"reset\")"]);
                    return false;
                }
                // The first press already moves off the focused window, as everywhere else.
                selected = windows.length === 1 ? 0 : action === "next" ? 1 : windows.length - 1;
                if (early !== "" && Date.now() - earlyAt < 1000) {
                    const end = early;
                    early = "";
                    return end === "commit" ? commit(selected) : true;
                }
                screen = ShellState.screenNamed(Hyprland.focusedMonitor?.name);
                open = true;
            } else if (windows.length > 0) {
                selected = (selected + (action === "next" ? 1 : -1) + windows.length) % windows.length;
            }
            idle.restart();
            return true;
        }
        if ((action === "commit" || action === "cancel") && !open) {
            early = action;
            earlyAt = Date.now();
            return true;
        }
        if (action === "commit")
            return commit(selected);
        if (action === "cancel") {
            close();
            return true;
        }
        return false;
    }
    // Focused through Hyprland once the switcher surface is gone: unmapping it makes Hyprland refocus the
    // window under the pointer (follow_mouse), which took the keyboard back from a window activated before.
    // The dispatcher also moves the pointer onto the window, so that refocus agrees with it.
    function commit(index) {
        const target = windows[index];
        close();
        if (!target?.address)
            return false;
        focusLater.address = target.address.startsWith("0x") ? target.address : "0x" + target.address;
        focusLater.restart();
        return true;
    }
    function close() {
        open = false;
        idle.stop();
        windows = [];
    }

    visible: open
    screen: Quickshell.screens[0]
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-overlay"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None

    Connections {
        target: Hyprland
        function onActiveToplevelChanged() {
            const address = Hyprland.activeToplevel?.address;
            if (address)
                root.recent = [address].concat(root.recent.filter(a => a !== address)).slice(0, 64);
        }
    }
    Timer {
        id: focusLater
        property string address: ""
        interval: 60
        onTriggered: Hyprland.dispatch("hl.dsp.focus({ window = \"address:" + address + "\" })")
    }
    // A switcher left open (the Alt release lost to a lock screen, say) commits by itself instead of staying up.
    Timer {
        id: idle
        interval: 10000
        onTriggered: {
            Quickshell.execDetached(["hyprctl", "dispatch", "hl.dsp.submap(\"reset\")"]);
            root.request("commit");
        }
    }
    MouseArea {
        anchors.fill: parent
        onPressed: {
            Quickshell.execDetached(["hyprctl", "dispatch", "hl.dsp.submap(\"reset\")"]);
            root.close();
        }
    }
    Card {
        id: card
        anchors.centerIn: parent
        readonly property int columns: Math.max(1, Math.min(root.windows.length, Math.floor((root.width - 96) / 236)))
        width: grid.implicitWidth + 2 * Theme.dialogPadding
        height: grid.implicitHeight + 2 * Theme.dialogPadding
        opacity: root.open ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.reduceMotion ? 0 : 90
            }
        }
        GridLayout {
            id: grid
            anchors.centerIn: parent
            columns: card.columns
            rowSpacing: 12
            columnSpacing: 12
            Repeater {
                model: root.windows
                Rectangle {
                    id: item
                    required property var modelData
                    required property int index
                    readonly property bool current: index === root.selected
                    readonly property string appId: Dock.appIdOf(modelData)
                    implicitWidth: 224
                    implicitHeight: 176
                    radius: Theme.corner(12)
                    color: current ? Theme.raised : "transparent"
                    border.color: current ? Theme.accent : "transparent"
                    border.width: 2
                    Accessible.role: Accessible.Button
                    Accessible.name: modelData.title || appId
                    ColumnLayout {
                        anchors {
                            fill: parent
                            margins: 8
                        }
                        spacing: 6
                        Item {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            ScreencopyView {
                                anchors.centerIn: parent
                                width: Math.min(parent.width, implicitWidth)
                                height: Math.min(parent.height, implicitHeight)
                                captureSource: root.open ? item.modelData.wayland : null
                                live: false
                                constraintSize: Qt.size(parent.width, parent.height)
                            }
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Image {
                                Layout.preferredWidth: 18
                                Layout.preferredHeight: 18
                                sourceSize: Qt.size(36, 36)
                                source: Quickshell.iconPath(DesktopEntries.heuristicLookup(item.appId)?.icon || item.appId, "application-x-executable")
                            }
                            Text {
                                Layout.fillWidth: true
                                text: item.modelData.title || item.appId
                                textFormat: Text.PlainText
                                color: Theme.text
                                font.pixelSize: Theme.textSize(12)
                                elide: Text.ElideRight
                            }
                        }
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            Quickshell.execDetached(["hyprctl", "dispatch", "hl.dsp.submap(\"reset\")"]);
                            root.commit(item.index);
                        }
                    }
                }
            }
        }
    }
}
