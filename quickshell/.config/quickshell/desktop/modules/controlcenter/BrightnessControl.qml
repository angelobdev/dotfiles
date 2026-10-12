import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

ControlTile {
    id: root
    property bool expanded: Config.expandMonitors
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
                text: "Luminosità"
                color: Theme.text
                font.pixelSize: 13
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
            Text {
                text: Brightness.primary?.available ? Brightness.displayPercent(Brightness.primary) + "%" : "—"
                color: Theme.muted
                font.pixelSize: 12
            }
            CompactIconButton {
                visible: Brightness.others.length > 0
                iconName: "chevron-down"
                rotation: root.expanded ? 180 : 0
                tooltip: "Altri monitor"
                implicitHeight: 26
                implicitWidth: 28
                onClicked: root.expanded = !root.expanded
            }
        }
        Text {
            text: Brightness.primary?.name || "Nessun monitor"
            color: Theme.muted
            font.pixelSize: 11
        }
        RowLayout {
            Icon {
                name: "sun"
                Layout.preferredWidth: 20
                Layout.preferredHeight: 20
            }
            ControlSlider {
                id: primarySlider
                Layout.fillWidth: true
                from: 1
                to: 100
                stepSize: 1
                enabled: Brightness.primary?.available ?? false
                onMoved: Brightness.setBrightness(Brightness.primary, value)
                Accessible.name: "Luminosità monitor principale"
                Binding on value {
                    when: !primarySlider.pressed
                    value: Brightness.displayPercent(Brightness.primary)
                }
            }
        }
        Text {
            visible: !!Brightness.primary && !Brightness.primary.available
            text: Brightness.primary?.error || "Lettura in corso…"
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Theme.muted
            font.pixelSize: 11
        }
        ColumnLayout {
            visible: root.expanded && Brightness.others.length > 0
            Layout.fillWidth: true
            Repeater {
                model: Brightness.otherNames
                ColumnLayout {
                    id: monitorRow
                    required property string modelData
                    readonly property var monitor: Brightness.monitors.find(m => m.name === modelData)
                    Layout.fillWidth: true
                    spacing: 3
                    Text {
                        text: monitorRow.modelData + ((monitorRow.monitor?.available ?? false) ? " · " + Brightness.displayPercent(monitorRow.monitor) + "%" : "")
                        color: Theme.muted
                        font.pixelSize: 11
                    }
                    ControlSlider {
                        id: otherSlider
                        Layout.fillWidth: true
                        from: 1
                        to: 100
                        stepSize: 1
                        enabled: monitorRow.monitor?.available ?? false
                        onMoved: Brightness.setBrightness(monitorRow.monitor, value)
                        Accessible.name: "Luminosità " + monitorRow.modelData
                        Binding on value {
                            when: !otherSlider.pressed
                            value: Brightness.displayPercent(monitorRow.monitor)
                        }
                    }
                    Text {
                        visible: !(monitorRow.monitor?.available ?? false)
                        text: monitorRow.monitor?.error || "Lettura in corso…"
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        color: Theme.muted
                        font.pixelSize: 11
                    }
                }
            }
        }
        Text {
            visible: Brightness.error !== ""
            text: Brightness.error
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            color: Theme.danger
            font.pixelSize: 11
        }
    }
}
