import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Io
import Quickshell.Hyprland
import ".."
import "../components"

Overlay {
    id: root
    panelName: "hints"
    property var bindings: []
    property string error: ""
    readonly property var categories: ["Applicazioni", "Shell e pannelli", "Cattura schermo", "Finestre", "Workspace", "Mouse", "Audio e luminosità", "Sessione", "Altro"]
    function category(bind) {
        const name = (bind.description || "").toLowerCase();
        if ((bind.key || "").startsWith("XF86Audio") || (bind.key || "").startsWith("XF86MonBrightness"))
            return "Audio e luminosità";
        if ((bind.key || "").startsWith("mouse:"))
            return "Mouse";
        if (/screenshot|registrazione/.test(name))
            return "Cattura schermo";
        if (/workspace|scratchpad/.test(name))
            return "Workspace";
        if (/blocca|sospendi|logout|riavvio|spegni|sessione/.test(name))
            return "Sessione";
        if (/applicazioni|centro di controllo|notifiche|quickshell|rete|wi-fi|volume e|batteria|calendario|hints|sfondo|clipboard/.test(name))
            return "Shell e pannelli";
        if (/browser|terminale|kitty|1password/.test(name))
            return "Applicazioni";
        if (/finestra|focus|floating|fullscreen|schermo intero|^sposta |tiling|split|pseudo/.test(name))
            return "Finestre";
        return "Altro";
    }
    function shortcut(bind) {
        const parts = [];
        for (const [mask, label] of [[64, "Super"], [4, "Ctrl"], [1, "Shift"], [8, "Alt"], [128, "Mod5"]])
            if ((bind.modmask & mask) !== 0)
                parts.push(label);
        const names = {
            Return: "Invio",
            Print: "Stamp",
            Space: "Spazio",
            space: "Spazio",
            left: "←",
            right: "→",
            up: "↑",
            down: "↓",
            "mouse:272": "Mouse sinistro",
            "mouse:273": "Mouse destro"
        };
        parts.push(names[bind.key] || bind.key || ("code:" + bind.keycode));
        return parts.join(" + ");
    }
    function refreshBindings() {
        if (!reader.running)
            reader.running = true;
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "configreloaded" && root.visible)
                root.refreshBindings();
        }
    }
    onOpened: {
        search.clear();
        error = "";
        search.forceActiveFocus();
        refreshBindings();
    }
    Process {
        id: reader
        command: ["hyprctl", "-j", "binds"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.bindings = JSON.parse(text).map(b => ({
                                keys: root.shortcut(b),
                                name: b.description || b.dispatcher,
                                submap: b.submap || "",
                                release: b.release,
                                category: root.category(b)
                            })).sort((a, b) => root.categories.indexOf(a.category) - root.categories.indexOf(b.category));
                } catch (e) {
                    root.error = "Impossibile leggere i bind di Hyprland.";
                }
            }
        }
        onExited: (code, status) => {
            if (code !== 0)
                root.error = "Hyprland non ha restituito i bind attivi.";
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(820, parent.width - 48)
        height: Math.min(650, parent.height - 96)
        ColumnLayout {
            anchors {
                fill: parent
                margins: 22
            }
            spacing: 14
            Heading {
                text: "Hints · Scorciatoie tastiera"
            }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: "Cerca una scorciatoia o un’azione…"
            }
            RowLayout {
                Text {
                    text: "Scorciatoia"
                    Layout.preferredWidth: 280
                    color: Theme.muted
                    font.pixelSize: 12
                }
                Text {
                    text: "Azione"
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
            ListView {
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 3
                model: root.bindings.filter(b => (b.keys + " " + b.name + " " + b.submap + " " + b.category).toLowerCase().includes(search.text.toLowerCase()))
                section.property: "category"
                section.criteria: ViewSection.FullString
                section.delegate: Item {
                    required property string section
                    width: list.width
                    height: 38
                    Text {
                        anchors {
                            left: parent.left
                            bottom: parent.bottom
                            bottomMargin: 8
                        }
                        text: section
                        color: Theme.muted
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.6
                    }
                }
                delegate: Rectangle {
                    required property var modelData
                    required property int index
                    width: list.width
                    height: Math.max(40, description.implicitHeight + 16)
                    radius: 9
                    color: index % 2 === 0 ? Theme.raised : "transparent"
                    RowLayout {
                        anchors {
                            fill: parent
                            leftMargin: 10
                            rightMargin: 10
                        }
                        spacing: 14
                        Text {
                            text: modelData.keys
                            Layout.preferredWidth: 256
                            color: Theme.accent
                            font.family: Theme.font
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                        Text {
                            id: description
                            text: modelData.name + (modelData.submap ? " [" + modelData.submap + "]" : "") + (modelData.release ? " · al rilascio" : "")
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            color: Theme.text
                            font.pixelSize: 13
                            textFormat: Text.PlainText
                        }
                    }
                }
                ScrollBar.vertical: ScrollBar {}
            }
            Text {
                visible: root.error !== ""
                text: root.error
                color: Theme.danger
            }
            Text {
                visible: !reader.running && list.count === 0 && !root.error
                text: "Nessuna scorciatoia trovata"
                color: Theme.muted
            }
            RowLayout {
                Text {
                    text: root.bindings.length + " bind dalla sessione attiva"
                    color: Theme.muted
                    font.pixelSize: 12
                }
                Item {
                    Layout.fillWidth: true
                }
                ActionButton {
                    text: "Chiudi"
                    onClicked: ShellState.close()
                }
            }
        }
    }
}
