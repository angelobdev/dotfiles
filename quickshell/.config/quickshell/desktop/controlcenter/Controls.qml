import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Overlay {
    id: root
    panelName: "controls"
    onOpened: closeButton.forceActiveFocus()
    Card {
        anchors {
            top: parent.top
            right: parent.right
            topMargin: 58
            rightMargin: 12
        }
        width: Math.min(Config.controlCenterWidth, parent.width - 24)
        height: Math.min(layout.implicitHeight + 32, parent.height - 76)
        ColumnLayout {
            id: layout
            anchors {
                fill: parent
                margins: 16
            }
            spacing: 12
            RowLayout {
                Text {
                    text: "Centro di controllo"
                    font.family: Theme.font
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    color: Theme.text
                    Layout.fillWidth: true
                }
                PanelIconButton {
                    id: closeButton
                    iconName: "close"
                    tooltip: "Chiudi"
                    onClicked: ShellState.close()
                }
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                implicitHeight: grid.implicitHeight
                contentWidth: availableWidth
                clip: true
                GridLayout {
                    id: grid
                    width: parent.width
                    columns: 2
                    rowSpacing: 10
                    columnSpacing: 10
                    Repeater {
                        model: Config.controlCenterModules.filter((name, index, all) => ["network", "bluetooth", "brightness", "audio", "media", "doNotDisturb", "idle"].includes(name) && all.indexOf(name) === index)
                        Loader {
                            required property string modelData
                            Layout.fillWidth: true
                            Layout.columnSpan: ["network", "bluetooth"].includes(modelData) ? 1 : 2
                            source: ({
                                    network: "NetworkTile.qml",
                                    bluetooth: "BluetoothTile.qml",
                                    brightness: "BrightnessControl.qml",
                                    audio: "AudioControl.qml",
                                    media: "MediaControl.qml",
                                    doNotDisturb: "FocusControl.qml",
                                    idle: "IdleControl.qml"
                                })[modelData]
                        }
                    }
                }
            }
        }
    }
}
