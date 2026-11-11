import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"
import "../services/LauncherRank.js" as Rank

Overlay {
    id: root
    panelName: "launcher"
    dialog: true
    // Entry whose pin menu is open; null when closed.
    property var menuEntry: null
    property point menuOrigin: Qt.point(0, 0)
    // Entries of the desktop that need a profile: shown only with it installed (services/Installed.qml).
    readonly property var appUnits: ({
            "desktop-ai": "assistant",
            "desktop-radio": "radio"
        })
    // The launch history (empty when Settings → Privacy turns it off) and the time it is scored at, both taken when
    // the launcher opens: a launch from it does not reorder the rows while it fades out.
    property var history: ({})
    property real now: 0
    // Best match first, then the apps used most lately, then by name (services/LauncherRank.js).
    readonly property var appResults: Rank.rank(DesktopEntries.applications.values.filter(e => !e.noDisplay && !Config.launcherHidden.includes(e.id) && (!appUnits[e.id] || Installed.has(appUnits[e.id]))), search.text, history, now)
    // A calculation first (Enter copies it), then apps, then files (Enter opens one).
    // Each row has a key, so results that arrive later (files, a calculation) are inserted around the selected
    // row instead of rebuilding the list, which moved the selection to the first row.
    readonly property var results: (LauncherSearch.calc !== "" ? [{
                key: "calc",
                kind: "calc",
                text: LauncherSearch.calc
            }] : []).concat(appResults.map(entry => ({
                key: "app:" + entry.id,
                kind: "app",
                entry: entry
            }))).concat(LauncherSearch.files.map(path => ({
                key: "file:" + path,
                kind: "file",
                path: path
            })))
    onOpened: {
        history = Config.launcherHistory ? Apps.launches : {};
        now = Date.now();
        closeMenu();
        search.clear();
        // A recreated panel starts with an empty field, so clear() emits no textChanged: reset the shared search too.
        LauncherSearch.query = "";
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
                onAccepted: root.launch(root.results[apps.currentIndex])
                Keys.onPressed: event => {
                    if (event.key === Qt.Key_P && event.modifiers & Qt.ControlModifier) {
                        root.togglePin(root.results[apps.currentIndex]?.entry);
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
                    color: Theme.selection
                }
                highlightMoveDuration: Theme.motionNormal
                highlightMoveVelocity: -1
                highlightResizeDuration: 0
                model: ScriptModel {
                    values: root.results
                    objectProp: "key"
                }
                delegate: ActionButton {
                    id: row
                    required property var modelData
                    required property int index
                    width: apps.width
                    rightPadding: 40
                    implicitHeight: Theme.hit(40)
                    readonly property var entry: modelData.entry ?? null
                    iconSource: modelData.kind === "calc" ? Quickshell.iconPath("accessories-calculator", "application-x-executable") : modelData.kind === "file" ? Quickshell.iconPath("text-x-generic", "application-x-executable") : Quickshell.iconPath(entry.icon, "application-x-executable")
                    iconSize: 24
                    alignLeft: true
                    textElide: Text.ElideMiddle
                    text: modelData.kind === "calc" ? "= " + modelData.text : modelData.kind === "file" ? modelData.path.replace(Quickshell.env("HOME"), "~") : entry.name + (entry.runInTerminal ? I18n.tr("launcher.terminalSuffix") : "")
                    tooltip: modelData.kind === "calc" ? I18n.tr("launcher.copyResult") : modelData.kind === "file" ? I18n.tr("launcher.openFile") : ""
                    highlighted: apps.currentIndex === index
                    tone: "cursor"
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
                font.pixelSize: Theme.textSize(12)
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
