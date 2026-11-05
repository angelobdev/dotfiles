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
    readonly property var appResults: DesktopEntries.applications.values.filter(e => !e.noDisplay && !Config.launcherHidden.includes(e.id) && (e.name + " " + e.genericName + " " + e.keywords.join(" ")).toLowerCase().includes(search.text.toLowerCase())).sort((a, b) => a.name.localeCompare(b.name))
    // A calculation first (Enter copies it), then apps, then files (Enter opens one).
    readonly property var results: (LauncherSearch.calc !== "" ? [{
                kind: "calc",
                text: LauncherSearch.calc
            }] : []).concat(appResults.map(entry => ({
                kind: "app",
                entry: entry
            }))).concat(LauncherSearch.files.map(path => ({
                kind: "file",
                path: path
            })))
    onOpened: {
        closeMenu();
        search.clear();
        apps.currentIndex = 0;
        search.forceActiveFocus();
    }
    function launch(item) {
        if (!item)
            return;
        if (item.kind === "calc")
            LauncherSearch.copy(item.text);
        else if (item.kind === "file")
            LauncherSearch.open(item.path);
        else
            Apps.launch(item.entry);
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
                onTextChanged: {
                    apps.currentIndex = 0;
                    LauncherSearch.query = text;
                }
                Keys.onDownPressed: apps.currentIndex = Math.min(apps.count - 1, apps.currentIndex + 1)
                Keys.onUpPressed: apps.currentIndex = Math.max(0, apps.currentIndex - 1)
                onAccepted: root.launch(apps.model[apps.currentIndex])
                Keys.onPressed: event => {
                    if (event.key === Qt.Key_P && event.modifiers & Qt.ControlModifier) {
                        root.togglePin(apps.model[apps.currentIndex]?.entry);
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
                model: root.results
                delegate: ActionButton {
                    id: row
                    required property var modelData
                    required property int index
                    width: apps.width
                    rightPadding: 40
                    implicitHeight: Theme.hit(52)
                    readonly property var entry: modelData.entry ?? null
                    iconSource: modelData.kind === "calc" ? Quickshell.iconPath("accessories-calculator", "application-x-executable") : modelData.kind === "file" ? Quickshell.iconPath("text-x-generic", "application-x-executable") : Quickshell.iconPath(entry.icon, "application-x-executable")
                    iconSize: 30
                    alignLeft: true
                    textElide: Text.ElideMiddle
                    text: modelData.kind === "calc" ? "= " + modelData.text : modelData.kind === "file" ? modelData.path.replace(Quickshell.env("HOME"), "~") : entry.name + (entry.runInTerminal ? I18n.tr("launcher.terminalSuffix") : "")
                    tooltip: modelData.kind === "calc" ? I18n.tr("launcher.copyResult") : modelData.kind === "file" ? I18n.tr("launcher.openFile") : ""
                    highlighted: apps.currentIndex === index
                    highlightBackground: false
                    onClicked: root.launch(modelData)
                    // A long press (touch) opens the pin menu like a right click; Button then skips the click.
                    onPressAndHold: {
                        if (!row.entry)
                            return;
                        apps.currentIndex = row.index;
                        root.openMenu(row.entry, row, Qt.point(row.width / 2, row.height / 2));
                    }
                    TapHandler {
                        acceptedButtons: Qt.RightButton
                        onTapped: (point, button) => {
                            if (!row.entry)
                                return;
                            apps.currentIndex = row.index;
                            root.openMenu(row.entry, row, point.position);
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
                        visible: !!row.entry && Dock.isPinned(row.entry.id)
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
                // Touch has no arrows, Enter or Ctrl+P. Wraps: a wide theme font (Fira Code) or a long
                // translation would otherwise run past the card.
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: Tablet.active ? I18n.tr("launcher.touchHint") : I18n.tr("launcher.navigationHint")
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
