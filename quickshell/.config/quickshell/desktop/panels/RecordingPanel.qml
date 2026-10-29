import QtQuick
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"

Overlay {
    id: root
    panelName: "recording"
    property string monitor: ""
    property bool area: false
    property string audioMode: "none"
    onOpened: monitor = ShellState.activeScreen?.name || Quickshell.screens[0]?.name || ""
    SidePanelCard {
        height: Math.min(460, parent.height - 76)
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Theme.panelPadding
            spacing: 14
            PanelHeader {
                title: I18n.tr("recording.title")
                Layout.fillWidth: true
            }
            Text {
                text: Recording.running ? (Recording.stopping ? I18n.tr("recording.saving") : I18n.tr("recording.elapsed", [Recording.elapsed])) : I18n.tr("recording.chooseSource")
                color: Theme.text
                font.pixelSize: 15
            }
            RowLayout {
                visible: !Recording.running
                ActionButton {
                    text: I18n.tr("recording.display")
                    highlighted: !root.area
                    onClicked: root.area = false
                }
                ActionButton {
                    text: I18n.tr("recording.area")
                    highlighted: root.area
                    onClicked: root.area = true
                }
            }
            Flow {
                visible: !Recording.running && !root.area
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: Quickshell.screens
                    ActionButton {
                        required property var modelData
                        text: modelData.name
                        highlighted: root.monitor === modelData.name
                        onClicked: root.monitor = modelData.name
                    }
                }
            }
            Text {
                visible: !Recording.running
                text: I18n.tr("audio.title")
                color: Theme.muted
                font.pixelSize: 12
            }
            RowLayout {
                visible: !Recording.running
                ActionButton {
                    text: I18n.tr("recording.noAudio")
                    highlighted: root.audioMode === "none"
                    onClicked: root.audioMode = "none"
                }
                ActionButton {
                    text: I18n.tr("audio.speaker")
                    highlighted: root.audioMode === "output"
                    onClicked: root.audioMode = "output"
                }
                ActionButton {
                    text: I18n.tr("audio.microphone")
                    highlighted: root.audioMode === "input"
                    onClicked: root.audioMode = "input"
                }
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: Recording.error || Recording.path || I18n.tr("recording.saveLocationHint")
                color: Recording.error ? Theme.danger : Theme.muted
                font.pixelSize: 12
                textFormat: Text.PlainText
            }
            Item {
                Layout.fillHeight: true
            }
            ActionButton {
                Layout.fillWidth: true
                text: Recording.running ? I18n.tr("recording.stopAndSave") : I18n.tr("recording.start")
                iconName: Recording.running ? "stop" : "record"
                destructive: Recording.running
                highlighted: !Recording.running
                enabled: !Recording.stopping && !Recording.selecting && !!root.monitor
                onClicked: Recording.running ? Recording.stop() : Recording.start(root.monitor, root.area, root.audioMode)
            }
        }
    }
}
