import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import "../.."
import "../../components"
import "../../services"

// Sound: output volume and device, per-app volumes, input volume and device. The Sound panel of the Control
// Center and Settings → Sound both show it.
Item {
    id: root
    readonly property Item focusItem: root
    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true
        ColumnLayout {
            width: parent.width
            spacing: 6
            Heading {
                text: I18n.tr("audio.output")
                section: true
            }
            // Each section is a card, as on the option pages. The device rows nearly fill it, so their highlight
            // reads as a row; plain text lines up with the icons of the rows.
            GroupCard {
                Layout.fillWidth: true
                verticalPadding: 6
                leftPadding: 6
                rightPadding: 6
                spacing: 2
                RowLayout {
                    Layout.fillWidth: true
                    ActionButton {
                        iconName: Audio.muted ? "volume-muted" : "volume-high"
                        tooltip: I18n.tr("audio.toggleMute")
                        enabled: !!Audio.sink
                        highlighted: Audio.muted
                        tone: "state"
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
                        implicitHeight: Theme.hit(42)
                        text: Audio.deviceName(modelData)
                        textElide: Text.ElideMiddle
                        iconName: "volume-high"
                        // An HDMI or DisplayPort output with nothing plugged in.
                        normalColor: Audio.absent(modelData) ? Theme.muted : Theme.text
                        highlighted: Audio.sink?.id === modelData.id
                        tone: "state"
                        tooltip: Audio.deviceDetails(modelData)
                        onClicked: Audio.selectOutput(modelData)
                    }
                }
                Text {
                    visible: Audio.outputs.length === 0
                    Layout.leftMargin: 12
                    text: I18n.tr("audio.noOutputs")
                    color: Theme.muted
                }
            }
            Heading {
                visible: Audio.streams.length > 0
                text: I18n.tr("audio.applications")
                section: true
                Layout.topMargin: 12
            }
            GroupCard {
                Layout.fillWidth: true
                visible: Audio.streams.length > 0
                verticalPadding: 6
                leftPadding: 6
                rightPadding: 6
                spacing: 2
                Repeater {
                    model: Audio.streams
                    RowLayout {
                        id: stream
                        required property var modelData
                        readonly property string appName: Audio.streamName(modelData)
                        Layout.fillWidth: true
                        spacing: 8
                        Image {
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                            sourceSize: Qt.size(44, 44)
                            source: Quickshell.iconPath(Audio.streamIcon(stream.modelData), "audio-x-generic")
                        }
                        Text {
                            Layout.preferredWidth: 140
                            text: stream.appName
                            textFormat: Text.PlainText
                            color: Theme.text
                            elide: Text.ElideRight
                        }
                        ActionButton {
                            iconName: stream.modelData.audio?.muted ? "volume-muted" : "volume-high"
                            tooltip: I18n.tr("audio.toggleApp", [stream.appName])
                            highlighted: stream.modelData.audio?.muted ?? false
                            tone: "state"
                            onClicked: Audio.toggleStreamMute(stream.modelData)
                        }
                        ControlSlider {
                            Layout.fillWidth: true
                            Accessible.name: I18n.tr("audio.appVolume", [stream.appName])
                            value: stream.modelData.audio?.volume ?? 0
                            onMoved: Audio.setStreamVolume(stream.modelData, value)
                        }
                        Text {
                            text: Math.round((stream.modelData.audio?.volume ?? 0) * 100) + "%"
                            color: Theme.text
                            Layout.preferredWidth: 44
                        }
                    }
                }
            }
            Heading {
                text: I18n.tr("audio.input")
                section: true
                Layout.topMargin: 12
            }
            GroupCard {
                Layout.fillWidth: true
                verticalPadding: 6
                leftPadding: 6
                rightPadding: 6
                spacing: 2
                RowLayout {
                    Layout.fillWidth: true
                    ActionButton {
                        iconName: Audio.source?.audio?.muted ? "microphone-muted" : "microphone"
                        tooltip: I18n.tr("audio.toggleMicrophone")
                        enabled: !!Audio.source
                        highlighted: Audio.source?.audio?.muted ?? false
                        tone: "state"
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
                        implicitHeight: Theme.hit(42)
                        text: Audio.deviceName(modelData)
                        textElide: Text.ElideMiddle
                        iconName: "microphone"
                        highlighted: Audio.source?.id === modelData.id
                        tone: "state"
                        tooltip: Audio.deviceDetails(modelData)
                        onClicked: Audio.selectInput(modelData)
                    }
                }
                Text {
                    visible: Audio.inputs.length === 0
                    Layout.leftMargin: 12
                    text: I18n.tr("audio.noInputs")
                    color: Theme.muted
                }
            }
            Text {
                Layout.fillWidth: true
                Layout.topMargin: 6
                wrapMode: Text.Wrap
                text: I18n.tr("audio.routingHint")
                color: Theme.muted
                font.pixelSize: Theme.textSize(12)
            }
        }
    }
}
