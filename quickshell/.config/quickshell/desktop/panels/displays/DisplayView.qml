import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import "../.."
import "../../components"
import "../../services"

// Displays: the connected monitors, and how the others sit with the laptop panel: extended beside it,
// mirroring it, alone (panel off) or off. config/displays.lua applies the mode and keeps it; with one monitor
// the modes wait for another, and a computer without a panel has none. The Displays panel (Super + P) and
// Settings → Displays both show it.
ColumnLayout {
    id: root
    // On screen: the monitors are listed again each time it shows.
    property bool shown: false
    readonly property Item focusItem: root
    spacing: 14
    readonly property var monitors: HyprSettings.monitorList
    property string mode: "extend"
    readonly property bool several: monitors.filter(m => m.name !== "FALLBACK").length > 1
    // The same names config/displays.lua looks for.
    readonly property bool laptop: monitors.some(m => HyprSettings.isPanel(m.name))
    function choose(name) {
        mode = name;
        Quickshell.execDetached(["hyprctl", "eval", "desktop_display_mode(\"" + name + "\")"]);
        refresh.restart();
    }
    function update() {
        HyprSettings.listMonitors();
        state.reload();
    }
    // A panel created open sets shown before any change is seen, hence both.
    onShownChanged: if (shown)
        update()
    Component.onCompleted: if (shown)
        update()
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (root.shown && (event.name === "monitoraddedv2" || event.name === "monitorremovedv2" || event.name === "monitoradded" || event.name === "monitorremoved"))
                refresh.restart();
        }
    }
    Timer {
        id: refresh
        interval: 400
        onTriggered: HyprSettings.listMonitors()
    }
    FileView {
        id: state
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session/display.lua"
        printErrors: false
        onLoaded: root.mode = (text().match(/mode\s*=\s*"(\w+)"/) ?? [])[1] ?? "extend"
        onLoadFailed: root.mode = "extend"
    }
    Repeater {
        model: root.monitors.filter(m => m.name !== "FALLBACK")
        RowLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: 12
            Icon {
                name: "monitor"
                color: modelData.disabled ? Theme.muted : Theme.text
                Layout.preferredWidth: 22
                Layout.preferredHeight: 22
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: HyprSettings.displayName(modelData.name)
                    textFormat: Text.PlainText
                    color: Theme.text
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    // The connector, then the mode.
                    text: modelData.name + " · " + (modelData.disabled ? I18n.tr("displays.off") : I18n.tr("displays.details", [modelData.width, modelData.height, Math.round(modelData.refreshRate), Math.round(modelData.scale * 100)]) + (modelData.mirrorOf && modelData.mirrorOf !== "none" ? " · " + I18n.tr("displays.mirroring") : ""))
                    textFormat: Text.PlainText
                    color: Theme.muted
                    font.pixelSize: Theme.textSize(12)
                    elide: Text.ElideRight
                }
            }
        }
    }
    ChoiceChips {
        Layout.fillWidth: true
        visible: root.laptop
        enabled: root.several
        options: [
            {
                name: "extend",
                label: I18n.tr("displays.modes.extend")
            },
            {
                name: "mirror",
                label: I18n.tr("displays.modes.mirror")
            },
            {
                name: "external",
                label: I18n.tr("displays.modes.external")
            },
            {
                name: "internal",
                label: I18n.tr("displays.modes.internal")
            }
        ]
        current: root.mode
        onChosen: name => root.choose(name)
    }
    // What the chosen mode does.
    Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: !root.laptop ? I18n.tr("displays.noPanel") : !root.several ? I18n.tr("displays.single") : I18n.tr({
            "mirror": "displays.hints.mirror",
            "external": "displays.hints.external",
            "internal": "displays.hints.internal"
        }[root.mode] ?? "displays.hints.extend")
        color: Theme.muted
        font.pixelSize: Theme.textSize(12)
    }
}
