import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// The keys and the strip above them: the extra row switch on the left, accented variants in the middle
// after a long press, docking and hiding on the right. In the floating keyboard the strip is the handle.
Rectangle {
    id: root
    property bool floating: false
    // The floating keyboard moves this item when its strip is dragged.
    property Item dragTarget: null
    readonly property int padding: 8
    readonly property int spacing: 6
    // Sized for fingers on a 14 inch display (a logical pixel is about 0.18 mm): keys of 10-11 mm.
    readonly property int keyHeight: floating ? 56 : 64
    readonly property real unit: (width - 2 * padding - 9 * spacing) / 10
    function keyWidth(units) {
        return units * (unit + spacing) - spacing;
    }
    function activate(key) {
        if (key.action === "shift")
            Keyboard.shiftTapped();
        else if (key.action === "page")
            Keyboard.page = key.page;
        else if (key.action === "modifier")
            Keyboard[key.modifier] = !Keyboard[key.modifier];
        else if (key.action !== "backspace")
            Keyboard.type(key);
    }
    implicitHeight: column.implicitHeight + 2 * padding
    radius: floating ? Theme.corner(18) : 0
    color: Theme.background
    border.width: floating ? Theme.frameWidth : 0
    border.color: Theme.frameInactive
    // Holding Backspace repeats it, as a physical key does.
    Timer {
        id: repeat
        property var key: null
        interval: 60
        repeat: true
        onTriggered: Keyboard.type(key)
    }
    Timer {
        id: repeatDelay
        interval: 420
        onTriggered: repeat.start()
    }
    component KeyButton: Rectangle {
        id: button
        required property var key
        readonly property bool special: !!key.action && !["space", "enter"].includes(key.action) || key.name !== undefined
        readonly property bool lit: key.action === "shift" && Keyboard.shift > 0 || key.action === "modifier" && Keyboard[key.modifier] === true
        readonly property string icon: key.icon ?? (key.action === "backspace" ? "backspace" : key.action === "enter" ? "enter" : key.action === "shift" ? (Keyboard.shift === 2 ? "shift-lock" : "shift") : "")
        width: root.keyWidth(key.width ?? 1)
        height: root.keyHeight
        radius: Theme.corner(10)
        // Letters stand out from the keyboard background; function keys sit between the two.
        color: tap.pressed ? Theme.accent : lit ? Qt.alpha(Theme.accent, 0.3) : special ? Theme.raised : Theme.tile
        border.width: 1
        border.color: Theme.stroke
        Icon {
            anchors.centerIn: parent
            visible: button.icon !== ""
            name: button.icon
            color: tap.pressed ? Theme.accentText : Theme.text
            width: 24
            height: 24
        }
        Text {
            anchors.centerIn: parent
            visible: button.icon === ""
            text: Keyboard.labelOf(button.key)
            color: tap.pressed ? Theme.accentText : Theme.text
            font.family: Theme.font
            font.pixelSize: button.special ? 15 : 22
        }
        // The shifted character, small in the corner, where it is not just the capital.
        Text {
            anchors {
                top: parent.top
                right: parent.right
                margins: 4
            }
            visible: button.key.shift !== undefined
            text: button.key.shift ?? ""
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 12
        }
        // A key held without variants still types once; Backspace types on press and then repeats.
        TapHandler {
            id: tap
            longPressThreshold: 0.45
            onTapped: root.activate(button.key)
            onLongPressed: {
                if (Keyboard.layout.accents[button.key.label])
                    Keyboard.longPress(button.key);
                else if (button.key.action !== "backspace")
                    root.activate(button.key);
            }
            onPressedChanged: {
                if (button.key.action !== "backspace")
                    return;
                if (pressed) {
                    Keyboard.type(button.key);
                    repeat.key = button.key;
                    repeatDelay.start();
                } else {
                    repeatDelay.stop();
                    repeat.stop();
                }
            }
        }
    }
    component StripButton: Rectangle {
        id: stripButton
        property string icon: ""
        property bool lit: false
        signal clicked
        width: 52
        height: 38
        radius: Theme.corner(8)
        color: stripTap.pressed ? Theme.raised : lit ? Qt.alpha(Theme.accent, 0.3) : "transparent"
        Icon {
            anchors.centerIn: parent
            name: stripButton.icon
            color: Theme.text
            width: 22
            height: 22
        }
        TapHandler {
            id: stripTap
            onTapped: stripButton.clicked()
        }
    }
    ColumnLayout {
        id: column
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: root.padding
        }
        spacing: root.spacing
        Item {
            id: strip
            Layout.fillWidth: true
            implicitHeight: 40
            DragHandler {
                enabled: root.dragTarget !== null
                target: root.dragTarget
                xAxis.minimum: 0
                xAxis.maximum: root.dragTarget ? root.dragTarget.parent.width - root.dragTarget.width : 0
                yAxis.minimum: 0
                yAxis.maximum: root.dragTarget ? root.dragTarget.parent.height - root.dragTarget.height : 0
            }
            StripButton {
                anchors.verticalCenter: parent.verticalCenter
                icon: "keyboard"
                lit: Keyboard.extra
                onClicked: Keyboard.setExtra(!Keyboard.extra)
                Accessible.name: I18n.tr("osk.extra")
            }
            Row {
                anchors.centerIn: parent
                spacing: root.spacing
                Repeater {
                    model: Keyboard.accents
                    KeyButton {
                        required property var modelData
                        key: modelData
                        width: 72
                        height: 38
                    }
                }
            }
            Row {
                anchors {
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                }
                spacing: 4
                StripButton {
                    icon: Keyboard.floating ? "dock" : "pip"
                    onClicked: Keyboard.setFloating(!Keyboard.floating)
                    Accessible.name: Keyboard.floating ? I18n.tr("osk.dock") : I18n.tr("osk.float")
                }
                StripButton {
                    icon: "chevron-down"
                    onClicked: Keyboard.setShown(false)
                    Accessible.name: I18n.tr("osk.hide")
                }
            }
        }
        Row {
            visible: Keyboard.extraShown
            Layout.alignment: Qt.AlignHCenter
            spacing: root.spacing
            Repeater {
                model: Keyboard.layout.extra
                KeyButton {
                    required property var modelData
                    key: Object.assign({
                        width: 1.25
                    }, modelData)
                }
            }
        }
        Repeater {
            model: Keyboard.rows
            Row {
                required property var modelData
                Layout.alignment: Qt.AlignHCenter
                spacing: root.spacing
                Repeater {
                    model: parent.modelData.keys
                    KeyButton {
                        required property var modelData
                        key: modelData
                    }
                }
            }
        }
    }
}
