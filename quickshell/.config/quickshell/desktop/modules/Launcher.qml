import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
Overlay {
    id: root
    panelName: "launcher"
    onOpened: { search.clear(); apps.currentIndex = 0; search.forceActiveFocus(); }
    function launch(entry) {
        if (!entry) return;
        // Never pass desktop-file Exec strings through a shell.
        if (entry.runInTerminal) Quickshell.execDetached({
            command: ["kitty", "-e"].concat(entry.command),
            workingDirectory: entry.workingDirectory || Quickshell.env("HOME")
        });
        else entry.execute();
        ShellState.close();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(600, parent.width - 48)
        height: Math.min(560, parent.height - 100)
        ColumnLayout {
            anchors { fill: parent; margins: 22 }
            spacing: 14
            Heading { text: "Applicazioni" }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: "Cerca un’applicazione…"
                color: Theme.text
                font.family: Theme.font
                onTextChanged: apps.currentIndex = 0
                Keys.onDownPressed: apps.currentIndex = Math.min(apps.count - 1, apps.currentIndex + 1)
                Keys.onUpPressed: apps.currentIndex = Math.max(0, apps.currentIndex - 1)
                onAccepted: root.launch(apps.model[apps.currentIndex])
            }
            ListView {
                id: apps
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true
                spacing: 4
                model: DesktopEntries.applications.values.filter(e => !e.noDisplay &&
                    (e.name + " " + e.genericName + " " + e.keywords.join(" ")).toLowerCase().includes(search.text.toLowerCase()))
                    .sort((a, b) => a.name.localeCompare(b.name))
                delegate: ActionButton {
                    required property var modelData
                    required property int index
                    width: apps.width
                    implicitHeight: 44
                    text: modelData.name + (modelData.runInTerminal ? "  [terminale]" : "")
                    highlighted: apps.currentIndex === index
                    onClicked: root.launch(modelData)
                }
                ScrollBar.vertical: ScrollBar {}
                Text { anchors.centerIn: parent; visible: apps.count === 0; text: "Nessuna applicazione"; color: Theme.muted }
            }
            Text { text: "↑ ↓ seleziona    Invio apri    Esc chiudi"; color: Theme.muted; font.pixelSize: 12 }
        }
    }
}
