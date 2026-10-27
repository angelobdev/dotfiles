import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

ControlTile {
    id: root
    property bool expanded: Config.expandAudioDevices
    implicitHeight: column.implicitHeight + 24
    ColumnLayout {
        id: column
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: 12
        }
        spacing: 4
        RowLayout {
            Text {
                text: I18n.tr("audio.sound")
                color: Theme.text
                font.pixelSize: 13
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
            Text {
                text: Audio.volume + "%"
                color: Theme.muted
                font.pixelSize: 12
            }
            CompactIconButton {
                iconName: "chevron-down"
                rotation: root.expanded ? 180 : 0
                tooltip: I18n.tr("audio.devices")
                implicitHeight: 26
                implicitWidth: 28
                onClicked: root.expanded = !root.expanded
            }
        }
        Text {
            text: Audio.sink?.description || I18n.tr("audio.noOutput")
            Layout.fillWidth: true
            elide: Text.ElideRight
            color: Theme.muted
            font.pixelSize: 11
            textFormat: Text.PlainText
        }
        RowLayout {
            CompactIconButton {
                implicitWidth: 30
                iconSize: 18
                iconName: Audio.muted ? "volume-muted" : "volume-high"
                tooltip: Audio.muted ? I18n.tr("audio.unmute") : I18n.tr("audio.mute")
                enabled: !!Audio.sink
                highlighted: Audio.muted
                onClicked: Audio.toggleMute()
            }
            ControlSlider {
                Layout.fillWidth: true
                value: Audio.volume / 100
                enabled: !!Audio.sink
                onMoved: Audio.setVolume(value)
                Accessible.name: I18n.tr("audio.outputVolume")
            }
        }
        ColumnLayout {
            visible: root.expanded
            Layout.fillWidth: true
            spacing: 4
            Text {
                text: I18n.tr("audio.outputsHeading")
                color: Theme.muted
                font.pixelSize: 10
                font.letterSpacing: 1
                Layout.topMargin: 6
            }
            Repeater {
                model: Audio.outputs
                ActionButton {
                    required property var modelData
                    Layout.fillWidth: true
                    alignLeft: true
                    implicitHeight: 34
                    font.pixelSize: 12
                    text: modelData.description || modelData.name
                    textElide: Text.ElideMiddle
                    tooltip: text
                    iconName: "volume-high"
                    iconSize: 16
                    highlighted: Audio.sink?.id === modelData.id
                    onClicked: Audio.selectOutput(modelData)
                }
            }
            Text {
                text: I18n.tr("audio.inputsHeading")
                color: Theme.muted
                font.pixelSize: 10
                font.letterSpacing: 1
                Layout.topMargin: 10
            }
            Repeater {
                model: Audio.inputs
                ActionButton {
                    required property var modelData
                    Layout.fillWidth: true
                    alignLeft: true
                    implicitHeight: 34
                    font.pixelSize: 12
                    text: modelData.description || modelData.name
                    textElide: Text.ElideMiddle
                    tooltip: text
                    iconName: "microphone"
                    iconSize: 16
                    highlighted: Audio.source?.id === modelData.id
                    onClicked: Audio.selectInput(modelData)
                }
            }
            RowLayout {
                CompactIconButton {
                    implicitWidth: 30
                    iconName: "microphone"
                    iconSize: 18
                    tooltip: I18n.tr("audio.toggleMicrophone")
                    enabled: !!Audio.source
                    highlighted: Audio.source?.audio?.muted ?? false
                    onClicked: Audio.toggleMic()
                }
                ControlSlider {
                    Layout.fillWidth: true
                    enabled: !!Audio.source
                    value: Audio.inputVolume / 100
                    onMoved: Audio.setInputVolume(value)
                    Accessible.name: I18n.tr("audio.inputVolume")
                }
                Text {
                    text: Audio.inputVolume + "%"
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
            ActionButton {
                text: I18n.tr("audio.openPanel")
                font.pixelSize: 12
                onClicked: ShellState.push("audio")
            }
        }
    }
}
