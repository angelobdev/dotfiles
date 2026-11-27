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
    readonly property var appResults: Rank.rank(DesktopEntries.applications.values.filter(e => !e.noDisplay && !Config.launcherHidden.includes(e.id) && (!appUnits[e.id] || Installed.has(appUnits[e.id]))), query, history, now)
    // What the launcher shows (services/Commands.qml, commands.json): route is the category open, "" the first
    // level; Alt held shows the stand-ins of the commands that have one.
    property string route: ""
    property bool alt: false
    readonly property var routeEntry: Commands.find(route)
    // The Apps category: the apps, as the launcher listed them before the commands.
    readonly property bool inApps: routeEntry?.rows === "apps"
    readonly property string query: search.text.trim()
    // The categories the launcher is in, before the field: "System › Power profile".
    readonly property string crumb: route === "" ? "" : Commands.model.order.filter(id => route === id || route.startsWith(id + ".")).map(id => Commands.label(Commands.find(id))).join(" › ")
    function appItem(entry, note) {
        return {
            key: "app:" + entry.id,
            kind: "app",
            entry: entry,
            note: note ?? ""
        };
    }
    function commandItem(entry, note) {
        const shown = Commands.variant(entry, alt);
        return {
            key: "command:" + entry.id,
            kind: "command",
            entry: shown,
            // A stand-in says what it replaces.
            note: shown !== entry ? Commands.label(entry) : note
        };
    }
    // Each row has a key, so results that arrive later (files, a calculation) are inserted around the selected
    // row instead of rebuilding the list, which moved the selection to the first row.
    readonly property var results: {
        if (inApps)
            return appResults.map(entry => appItem(entry));
        if (query === "") {
            if (routeEntry && routeEntry.rows)
                return Commands.rows(routeEntry).map(entry => commandItem(entry, ""));
            // A category, the first level included: its entries in the order of commands.json, always the same.
            return Commands.entriesOf(route).map(entry => commandItem(entry, ""));
        }
        // Searching: the commands under the category; on the first level the apps too, all by how well they match
        // (an app before a command that matches as well), then a calculation first and files last.
        const found = Commands.matches(query, route).map((match, index) => ({
                    tier: match.tier,
                    kind: 1,
                    index: index,
                    item: commandItem(match.entry, Commands.path(match.entry))
                }));
        if (route === "") {
            const appsLabel = I18n.tr("commands.apps.title");
            appResults.forEach((entry, index) => found.push({
                    tier: Rank.tier(entry, query),
                    kind: 0,
                    index: index,
                    item: appItem(entry, appsLabel)
                }));
        }
        found.sort((a, b) => a.tier - b.tier || a.kind - b.kind || a.index - b.index);
        const rows = found.map(match => match.item);
        if (route !== "")
            return rows;
        return (LauncherSearch.calc !== "" ? [{
                    key: "calc",
                    kind: "calc",
                    text: LauncherSearch.calc
                }] : []).concat(rows).concat(LauncherSearch.files.map(path => ({
                    key: "file:" + path,
                    kind: "file",
                    path: path
                })));
    }
    onOpened: {
        history = Config.launcherHistory ? Apps.launches : {};
        now = Date.now();
        closeMenu();
        alt = false;
        showRoute(ShellState.recall("launcher/commands", ""));
        search.clear();
        // A recreated panel starts with an empty field, so clear() emits no textChanged: reset the shared search too.
        LauncherSearch.query = "";
        apps.currentIndex = 0;
        search.forceActiveFocus();
    }
    // Opens on a category (desktop-shell commands ID), the first level for "" or one that does not exist.
    function showRoute(category) {
        route = Commands.find(category) ? category : "";
        Commands.prepare(routeEntry);
    }
    // The request is read at every opening signal (a panel created open gets two) and dropped once it closes.
    onOpenChanged: if (!open)
        ShellState.remember("launcher/commands", null)
    Connections {
        target: ShellState
        function onCommandsRequested() {
            root.showRoute(ShellState.recall("launcher/commands", ""));
            search.clear();
            apps.currentIndex = 0;
            search.forceActiveFocus();
        }
    }
    // Into a category; the rows of a provider open on the one in use.
    function enter(entry) {
        route = entry.id;
        Commands.prepare(entry);
        search.clear();
        apps.currentIndex = 0;
        Qt.callLater(() => apps.currentIndex = Math.max(0, results.findIndex(item => item.entry?.current)));
    }
    // Esc in a category goes up a level; on the first level it closes (components/Overlay.qml).
    function goBack() {
        if (route === "")
            return false;
        up();
        return true;
    }
    // Up a level, with the category left behind selected.
    function up() {
        const left = route;
        route = routeEntry?.parent ?? "";
        search.clear();
        Qt.callLater(() => apps.currentIndex = Math.max(0, results.findIndex(item => item.entry?.id === left)));
    }
    function launch(item) {
        if (!item)
            return;
        if (item.kind === "command") {
            if (Commands.opens(item.entry))
                enter(item.entry);
            else
                Commands.run(item.entry);
            return;
        }
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
        width: Math.min(Theme.dialogNarrow, parent.width - 48)
        height: Math.min(560, parent.height - 100)
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 14
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                // The category open; a click goes up a level.
                Rectangle {
                    visible: root.route !== ""
                    Layout.maximumWidth: 260
                    implicitWidth: crumbText.implicitWidth + 20
                    implicitHeight: Theme.hit(30)
                    radius: Theme.corner(8)
                    color: Theme.accent
                    Text {
                        id: crumbText
                        anchors.centerIn: parent
                        width: Math.min(implicitWidth, parent.width - 20)
                        text: root.crumb
                        elide: Text.ElideLeft
                        color: Theme.accentText
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                        font.weight: Font.DemiBold
                    }
                    TapHandler {
                        onTapped: root.up()
                    }
                }
                InputField {
                    id: search
                    Layout.fillWidth: true
                    placeholderText: I18n.tr(root.inApps ? "launcher.appsPlaceholder" : root.route !== "" ? "launcher.commandsPlaceholder" : "launcher.searchPlaceholder")
                    color: Theme.text
                    font.family: Theme.font
                    onTextChanged: {
                        apps.currentIndex = 0;
                        // Calculations and files only on the first level.
                        LauncherSearch.query = root.route === "" ? text : "";
                    }
                    Keys.onDownPressed: apps.currentIndex = Math.min(apps.count - 1, apps.currentIndex + 1)
                    Keys.onUpPressed: apps.currentIndex = Math.max(0, apps.currentIndex - 1)
                    onAccepted: root.launch(root.results[apps.currentIndex])
                    Keys.onPressed: event => {
                        const current = root.results[apps.currentIndex];
                        const opens = !!current && current.kind === "command" && Commands.opens(current.entry);
                        if (event.key === Qt.Key_Alt) {
                            root.alt = true;
                        } else if (event.key === Qt.Key_P && event.modifiers & Qt.ControlModifier) {
                            root.togglePin(current?.kind === "app" ? current.entry : null);
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Right && cursorPosition === text.length && opens) {
                            // Into the category selected.
                            if (opens)
                                root.enter(current.entry);
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Left && text === "" && root.route !== "") {
                            root.up();
                            event.accepted = true;
                        } else if (event.key === Qt.Key_Backspace && text === "" && root.route !== "") {
                            root.up();
                            event.accepted = true;
                        }
                    }
                    Keys.onReleased: event => {
                        if (event.key === Qt.Key_Alt)
                            root.alt = false;
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
                    implicitHeight: Theme.hit(40)
                    // An app (its desktop entry) or a command (services/Commands.qml).
                    readonly property var entry: modelData.kind === "app" ? modelData.entry : null
                    readonly property var command: modelData.kind === "command" ? modelData.entry : null
                    readonly property string switchState: command ? Commands.switchState(command) : ""
                    readonly property bool opens: !!command && Commands.opens(command)
                    readonly property bool marked: switchState !== "" || opens || !!command?.current || !!entry && Dock.isPinned(entry.id)
                    // What a row shows on its right: where a command is, why it is off, what Alt replaced, or Apps
                    // beside an app found from the first level.
                    readonly property string note: command && !Commands.enabled(command) && command.reason ? I18n.tr(command.reason) : modelData.note ?? ""
                    // The keys of its bind, as Hints shows them.
                    readonly property var keys: command ? Commands.keysOf(command) : []
                    rightPadding: 24 + trail.width
                    enabled: !command || Commands.enabled(command)
                    iconName: command ? (command.icon ?? "") : ""
                    iconSource: command ? "" : modelData.kind === "calc" ? Quickshell.iconPath("accessories-calculator", "application-x-executable") : modelData.kind === "file" ? Quickshell.iconPath("text-x-generic", "application-x-executable") : Quickshell.iconPath(entry.icon, "application-x-executable")
                    iconSize: command ? 20 : 24
                    alignLeft: true
                    textElide: command ? Text.ElideRight : Text.ElideMiddle
                    text: command ? Commands.label(command) : modelData.kind === "calc" ? "= " + modelData.text : modelData.kind === "file" ? modelData.path.replace(Quickshell.env("HOME"), "~") : entry.name + (entry.runInTerminal ? I18n.tr("launcher.terminalSuffix") : "")
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
                    // On the right, in a row: the note, the keys of the bind of a command, then its mark: the
                    // switch of a command (drawn: the row is what is pressed), the arrow of a category, the dot of the
                    // chosen row, the pin of a pinned app.
                    Row {
                        id: trail
                        anchors {
                            right: parent.right
                            rightMargin: 14
                            verticalCenter: parent.verticalCenter
                        }
                        spacing: 8
                        Text {
                            id: noteText
                            anchors.verticalCenter: parent.verticalCenter
                            visible: text !== ""
                            width: Math.min(implicitWidth, row.width * 0.3)
                            text: row.note
                            elide: Text.ElideLeft
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(12)
                        }
                        Row {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: row.keys.length > 0
                            spacing: 3
                            Repeater {
                                model: row.keys
                                Rectangle {
                                    id: keycap
                                    required property string modelData
                                    width: Math.max(height, capText.implicitWidth + 10)
                                    height: capText.implicitHeight + 4
                                    radius: Theme.corner(4)
                                    color: "transparent"
                                    border.width: 1
                                    border.color: Theme.stroke
                                    Text {
                                        id: capText
                                        anchors.centerIn: parent
                                        text: keycap.modelData
                                        textFormat: Text.PlainText
                                        color: Theme.muted
                                        font.family: Theme.font
                                        font.pixelSize: Theme.textSize(11)
                                    }
                                }
                            }
                        }
                        Item {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: row.marked
                            width: 34
                            height: 20
                            Rectangle {
                                anchors.right: parent.right
                                visible: row.switchState !== ""
                                width: 34
                                height: 20
                                radius: Theme.corner(10)
                                color: row.switchState === "on" ? Theme.active : Theme.track
                                Rectangle {
                                    x: row.switchState === "on" ? parent.width - width - 3 : 3
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 14
                                    height: 14
                                    radius: Theme.corner(7)
                                    color: row.switchState === "on" ? Theme.accent : Theme.muted
                                }
                            }
                            Icon {
                                anchors {
                                    right: parent.right
                                    verticalCenter: parent.verticalCenter
                                }
                                width: 16
                                height: 16
                                visible: row.opens
                                name: "chevron-right"
                                color: row.highlighted ? Theme.text : Theme.muted
                            }
                            Rectangle {
                                anchors {
                                    right: parent.right
                                    rightMargin: 4
                                    verticalCenter: parent.verticalCenter
                                }
                                visible: !!row.command?.current
                                width: 8
                                height: 8
                                radius: 4
                                color: Theme.accent
                            }
                            // Only pinned apps carry a mark; the hint below says how to pin.
                            Icon {
                                anchors {
                                    right: parent.right
                                    verticalCenter: parent.verticalCenter
                                }
                                width: 16
                                height: 16
                                visible: !!row.entry && Dock.isPinned(row.entry.id)
                                name: "pin"
                                color: row.highlighted ? Theme.accentText : Theme.muted
                            }
                        }
                    }
                }
                ScrollBar.vertical: ScrollBar {}
                Text {
                    anchors.centerIn: parent
                    visible: apps.count === 0
                    text: I18n.tr(root.inApps ? "launcher.empty" : root.query !== "" ? "launcher.noResults" : "launcher.noCommands")
                    color: Theme.muted
                }
            }
            // Touch has no arrows, Enter or Ctrl+P: the gestures instead. Both wrap, so a wide theme font (Fira Code)
            // or a long translation does not run past the card.
            Text {
                visible: Tablet.active
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: I18n.tr("launcher.touchHint")
                color: Theme.muted
                font.pixelSize: Theme.textSize(12)
            }
            KeyHints {
                visible: !Tablet.active
                hints: I18n.tr(root.inApps ? "launcher.navigationHint" : "launcher.commandsHint")
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
