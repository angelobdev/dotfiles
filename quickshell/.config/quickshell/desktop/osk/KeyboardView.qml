import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "KeyScore.js" as KeyScore

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
    // Fingers on the keys by touch point id: the key under each, and how its release ends. Plain JS state;
    // pressedKeys is what the keys bind to.
    property var touches: ({})
    property var pressedKeys: []
    function keyWidth(units) {
        return units * (unit + spacing) - spacing;
    }
    // The key a touch lands on: the nearest one, so the gaps between keys type too, with likely letters a
    // little easier to reach.
    function keyAt(x, y) {
        const candidates = [];
        for (const row of keyRows.children) {
            if (!row.visible)
                continue;
            for (const button of row.children) {
                if (button.key === undefined)
                    continue;
                const origin = button.mapToItem(keys, 0, 0);
                const dx = Math.max(origin.x - x, 0, x - origin.x - button.width);
                const dy = Math.max(origin.y - y, 0, y - origin.y - button.height);
                candidates.push({
                    button: button,
                    label: button.key.label,
                    distance: Math.hypot(dx, dy)
                });
            }
        }
        const letters = Keyboard.predicting ? Keyboard.letters : {};
        return KeyScore.pick(candidates, letters, keyHeight * KeyScore.REACH)?.button ?? null;
    }
    // After a long press the finger slides up to the accents in the strip: the one nearest across.
    function accentAt(x, y) {
        if (y > 0)
            return null;
        let nearest = null;
        let best = Infinity;
        for (const button of accentRow.children) {
            if (button.key === undefined)
                continue;
            const centre = button.mapToItem(keys, button.width / 2, 0).x;
            if (Math.abs(centre - x) < best) {
                best = Math.abs(centre - x);
                nearest = button;
            }
        }
        return nearest;
    }
    function refreshPressed() {
        pressedKeys = Object.values(touches).filter(t => t.button && !t.done).map(t => t.button);
    }
    // Space and Backspace stay with the finger that pressed them (held like a physical key, or repeating);
    // every other key follows the finger and types on release.
    function touchPressed(id, x, y) {
        // A second finger commits the keys the others are on, so fast two-thumb typing keeps its order.
        for (const other of Object.keys(touches))
            commit(touches[other]);
        const button = keyAt(x, y);
        const key = button?.key;
        const touch = {
            button: button,
            pressed: button,
            x: x,
            y: y,
            sticky: key?.action === "space" || key?.action === "backspace",
            done: false,
            accents: false
        };
        touches[id] = touch;
        if (key?.action === "space") {
            Keyboard.hold(key, true);
        } else if (key?.action === "backspace") {
            Keyboard.type(key);
            repeat.key = key;
            repeatDelay.restart();
        }
        longPress.touchId = id;
        longPress.restart();
        refreshPressed();
    }
    function touchMoved(id, x, y) {
        const touch = touches[id];
        if (!touch || touch.done)
            return;
        if (touch.accents) {
            touch.button = accentAt(x, y);
        } else if (touch.sticky) {
            // Backspace stops repeating once the finger leaves it.
            if (touch.button.key.action === "backspace" && keyAt(x, y) !== touch.button) {
                repeatDelay.stop();
                repeat.stop();
                touch.done = true;
            }
        } else {
            const button = keyAt(x, y);
            if (button === touch.button)
                return;
            touch.button = button;
            if (longPress.touchId === id)
                longPress.restart();
        }
        refreshPressed();
    }
    function touchReleased(id, canceled) {
        const touch = touches[id];
        delete touches[id];
        if (longPress.touchId === id)
            longPress.stop();
        if (!touch)
            return;
        if (touch.button?.key.action === "space" && touch.sticky) {
            Keyboard.hold(touch.button.key, false);
        } else if (touch.sticky) {
            repeatDelay.stop();
            repeat.stop();
        } else if (!canceled) {
            commit(touch);
        }
        refreshPressed();
    }
    function commit(touch) {
        if (touch.done || touch.sticky || !touch.button)
            return;
        touch.done = true;
        // Only a touch that stayed on its letter says where a finger lands on the key it meant.
        if (touch.button === touch.pressed && /^[a-z]$/.test(touch.button.key.label ?? "")) {
            const centre = touch.button.mapToItem(keys, touch.button.width / 2, touch.button.height / 2);
            Keyboard.noteTouch(touch.x - centre.x, touch.y - centre.y);
        }
        root.activate(touch.button.key);
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
    // A key held without moving away: its accents appear in the strip and the finger can slide up to one;
    // a key without accents types at once.
    Timer {
        id: longPress
        property var touchId: null
        interval: 450
        onTriggered: {
            const touch = root.touches[touchId];
            if (!touch || touch.done || touch.sticky || !touch.button)
                return;
            const key = touch.button.key;
            if (Keyboard.layout.accents[key.label]) {
                Keyboard.longPress(key);
                touch.accents = true;
                touch.button = null;
            } else {
                root.commit(touch);
            }
            root.refreshPressed();
        }
    }
    component KeyButton: Rectangle {
        id: button
        required property var key
        // The accents in the strip take their own taps; the keys of the rows are driven by the touch area
        // over them.
        property bool standalone: false
        readonly property bool down: tap.pressed || root.pressedKeys.includes(button)
        readonly property bool special: !!key.action && !["space", "enter"].includes(key.action) || key.name !== undefined
        readonly property bool lit: key.action === "shift" && Keyboard.shift > 0 || key.action === "modifier" && Keyboard[key.modifier] === true
        readonly property string icon: key.icon ?? (key.action === "backspace" ? "backspace" : key.action === "enter" ? "enter" : key.action === "shift" ? (Keyboard.shift === 2 ? "shift-lock" : "shift") : "")
        width: root.keyWidth(key.width ?? 1)
        height: root.keyHeight
        radius: Theme.corner(10)
        // Letters stand out from the keyboard background; function keys sit between the two.
        color: down ? Theme.accent : lit ? Qt.alpha(Theme.accent, 0.3) : special ? Theme.raised : Theme.tile
        border.width: 1
        border.color: Theme.stroke
        Icon {
            anchors.centerIn: parent
            visible: button.icon !== ""
            name: button.icon
            color: button.down ? Theme.accentText : Theme.text
            width: 24
            height: 24
        }
        Text {
            anchors.centerIn: parent
            visible: button.icon === ""
            text: Keyboard.labelOf(button.key)
            color: button.down ? Theme.accentText : Theme.text
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
        TapHandler {
            id: tap
            enabled: button.standalone
            longPressThreshold: 0.45
            onTapped: root.activate(button.key)
            onLongPressed: root.activate(button.key)
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
                id: accentRow
                anchors.centerIn: parent
                spacing: root.spacing
                Repeater {
                    model: Keyboard.accents
                    KeyButton {
                        required property var modelData
                        key: modelData
                        standalone: true
                        width: 72
                        height: 38
                    }
                }
            }
            // Words that finish the one being typed, in the place of the accents. With Caps Lock on they would
            // go in lower case, so they wait.
            Row {
                anchors.centerIn: parent
                visible: Keyboard.accents.length === 0 && Keyboard.shift !== 2
                spacing: root.spacing
                Repeater {
                    model: Keyboard.suggestions
                    Rectangle {
                        id: suggestion
                        required property string modelData
                        width: Math.min(170, (strip.width - 220) / 3)
                        height: 38
                        radius: Theme.corner(8)
                        color: suggestionTap.pressed ? Theme.raised : Theme.tile
                        Accessible.role: Accessible.Button
                        Accessible.name: modelData
                        Text {
                            anchors.centerIn: parent
                            width: parent.width - 12
                            text: suggestion.modelData
                            textFormat: Text.PlainText
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: 16
                        }
                        TapHandler {
                            id: suggestionTap
                            onTapped: Keyboard.complete(suggestion.modelData)
                        }
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
        Item {
            id: keys
            Layout.fillWidth: true
            implicitHeight: keyRows.implicitHeight
            ColumnLayout {
                id: keyRows
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                }
                spacing: root.spacing
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
            // One area over every key, so a finger keeps its touch while it slides from key to key.
            MultiPointTouchArea {
                anchors.fill: parent
                onPressed: points => points.forEach(p => root.touchPressed(p.pointId, p.x, p.y))
                onUpdated: points => points.forEach(p => root.touchMoved(p.pointId, p.x, p.y))
                onReleased: points => points.forEach(p => root.touchReleased(p.pointId, false))
                onCanceled: points => points.forEach(p => root.touchReleased(p.pointId, true))
            }
        }
    }
}
