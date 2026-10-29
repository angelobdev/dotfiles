import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."

Button {
    id: root
    property bool destructive: false
    // Bar controls should not retain a focus highlight after mouse clicks.
    property bool keyboardFocusOnly: false
    // Text buttons keep their inset; small icon controls can opt out.
    property bool compact: false
    property string iconName: ""
    property url iconSource: ""
    property int iconSize: 20
    property bool alignLeft: false
    property bool iconAfterText: false
    property int textElide: Text.ElideRight
    property string tooltip: ""
    // Lists with a moving selection (ListView.highlight) draw the highlighted background themselves.
    property bool highlightBackground: true
    // Text and icon colour when neither destructive nor highlighted; the bar follows BarStyle.
    property color normalColor: Theme.text
    readonly property bool hasIcon: iconName !== "" || iconSource.toString() !== ""
    readonly property color foreground: destructive ? Theme.danger : highlighted ? Theme.accentText : normalColor
    implicitHeight: 36
    implicitWidth: Math.max(36, label.implicitWidth + (hasIcon ? iconSize + (text ? 10 : 0) : 0) + leftPadding + rightPadding)
    leftPadding: compact ? 0 : 12
    rightPadding: compact ? 0 : 12
    font.family: Theme.font
    font.pixelSize: 13
    opacity: enabled ? 1 : 0.45
    // A press sinks by a couple of pixels whatever the width, so wide rows barely move and icons visibly do.
    scale: down ? 1 - Math.min(0.04, 6 / Math.max(width, 1)) : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.motionFast
            easing.type: Easing.BezierSpline
            easing.bezierCurve: Theme.easeOut
        }
    }
    Accessible.name: text || tooltip
    // Only buttons with a tooltip pay for a tooltip window.
    Loader {
        active: root.tooltip !== ""
        sourceComponent: HintTooltip {
            target: root
            text: root.tooltip
            hovered: root.hovered && !root.down
        }
    }
    contentItem: RowLayout {
        layoutDirection: root.iconAfterText ? Qt.RightToLeft : Qt.LeftToRight
        // The centering fillers must not add spacing, or centred icon+text buttons overflow their implicit width.
        spacing: 0
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
        Item {
            visible: root.text !== "" && root.hasIcon
            Layout.preferredWidth: 10
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
        radius: Theme.corner(11)
        color: root.highlighted ? (root.highlightBackground ? Theme.accent : "transparent") : root.down || root.hovered || (root.keyboardFocusOnly ? root.visualFocus : root.activeFocus) ? Theme.raised : "transparent"
        Behavior on color {
            ColorAnimation {
                duration: Theme.motionFast
            }
        }
    }
}
