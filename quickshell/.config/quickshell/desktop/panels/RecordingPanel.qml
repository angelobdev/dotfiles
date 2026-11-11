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
    property bool area: ShellState.recall("recording/area", false)
    onAreaChanged: ShellState.remember("recording/area", area)
    property string audioMode: ShellState.recall("recording/audioMode", "none")
    onAudioModeChanged: ShellState.remember("recording/audioMode", audioMode)
    onOpened: monitor = ShellState.activeScreen?.name || Quickshell.screens[0]?.name || ""
    SidePanelCard {
        height: Math.min(460, parent.height - Theme.panelClearance)
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
                font.pixelSize: Theme.textSize(15)
            }
            RowLayout {
                visible: !Recording.running
                ActionButton {
                    text: I18n.tr("recording.display")
                    highlighted: !root.area
                    tone: "state"
                    onClicked: root.area = false
                }
                ActionButton {
                    text: I18n.tr("recording.area")
                    highlighted: root.area
                    tone: "state"
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
                        tone: "state"
                        onClicked: root.monitor = modelData.name
                    }
                }
            }
            Text {
                visible: !Recording.running
                text: I18n.tr("audio.title")
                color: Theme.muted
                font.pixelSize: Theme.textSize(12)
            }
            RowLayout {
                visible: !Recording.running
                ActionButton {
                    text: I18n.tr("recording.noAudio")
                    highlighted: root.audioMode === "none"
                    tone: "state"
                    onClicked: root.audioMode = "none"
                }
                ActionButton {
                    text: I18n.tr("audio.speaker")
                    highlighted: root.audioMode === "output"
                    tone: "state"
                    onClicked: root.audioMode = "output"
                }
                ActionButton {
                    text: I18n.tr("audio.microphone")
                    highlighted: root.audioMode === "input"
                    tone: "state"
                    onClicked: root.audioMode = "input"
                }
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: Recording.error || Recording.path || I18n.tr("recording.saveLocationHint")
                color: Recording.error ? Theme.danger : Theme.muted
                font.pixelSize: Theme.textSize(12)
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
