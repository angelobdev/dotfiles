import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

Overlay {
    id: root
    panelName: "clipboard"
    property bool confirmClear: false
    onOpened: {
        confirmClear = false;
        search.clear();
        Clipboard.refresh();
        search.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(620, parent.width - 32)
        height: Math.min(560, parent.height - 76)
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            PanelHeader {
                title: "Clipboard"
                Layout.fillWidth: true
                PanelIconButton {
                    iconName: Clipboard.paused ? "play" : "pause"
                    tooltip: Clipboard.paused ? "Riprendi storico" : "Sospendi storico"
                    enabled: Config.clipboardEnabled
                    onClicked: Clipboard.paused = !Clipboard.paused
                }
                PanelIconButton {
                    iconName: "trash"
                    tooltip: "Svuota storico"
                    enabled: !Clipboard.busy && Clipboard.entries.length > 0
                    onClicked: root.confirmClear = !root.confirmClear
                }
            }
            RowLayout {
                visible: root.confirmClear
                Layout.fillWidth: true
                Text {
                    text: "Eliminare tutto lo storico?"
                    color: Theme.text
                    Layout.fillWidth: true
                }
                ActionButton {
                    text: "Elimina"
                    destructive: true
                    onClicked: {
                        Clipboard.act("clear");
                        root.confirmClear = false;
                    }
                }
                ActionButton {
                    text: "Annulla"
                    onClicked: root.confirmClear = false
                }
            }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: "Cerca nello storico…"
                onTextChanged: clips.currentIndex = 0
                Keys.onDownPressed: clips.currentIndex = Math.min(clips.count - 1, clips.currentIndex + 1)
                Keys.onUpPressed: clips.currentIndex = Math.max(0, clips.currentIndex - 1)
                onAccepted: if (clips.model[clips.currentIndex])
                    Clipboard.act("copy", clips.model[clips.currentIndex].id)
            }
            ListView {
                id: clips
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: Clipboard.entries.filter(e => e.preview.toLowerCase().includes(search.text.toLowerCase()))
                delegate: RowLayout {
                    required property var modelData
                    required property int index
                    width: clips.width
                    ActionButton {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        implicitHeight: 46
                        text: modelData.preview
                        iconName: modelData.image ? "image" : "clipboard"
                        alignLeft: true
                        highlighted: clips.currentIndex === index
                        enabled: !Clipboard.busy
                        onClicked: Clipboard.act("copy", modelData.id)
                    }
                    PanelIconButton {
                        iconName: "trash"
                        tooltip: "Elimina elemento"
                        enabled: !Clipboard.busy
                        onClicked: Clipboard.act("delete", modelData.id)
                    }
                }
                ScrollBar.vertical: ScrollBar {}
                Text {
                    anchors.centerIn: parent
                    visible: clips.count === 0
                    text: "Nessun elemento nello storico"
                    color: Theme.muted
                }
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: Clipboard.error || (!Config.clipboardEnabled ? "Raccolta disabilitata nella configurazione." : Clipboard.paused ? "Raccolta sospesa. Lo storico rimane disponibile." : "↑ ↓ seleziona · Invio copia · Esc chiudi Lo storico è salvato sul disco.")
                color: Clipboard.error ? Theme.danger : Theme.muted
                font.pixelSize: 12
                textFormat: Text.PlainText
            }
        }
    }
}
