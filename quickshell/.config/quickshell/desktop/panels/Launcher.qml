import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"

Overlay {
    id: root
    panelName: "launcher"
    dialog: true
    onOpened: {
        search.clear();
        apps.currentIndex = 0;
        search.forceActiveFocus();
    }
    function launch(entry) {
        if (!entry)
            return;
        Apps.launch(entry);
        ShellState.close();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(600, parent.width - 48)
        height: Math.min(560, parent.height - 100)
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 14
            Heading {
                text: I18n.tr("launcher.title")
            }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: I18n.tr("launcher.searchPlaceholder")
                color: Theme.text
                font.family: Theme.font
                onTextChanged: apps.currentIndex = 0
                Keys.onDownPressed: apps.currentIndex = Math.min(apps.count - 1, apps.currentIndex + 1)
                Keys.onUpPressed: apps.currentIndex = Math.max(0, apps.currentIndex - 1)
                onAccepted: root.launch(apps.model[apps.currentIndex])
            }
            ListView {
                id: apps
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                // The selection glides between rows instead of jumping.
                highlight: Rectangle {
                    radius: 11
                    color: Theme.accent
                }
                highlightMoveDuration: Theme.motionNormal
                highlightMoveVelocity: -1
                highlightResizeDuration: 0
                model: DesktopEntries.applications.values.filter(e => !e.noDisplay && (e.name + " " + e.genericName + " " + e.keywords.join(" ")).toLowerCase().includes(search.text.toLowerCase())).sort((a, b) => a.name.localeCompare(b.name))
                delegate: ActionButton {
                    required property var modelData
                    required property int index
                    width: apps.width
                    implicitHeight: 52
                    iconSource: Quickshell.iconPath(modelData.icon, "application-x-executable")
                    iconSize: 30
                    alignLeft: true
                    text: modelData.name + (modelData.runInTerminal ? I18n.tr("launcher.terminalSuffix") : "")
                    highlighted: apps.currentIndex === index
                    highlightBackground: false
                    onClicked: root.launch(modelData)
                }
                ScrollBar.vertical: ScrollBar {}
                Text {
                    anchors.centerIn: parent
                    visible: apps.count === 0
                    text: I18n.tr("launcher.empty")
                    color: Theme.muted
                }
            }
            Text {
                text: I18n.tr("launcher.navigationHint")
                color: Theme.muted
                font.pixelSize: 12
            }
        }
    }
}
