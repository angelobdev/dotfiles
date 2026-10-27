import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

Overlay {
    panelName: "audio"
    dialog: true
    Card {
        anchors.centerIn: parent
        width: Math.min(620, parent.width - 48)
        height: Math.min(640, parent.height - 96)
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 14
            Heading {
                text: I18n.tr("audio.panelTitle")
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: availableWidth
                clip: true
                ColumnLayout {
                    width: parent.width
                    spacing: 12
                    Heading {
                        text: I18n.tr("audio.output")
                    }
                    RowLayout {
                        ActionButton {
                            iconName: Audio.muted ? "volume-muted" : "volume-high"
                            tooltip: I18n.tr("audio.toggleMute")
                            enabled: !!Audio.sink
                            highlighted: Audio.muted
                            onClicked: Audio.toggleMute()
                        }
                        ControlSlider {
                            Layout.fillWidth: true
                            Accessible.name: I18n.tr("audio.volume")
                            value: Audio.volume / 100
                            enabled: !!Audio.sink
                            onMoved: Audio.setVolume(value)
                        }
                        Text {
                            text: Audio.volume + "%"
                            color: Theme.text
                            Layout.preferredWidth: 44
                        }
                    }
                    Repeater {
                        model: Audio.outputs
                        ActionButton {
                            required property var modelData
                            Layout.fillWidth: true
                            alignLeft: true
                            implicitHeight: 42
                            text: modelData.description || modelData.name
                            textElide: Text.ElideMiddle
                            iconName: "volume-high"
                            highlighted: Audio.sink?.id === modelData.id
                            tooltip: modelData.name
                            onClicked: Audio.selectOutput(modelData)
                        }
                    }
                    Text {
                        visible: Audio.outputs.length === 0
                        text: I18n.tr("audio.noOutputs")
                        color: Theme.muted
                    }
                    Heading {
                        text: I18n.tr("audio.input")
                        Layout.topMargin: 12
                    }
                    RowLayout {
                        ActionButton {
                            iconName: Audio.source?.audio?.muted ? "microphone-muted" : "microphone"
                            tooltip: I18n.tr("audio.toggleMicrophone")
                            enabled: !!Audio.source
                            highlighted: Audio.source?.audio?.muted ?? false
                            onClicked: Audio.toggleMic()
                        }
                        ControlSlider {
                            Layout.fillWidth: true
                            Accessible.name: I18n.tr("audio.microphone")
                            value: Audio.inputVolume / 100
                            enabled: !!Audio.source
                            onMoved: Audio.setInputVolume(value)
                        }
                        Text {
                            text: Audio.inputVolume + "%"
                            color: Theme.text
                            Layout.preferredWidth: 44
                        }
                    }
                    Repeater {
                        model: Audio.inputs
                        ActionButton {
                            required property var modelData
                            Layout.fillWidth: true
                            alignLeft: true
                            implicitHeight: 42
                            text: modelData.description || modelData.name
                            textElide: Text.ElideMiddle
                            iconName: "microphone"
                            highlighted: Audio.source?.id === modelData.id
                            tooltip: modelData.name
                            onClicked: Audio.selectInput(modelData)
                        }
                    }
                    Text {
                        visible: Audio.inputs.length === 0
                        text: I18n.tr("audio.noInputs")
                        color: Theme.muted
                    }
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        text: I18n.tr("audio.routingHint")
                        color: Theme.muted
                        font.pixelSize: 12
                    }
                }
            }
            RowLayout {
                ActionButton {
                    iconName: "arrow-left"
                    text: I18n.tr("controlCenter.title")
                    onClicked: ShellState.back()
                }
                Item {
                    Layout.fillWidth: true
                }
                ActionButton {
                    text: I18n.tr("common.close")
                    onClicked: ShellState.close()
                }
            }
        }
    }
}
