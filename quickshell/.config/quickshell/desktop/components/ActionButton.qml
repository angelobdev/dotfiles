import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."

Button {
    id: root
    property bool destructive: false
    property string iconName: ""
    property url iconSource: ""
    property int iconSize: 20
    property bool alignLeft: false
    property bool iconAfterText: false
    property int textElide: Text.ElideRight
    property string tooltip: ""
    readonly property bool hasIcon: iconName !== "" || iconSource.toString() !== ""
    readonly property color foreground: destructive ? Theme.danger : highlighted ? Theme.accentText : Theme.text
    implicitHeight: 36
    implicitWidth: Math.max(36, label.implicitWidth + (hasIcon ? iconSize + (text ? 10 : 0) : 0) + 24)
    leftPadding: 0
    rightPadding: 0
    font.family: Theme.font
    font.pixelSize: 13
    opacity: enabled ? 1 : 0.45
    Accessible.name: text || tooltip
    HintTooltip {
        target: root
        text: root.tooltip
        hovered: root.hovered && !root.down
    }
    contentItem: RowLayout {
        layoutDirection: root.iconAfterText ? Qt.RightToLeft : Qt.LeftToRight
        spacing: root.text && root.hasIcon ? 10 : 0
        Item {
            Layout.fillWidth: true
            visible: !root.alignLeft
        }
        Item {
            visible: root.hasIcon
            Layout.preferredWidth: root.iconSize
            Layout.preferredHeight: root.iconSize
            Icon {
                anchors.fill: parent
                visible: root.iconName !== ""
                name: root.iconName
                color: root.foreground
            }
            Image {
                anchors.fill: parent
                visible: root.iconName === ""
                source: root.iconSource
                fillMode: Image.PreserveAspectFit
                sourceSize: Qt.size(root.iconSize * 2, root.iconSize * 2)
            }
        }
        Text {
            id: label
            visible: root.text !== ""
            Layout.fillWidth: root.alignLeft
            text: root.text
            font: root.font
            color: root.foreground
            verticalAlignment: Text.AlignVCenter
            elide: root.textElide
            textFormat: Text.PlainText
        }
        Item {
            Layout.fillWidth: true
            visible: !root.alignLeft
        }
    }
    background: Rectangle {
        radius: 11
        color: root.highlighted ? Theme.accent : root.down ? Theme.raised : root.hovered || root.activeFocus ? Theme.raised : "transparent"
        border.width: root.activeFocus ? 0 : 0
        border.color: Theme.accent
        Behavior on color {
            ColorAnimation {
                duration: 120
            }
        }
    }
}
