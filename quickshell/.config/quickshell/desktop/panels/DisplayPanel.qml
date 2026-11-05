import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."
import "../components"
import "../services"

// Displays (Super + P, the F1 key of the OmniBook): the connected monitors, and how the others sit with the
// laptop panel: extended beside it, mirroring it, alone (panel off) or off. config/tablet.lua applies the mode
// and keeps it; with one monitor the modes wait for another.
Overlay {
    id: root
    panelName: "displays"
    dialog: true
    property var monitors: []
    property string mode: "extend"
    readonly property bool several: monitors.filter(m => m.name !== "FALLBACK").length > 1
    function choose(name) {
        mode = name;
        Quickshell.execDetached(["hyprctl", "eval", "desktop_display_mode(\"" + name + "\")"]);
        refresh.restart();
    }
    onOpened: {
        lister.running = true;
        state.reload();
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (root.visible && (event.name === "monitoraddedv2" || event.name === "monitorremovedv2" || event.name === "monitoradded" || event.name === "monitorremoved"))
                refresh.restart();
        }
    }
    Timer {
        id: refresh
        interval: 400
        onTriggered: lister.running = true
    }
    Process {
        id: lister
        command: ["hyprctl", "monitors", "all", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.monitors = JSON.parse(text);
                } catch (failure) {}
            }
        }
    }
    FileView {
        id: state
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session/display.lua"
        printErrors: false
        onLoaded: root.mode = (text().match(/mode\s*=\s*"(\w+)"/) ?? [])[1] ?? "extend"
        onLoadFailed: root.mode = "extend"
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(520, parent.width - 48)
        height: column.implicitHeight + 2 * Theme.dialogPadding
        ColumnLayout {
            id: column
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: Theme.dialogPadding
            }
            spacing: 14
            PanelHeader {
                title: I18n.tr("displays.title")
                Layout.fillWidth: true
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
                            text: modelData.name + (modelData.model ? " · " + modelData.model : "")
                            textFormat: Text.PlainText
                            color: Theme.text
                            elide: Text.ElideRight
                        }
                        Text {
                            Layout.fillWidth: true
                            text: modelData.disabled ? I18n.tr("displays.off") : I18n.tr("displays.details", [modelData.width, modelData.height, Math.round(modelData.refreshRate), Math.round(modelData.scale * 100)]) + (modelData.mirrorOf && modelData.mirrorOf !== "none" ? " · " + I18n.tr("displays.mirroring") : "")
                            color: Theme.muted
                            font.pixelSize: Theme.textSize(12)
                            elide: Text.ElideRight
                        }
                    }
                }
            }
            ChoiceChips {
                Layout.fillWidth: true
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
            Text {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: root.several ? I18n.tr("displays.hint") : I18n.tr("displays.single")
                color: Theme.muted
                font.pixelSize: Theme.textSize(12)
            }
        }
    }
}
