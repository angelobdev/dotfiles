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
    // Entry whose pin menu is open; null when closed.
    property var menuEntry: null
    property point menuOrigin: Qt.point(0, 0)
    onOpened: {
        closeMenu();
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
    function togglePin(entry) {
        if (!entry)
            return;
        if (Dock.isPinned(entry.id))
            Dock.unpin(entry.id);
        else
            Dock.pin(entry.id);
    }
    function openMenu(entry, item, position) {
        menuEntry = entry;
        menuOrigin = item.mapToItem(contentItem, position.x, position.y);
        pinMenu.forceActiveFocus();
    }
    function closeMenu() {
        menuEntry = null;
        search.forceActiveFocus();
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
                Keys.onPressed: event => {
                    if (event.key === Qt.Key_P && event.modifiers & Qt.ControlModifier) {
                        root.togglePin(apps.model[apps.currentIndex]);
                        event.accepted = true;
                    }
                }
            }
            ListView {
                id: apps
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                // The selection glides between rows instead of jumping.
                highlight: Rectangle {
                    radius: Theme.corner(11)
                    color: Theme.accent
                }
                highlightMoveDuration: Theme.motionNormal
                highlightMoveVelocity: -1
                highlightResizeDuration: 0
                model: DesktopEntries.applications.values.filter(e => !e.noDisplay && (e.name + " " + e.genericName + " " + e.keywords.join(" ")).toLowerCase().includes(search.text.toLowerCase())).sort((a, b) => a.name.localeCompare(b.name))
                delegate: ActionButton {
                    id: row
                    required property var modelData
                    required property int index
                    width: apps.width
                    rightPadding: 40
                    implicitHeight: 52
                    iconSource: Quickshell.iconPath(modelData.icon, "application-x-executable")
                    iconSize: 30
                    alignLeft: true
                    text: modelData.name + (modelData.runInTerminal ? I18n.tr("launcher.terminalSuffix") : "")
                    highlighted: apps.currentIndex === index
                    highlightBackground: false
                    onClicked: root.launch(modelData)
                    TapHandler {
                        acceptedButtons: Qt.RightButton
                        onTapped: (point, button) => {
                            apps.currentIndex = row.index;
                            root.openMenu(row.modelData, row, point.position);
                        }
                    }
                    // Only pinned apps carry a mark; the hint below says how to pin.
                    Icon {
                        anchors {
                            right: parent.right
                            rightMargin: 14
                            verticalCenter: parent.verticalCenter
                        }
                        width: 16
                        height: 16
                        visible: Dock.isPinned(row.modelData.id)
                        name: "pin"
                        color: row.highlighted ? Theme.accentText : Theme.muted
                    }
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
    // A click beside the pin menu closes only the menu.
    MouseArea {
        anchors.fill: parent
        visible: root.menuEntry !== null
        acceptedButtons: Qt.AllButtons
        onPressed: root.closeMenu()
    }
    PopupMenu {
        id: pinMenu
        visible: root.menuEntry !== null
        x: Math.max(6, Math.min(root.menuOrigin.x, parent.width - width - 6))
        y: Math.max(6, Math.min(root.menuOrigin.y, parent.height - height - 6))
        entries: root.menuEntry ? [
            {
                kind: "heading",
                text: root.menuEntry.name
            },
            {
                text: I18n.tr(Dock.isPinned(root.menuEntry.id) ? "dock.menu.unpin" : "dock.menu.pin"),
                action: () => root.togglePin(root.menuEntry)
            }
        ] : []
        onTriggered: root.closeMenu()
        onDismissed: root.closeMenu()
    }
}
