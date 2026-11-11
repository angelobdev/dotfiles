import QtQuick
import QtQuick.Layouts
import ".."

// The keys of a panel, in its footer: each key drawn as a keycap, followed by what it does, wrapping onto further
// lines when narrow. hints is a catalog string "KEYS|action; KEYS|action": entries split on ";", the keys from the
// action on the first "|", keys that do the same split on "," (drawn with a "/" between them), for example
// "↑↓,Tab|select; Enter|open; Esc|close". It can also be a list: [{ keys: ["Enter", "Space"], action: "…" }].
Flow {
    id: root
    property var hints: ""
    // Free text after the keys (Clipboard: where the history is kept).
    property string note: ""
    readonly property var entries: parse(hints)
    function parse(source) {
        if (Array.isArray(source))
            return source.map(entry => ({
                        keys: [].concat(entry.keys ?? []),
                        action: entry.action ?? ""
                    }));
        return String(source ?? "").split(";").map(part => part.trim()).filter(part => part !== "").map(part => {
            const bar = part.indexOf("|");
            if (bar < 0)
                return {
                    keys: [],
                    action: part
                };
            return {
                keys: part.slice(0, bar).split(",").map(key => key.trim()).filter(key => key !== ""),
                action: part.slice(bar + 1).trim()
            };
        });
    }
    Layout.fillWidth: true
    Layout.minimumWidth: 0
    spacing: 4
    Accessible.role: Accessible.StaticText
    Accessible.name: entries.map(entry => entry.keys.join(" / ") + " " + entry.action).concat(note !== "" ? [note] : []).join(", ")
    Repeater {
        model: root.entries
        // One entry: its keys, then its action; the right padding sets it apart from the next.
        Row {
            id: entry
            required property var modelData
            spacing: 5
            rightPadding: 10
            Repeater {
                model: entry.modelData.keys
                Row {
                    id: key
                    required property string modelData
                    required property int index
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Text {
                        visible: key.index > 0
                        anchors.verticalCenter: parent.verticalCenter
                        text: "/"
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(11)
                    }
                    Rectangle {
                        width: Math.max(height, cap.implicitWidth + 10)
                        height: cap.implicitHeight + 2
                        radius: Theme.corner(4)
                        color: "transparent"
                        border.width: 1
                        border.color: Theme.stroke
                        Text {
                            id: cap
                            anchors.centerIn: parent
                            text: key.modelData
                            textFormat: Text.PlainText
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                    }
                }
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: entry.modelData.action
                textFormat: Text.PlainText
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
            }
        }
    }
    Text {
        visible: root.note !== ""
        width: Math.min(implicitWidth, root.width)
        text: root.note
        wrapMode: Text.Wrap
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
}
