import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"

Overlay {
    id: root
    panelName: "controls"
    readonly property var moduleSources: ({
            network: "NetworkTile.qml",
            bluetooth: "BluetoothTile.qml",
            brightness: "BrightnessControl.qml",
            audio: "AudioControl.qml",
            media: "MediaControl.qml",
            doNotDisturb: "FocusControl.qml",
            idle: "IdleControl.qml",
            rotation: "RotationControl.qml"
        })
    onOpened: header.closeButton.forceActiveFocus()
    SidePanelCard {
        height: Math.min(layout.implicitHeight + 32, parent.height - 76)
        ColumnLayout {
            id: layout
            anchors {
                fill: parent
                margins: Theme.panelPadding
            }
            spacing: 12
            PanelHeader {
                id: header
                title: I18n.tr("controlCenter.title")
                Layout.fillWidth: true
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
                        model: Config.controlCenterModules.filter((name, index, all) => Object.prototype.hasOwnProperty.call(root.moduleSources, name) && all.indexOf(name) === index)
                        Loader {
                            required property string modelData
                            Layout.fillWidth: true
                            Layout.columnSpan: ["network", "bluetooth"].includes(modelData) ? 1 : 2
                            // A tile with nothing to control on this machine sets "available" to false.
                            visible: item?.available ?? true
                            source: root.moduleSources[modelData]
                        }
                    }
                }
            }
        }
    }
}
