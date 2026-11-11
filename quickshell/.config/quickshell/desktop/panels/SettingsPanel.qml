import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "theming"
import "settings"
import "network"
import "bluetooth"
import "displays"
import "audio"
import "agent"
import "system"
import "settings/SettingsSearch.js" as Search

// Settings: one entry point for configuring the desktop, after GNOME Settings. A sidebar of sections on the
// left, the chosen section on the right; on a narrow screen one of the two at a time, with Back. Sections are
// built the first time they show, then kept while the panel is loaded (components/LazyPanel.qml). A search
// field tops the sidebar: while it has text, the sidebar lists the matching sections, tabs and options.
Overlay {
    id: root
    panelName: "settings"
    dialog: true
    // Every section, in sidebar order and grouped under a label (settings.sidebar.<group>), after GNOME Settings. Network, Bluetooth, Displays and Sound show the views
    // of their quick panels, Appearance the Theming view; the others are built from SettingsSchema.js
    // (settings/OptionsSection.qml).
    // Labels as catalog keys, translated where shown: a translation reload would otherwise make a new array, and the
    // page Repeater below would rebuild every page visited so far (scroll, focus and half-typed values lost).
    readonly property var sections: [
        {
            name: "network",
            icon: "wifi",
            labelKey: "settings.sections.network",
            group: "connections"
        },
        {
            name: "bluetooth",
            icon: "bluetooth",
            labelKey: "settings.sections.bluetooth",
            group: "connections"
        },
        {
            name: "displays",
            icon: "monitor",
            labelKey: "settings.sections.displays",
            group: "devices"
        },
        {
            name: "sound",
            icon: "volume-high",
            labelKey: "settings.sections.sound",
            group: "devices"
        },
        {
            name: "power",
            icon: "battery-75",
            labelKey: "settings.sections.power",
            group: "devices"
        },
        {
            name: "appearance",
            icon: "palette",
            labelKey: "settings.sections.appearance",
            group: "personalization"
        },
        {
            name: "desktop",
            icon: "apps",
            labelKey: "settings.sections.desktop",
            group: "personalization"
        },
        {
            name: "assistant",
            icon: "assistant",
            labelKey: "settings.sections.assistant",
            group: "personalization",
            // Only with the AI Assistant profile installed (services/Installed.qml).
            unit: "assistant"
        },
        {
            name: "keyboard",
            icon: "keyboard",
            labelKey: "settings.sections.keyboard",
            group: "input"
        },
        {
            name: "tablet",
            icon: "rotate",
            labelKey: "settings.sections.tablet",
            group: "input"
        },
        {
            name: "privacy",
            icon: "eye-off",
            labelKey: "settings.sections.privacy",
            group: "system"
        },
        {
            name: "system",
            icon: "controls",
            labelKey: "settings.sections.system",
            group: "system"
        }
    ]
    // Names that open a tab of a section: the updates panel links to System → Updates.
    readonly property var sectionAliases: ({
            updates: ["system", "updates"],
            plugins: ["system", "plugins"]
        })
    readonly property var sectionNames: sections.map(entry => entry.name)
    readonly property var groupLabels: ({
            connections: I18n.tr("settings.sidebar.connections"),
            devices: I18n.tr("settings.sidebar.devices"),
            personalization: I18n.tr("settings.sidebar.personalization"),
            input: I18n.tr("settings.sidebar.input"),
            system: I18n.tr("settings.sidebar.system")
        })
    // The sidebar: each group's label, then its sections.
    readonly property var sidebarRows: {
        const rows = [];
        for (const entry of sections) {
            if (entry.unit && !Installed.has(entry.unit))
                continue;
            if (rows.length === 0 || rows[rows.length - 1].group !== entry.group)
                rows.push({
                    heading: true,
                    group: entry.group,
                    label: groupLabels[entry.group] ?? entry.group
                });
            rows.push(entry);
        }
        return rows;
    }
    // Up and down in the sidebar skip the labels; false at either end.
    function sidebarStep(step) {
        let index = sidebarRows.findIndex(row => !row.heading && row.name === section);
        do
            index += step;
        while (index >= 0 && index < sidebarRows.length && sidebarRows[index].heading);
        if (index < 0 || index >= sidebarRows.length)
            return false;
        showSection(sidebarRows[index].name, "");
        return true;
    }
    property string section: ShellState.recall("settings/section", "appearance")
    onSectionChanged: {
        ShellState.remember("settings/section", section);
        if (!visited.includes(section))
            visited = visited.concat([section]);
    }
    // Narrow screens show the sidebar or a section, not both; Back returns to the sidebar.
    readonly property bool compact: card.width < 820
    // The widest a section of option rows and lists grows, so a label and its control stay within reach of each
    // other; the sections that use the room (grids, the monitor list, tabs with logs) take the whole width.
    readonly property int readableWidth: 720
    readonly property var wideSections: ["appearance", "displays", "system"]
    // Sections that show a view without a key footer (no keys of their own beyond Tab): the panel adds one with
    // the keys it handles there.
    readonly property var viewSections: ["network", "bluetooth", "displays", "sound", "assistant", "system"]
    property bool showingSidebar: false
    // The page of the Appearance section, for IPC (shell.qml theming()); set when it loads.
    property var appearance: null
    // A tab asked for before its section page existed.
    property string requestedTab: ""
    // Sections shown at least once: their pages stay loaded. The one it opens on counts too: onSectionChanged does
    // not run for the initial value, and its page would be rebuilt after the first switch. Written here and in
    // onSectionChanged, never from a Loader, so the active bindings below do not loop.
    property var visited: []
    Component.onCompleted: visited = [section]
    // The search: while it has text, the sidebar shows what matches (SettingsSearch.js), in the language shown and
    // among the sections shown.
    readonly property string query: searchField.text
    readonly property bool searching: query.trim() !== ""
    readonly property var searchResults: searching ? Search.find(Search.entries(key => I18n.tr(key), sidebarRows.filter(row => !row.heading)), query) : []
    // The result Up and Down are on, which Enter opens.
    property int searchCurrent: 0
    onQueryChanged: searchCurrent = 0

    // Ctrl+F, or / on the sidebar: the search field, its text selected to type over; on a narrow screen the
    // sidebar shows first.
    function focusSearch() {
        if (compact)
            showingSidebar = true;
        searchField.forceActiveFocus();
        searchField.selectAll();
    }
    function searchStep(step) {
        if (searchResults.length === 0)
            return;
        searchCurrent = Math.max(0, Math.min(searchResults.length - 1, searchCurrent + step));
        results.positionViewAtIndex(searchCurrent, ListView.Contain);
    }
    // A result: its section, with its tab, and for an option its row, scrolled to and made the current one. The
    // results stay, to try the next one; Esc clears them.
    function openResult(entry) {
        if (!entry)
            return;
        searchCurrent = Math.max(0, searchResults.indexOf(entry));
        showSection(entry.section, entry.tab);
        const page = pages.itemAt(sectionNames.indexOf(entry.section))?.item;
        if (entry.key !== "")
            page?.reveal?.(entry.key);
        else if (entry.section === "system")
            Qt.callLater(() => page?.focusItem?.forceActiveFocus());
    }
    // Esc clears the search first, then goes back inside a section (the details of a network), then closes.
    function escapePressed() {
        if (searchField.text !== "") {
            searchField.clear();
            return;
        }
        const page = pages.itemAt(sectionNames.indexOf(section))?.item;
        if (!(page?.goBack?.() ?? false))
            ShellState.close();
    }

    // A section by name, an unknown one falls back to the first. tab: a tab inside it (Appearance), "" for the
    // one it remembers.
    function showSection(name, tab) {
        // "section/tab" names a tab too (system/advanced, appearance/font).
        if (name.includes("/")) {
            tab = name.split("/")[1];
            name = name.split("/")[0];
        }
        const alias = sectionAliases[name];
        if (alias) {
            name = alias[0];
            tab = alias[1];
        }
        section = sectionNames.includes(name) ? name : sectionNames[0];
        showingSidebar = false;
        // Set above, so the page is loaded by now, unless the panel is being created: then the page takes the
        // tab when it loads (requestedTab).
        const item = pages.itemAt(sectionNames.indexOf(section))?.item;
        requestedTab = item ? "" : (tab ?? "");
        if (item && (section === "appearance" || section === "system"))
            item.open(tab ?? "");
        else
            Qt.callLater(() => pages.itemAt(sectionNames.indexOf(section))?.item?.focusItem?.forceActiveFocus());
    }
    // ShellState.openSection keeps the section asked for; another one asked while open moves there. A search left
    // from the last time is gone.
    onOpened: {
        searchField.clear();
        showSection(ShellState.recall("settings/section", section), "");
    }
    closeOnEscape: false
    contentItem.Keys.onEscapePressed: root.escapePressed()
    Connections {
        target: ShellState
        function onSectionRequested(name, section) {
            if (name === root.panelName)
                root.showSection(section, "");
        }
    }
    // Ctrl+F: the search, from anywhere in the panel (text fields of the pages have no use for it).
    Shortcut {
        enabled: root.open
        sequence: "Ctrl+F"
        onActivated: root.focusSearch()
    }
    Card {
        id: card
        anchors.centerIn: parent
        width: Math.min(Theme.dialogSettings, parent.width - 48)
        height: Math.min(760, parent.height - 96)
        RowLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: Theme.dialogPadding
            // Sidebar: the panel title, the search, and one row per section, or the results while searching.
            ColumnLayout {
                visible: !root.compact || root.showingSidebar
                Layout.fillHeight: true
                Layout.fillWidth: root.compact
                Layout.preferredWidth: root.compact ? -1 : 220
                spacing: 14
                Heading {
                    Layout.fillWidth: true
                    text: I18n.tr("settings.title")
                }
                InputField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: I18n.tr("settings.search.placeholder")
                    Accessible.name: I18n.tr("settings.search.placeholder")
                    // Up and down pick a result; with nothing typed, down goes to the sections.
                    Keys.onUpPressed: root.searchStep(-1)
                    Keys.onDownPressed: {
                        if (root.searching)
                            root.searchStep(1);
                        else
                            sidebar.forceActiveFocus();
                    }
                    Keys.onEscapePressed: root.escapePressed()
                    onAccepted: root.openResult(root.searchResults[root.searchCurrent])
                }
                ListView {
                    id: sidebar
                    visible: !root.searching
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 2
                    model: root.sidebarRows
                    currentIndex: Math.max(0, root.sidebarRows.findIndex(row => !row.heading && row.name === root.section))
                    keyNavigationEnabled: false
                    highlightMoveDuration: Theme.motionNormal
                    Accessible.role: Accessible.List
                    Accessible.name: I18n.tr("settings.title")
                    // Up from the first section goes to the search.
                    Keys.onUpPressed: {
                        if (!root.sidebarStep(-1))
                            searchField.forceActiveFocus();
                    }
                    Keys.onDownPressed: root.sidebarStep(1)
                    // "/" starts a search; other keys stay with the list.
                    Keys.onPressed: event => {
                        if (event.text === "/") {
                            root.focusSearch();
                            event.accepted = true;
                        }
                    }
                    // A group label, or a section.
                    delegate: Item {
                        id: sidebarRow
                        required property var modelData
                        required property int index
                        width: sidebar.width
                        height: modelData.heading ? Theme.hit(30) : Theme.hit(38)
                        Text {
                            visible: sidebarRow.modelData.heading === true
                            anchors {
                                left: parent.left
                                leftMargin: 10
                                bottom: parent.bottom
                                bottomMargin: 6
                            }
                            // Only group rows have a label; section rows draw their ActionButton instead.
                            text: sidebarRow.modelData.label ?? ""
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                            font.weight: Font.DemiBold
                        }
                        ActionButton {
                            visible: sidebarRow.modelData.heading !== true
                            anchors.fill: parent
                            alignLeft: true
                            iconName: sidebarRow.modelData.icon ?? ""
                            text: I18n.tr(sidebarRow.modelData.labelKey)
                            highlighted: sidebarRow.modelData.name === root.section
                            tone: "state"
                            onClicked: root.showSection(sidebarRow.modelData.name, "")
                        }
                    }
                }
                // The results: "Section › Group › Option" (or "Section › Tab"), the group and the separators muted,
                // wrapping on the narrow sidebar.
                ListView {
                    id: results
                    visible: root.searching && root.searchResults.length > 0
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 2
                    model: root.searchResults
                    currentIndex: root.searchCurrent
                    keyNavigationEnabled: false
                    Accessible.role: Accessible.List
                    Accessible.name: I18n.tr("settings.search.results")
                    Keys.onUpPressed: root.searchStep(-1)
                    Keys.onDownPressed: root.searchStep(1)
                    delegate: ActionButton {
                        id: result
                        required property var modelData
                        required property int index
                        width: results.width
                        implicitWidth: results.width
                        implicitHeight: Math.max(Theme.hit(38), resultPath.implicitHeight + topPadding + bottomPadding)
                        alignLeft: true
                        text: modelData.path.join(" › ")
                        highlighted: index === root.searchCurrent
                        tone: "cursor"
                        onClicked: root.openResult(modelData)
                        contentItem: Item {
                            implicitHeight: resultPath.implicitHeight
                            Flow {
                                id: resultPath
                                anchors {
                                    left: parent.left
                                    right: parent.right
                                    verticalCenter: parent.verticalCenter
                                }
                                Repeater {
                                    model: result.modelData.path
                                    // One part of the path, and the separator after it but the last.
                                    Row {
                                        id: part
                                        required property string modelData
                                        required property int index
                                        readonly property bool last: index === result.modelData.path.length - 1
                                        Text {
                                            width: Math.min(implicitWidth, resultPath.width - (part.last ? 0 : separator.implicitWidth))
                                            text: part.modelData
                                            wrapMode: Text.Wrap
                                            color: part.index === 0 || part.last ? result.foreground : Theme.muted
                                            font: result.font
                                            textFormat: Text.PlainText
                                        }
                                        Text {
                                            id: separator
                                            visible: !part.last
                                            text: " › "
                                            color: Theme.muted
                                            font: result.font
                                            textFormat: Text.PlainText
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                Text {
                    visible: root.searching && root.searchResults.length === 0
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    leftPadding: 10
                    rightPadding: 10
                    verticalAlignment: Text.AlignTop
                    text: I18n.tr("settings.search.noResults", [root.query.trim()])
                    wrapMode: Text.Wrap
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(12)
                    textFormat: Text.PlainText
                }
            }
            Rectangle {
                visible: !root.compact
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                color: Theme.stroke
            }
            // The chosen section.
            ColumnLayout {
                visible: !root.compact || !root.showingSidebar
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10
                ActionButton {
                    visible: root.compact
                    iconName: "arrow-left"
                    text: I18n.tr("settings.title")
                    onClicked: {
                        root.showingSidebar = true;
                        (root.searching ? searchField : sidebar).forceActiveFocus();
                    }
                }
                StackLayout {
                    Layout.fillWidth: true
                    Layout.maximumWidth: root.wideSections.includes(root.section) ? Number.POSITIVE_INFINITY : root.readableWidth
                    Layout.fillHeight: true
                    currentIndex: root.sectionNames.indexOf(root.section)
                    // One page per section, in sidebar order, built the first time it shows.
                    Repeater {
                        id: pages
                        model: root.sections
                        Loader {
                            id: page
                            required property var modelData
                            // This section is on screen: its view scans, polls and lists only then.
                            readonly property bool shownHere: root.open && root.section === modelData.name && (!root.compact || !root.showingSidebar)
                            // Built the first time it shows, then kept (root.visited, set outside this binding).
                            active: root.visited.includes(modelData.name) || root.section === modelData.name
                            onLoaded: {
                                if (modelData.name === "appearance")
                                    root.appearance = item;
                                if (root.section === modelData.name && item.open) {
                                    item.open(root.requestedTab);
                                    root.requestedTab = "";
                                }
                            }
                            sourceComponent: ({
                                    appearance: appearanceView,
                                    network: networkView,
                                    bluetooth: bluetoothView,
                                    displays: displaysView,
                                    sound: soundView,
                                    assistant: assistantView,
                                    system: systemView,
                                    keyboard: keyboardView,
                                    power: powerView,
                                    privacy: privacyView
                                })[modelData.name] ?? optionsView
                            // Appearance: the theme, wallpaper, font, icons and cursors (panels/theming).
                            Component {
                                id: appearanceView
                                ThemingView {
                                    title: I18n.tr(page.modelData.labelKey)
                                    active: root.open && root.section === "appearance" && (!root.compact || !root.showingSidebar)
                                }
                            }
                            // Network: the title follows the network whose details are open, with Back to the list.
                            Component {
                                id: networkView
                                ColumnLayout {
                                    readonly property Item focusItem: network.focusItem
                                    readonly property bool inDetails: network.inDetails
                                    function goBack() {
                                        return network.goBack();
                                    }
                                    spacing: 14
                                    RowLayout {
                                        Layout.fillWidth: true
                                        PanelIconButton {
                                            visible: network.inDetails
                                            iconName: "arrow-left"
                                            tooltip: I18n.tr("network.title")
                                            onClicked: network.closeDetails()
                                        }
                                        Heading {
                                            Layout.fillWidth: true
                                            text: network.inDetails ? network.title : I18n.tr(page.modelData.labelKey)
                                            elide: Text.ElideRight
                                        }
                                    }
                                    NetworkView {
                                        id: network
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        shown: page.shownHere
                                    }
                                }
                            }
                            Component {
                                id: bluetoothView
                                ColumnLayout {
                                    readonly property Item focusItem: bluetooth.focusItem
                                    spacing: 14
                                    Heading {
                                        Layout.fillWidth: true
                                        text: I18n.tr(page.modelData.labelKey)
                                    }
                                    BluetoothView {
                                        id: bluetooth
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        shown: page.shownHere
                                    }
                                }
                            }
                            Component {
                                id: displaysView
                                ColumnLayout {
                                    readonly property Item focusItem: displays.focusItem
                                    spacing: 14
                                    Heading {
                                        Layout.fillWidth: true
                                        text: I18n.tr(page.modelData.labelKey)
                                    }
                                    DisplayView {
                                        id: displays
                                        Layout.fillWidth: true
                                        shown: page.shownHere
                                    }
                                    MonitorSettings {
                                        shown: page.shownHere
                                    }
                                    Item {
                                        Layout.fillHeight: true
                                    }
                                }
                            }
                            Component {
                                id: soundView
                                ColumnLayout {
                                    readonly property Item focusItem: sound.focusItem
                                    spacing: 14
                                    Heading {
                                        Layout.fillWidth: true
                                        text: I18n.tr(page.modelData.labelKey)
                                    }
                                    AudioView {
                                        id: sound
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                    }
                                }
                            }
                            Component {
                                id: assistantView
                                ColumnLayout {
                                    readonly property Item focusItem: assistant.focusItem
                                    spacing: 14
                                    Heading {
                                        Layout.fillWidth: true
                                        text: I18n.tr(page.modelData.labelKey)
                                    }
                                    AgentView {
                                        id: assistant
                                        Layout.fillWidth: true
                                        shown: page.shownHere
                                    }
                                    AgentsGroup {}
                                    AssistantLanguage {}
                                    Item {
                                        Layout.fillHeight: true
                                    }
                                }
                            }
                            // System: About, Updates and Advanced, as tabs.
                            Component {
                                id: systemView
                                SystemView {
                                    title: I18n.tr(page.modelData.labelKey)
                                    shown: page.shownHere
                                    readableWidth: root.readableWidth
                                }
                            }
                            // Keyboard: the on-screen keyboard options, then the layout and personal shortcuts.
                            Component {
                                id: keyboardView
                                OptionsSection {
                                    section: page.modelData.name
                                    title: I18n.tr(page.modelData.labelKey)
                                    KeyboardHyprland {}
                                }
                            }
                            // Power: the battery warnings, then the power profile of the battery panel.
                            Component {
                                id: powerView
                                OptionsSection {
                                    section: page.modelData.name
                                    title: I18n.tr(page.modelData.labelKey)
                                    PowerProfileGroup {}
                                }
                            }
                            // Privacy: the schema options, with how many apps the launch history holds and its Clear
                            // in the Launcher card.
                            Component {
                                id: privacyView
                                OptionsSection {
                                    section: page.modelData.name
                                    title: I18n.tr(page.modelData.labelKey)
                                    groupRows: ({
                                            launcher: launchHistoryRow
                                        })
                                }
                            }
                            Component {
                                id: launchHistoryRow
                                RowLayout {
                                    spacing: 14
                                    Text {
                                        Layout.fillWidth: true
                                        text: Apps.remembered > 0 ? I18n.plural("settings.launchHistory.count.one", "settings.launchHistory.count.other", Apps.remembered) : I18n.tr("settings.launchHistory.none")
                                        wrapMode: Text.WordWrap
                                        color: Theme.muted
                                        font.family: Theme.font
                                        font.pixelSize: Theme.textSize(12)
                                    }
                                    ActionButton {
                                        outlined: true
                                        enabled: Apps.remembered > 0
                                        text: I18n.tr("settings.launchHistory.clear")
                                        onClicked: Apps.clearHistory()
                                    }
                                }
                            }
                            Component {
                                id: optionsView
                                OptionsSection {
                                    section: page.modelData.name
                                    title: I18n.tr(page.modelData.labelKey)
                                }
                            }
                        }
                    }
                }
                // The keys the panel handles on the sections that show a view with none of its own (the option pages
                // and Appearance list these with theirs). Esc goes back from the details of a network first.
                KeyHints {
                    visible: !Tablet.active && root.viewSections.includes(root.section)
                    Layout.maximumWidth: root.wideSections.includes(root.section) ? Number.POSITIVE_INFINITY : root.readableWidth
                    // pages.count: the binding runs again once the pages exist, and then follows the network page.
                    hints: root.section === "network" && pages.count > 0 && (pages.itemAt(root.sectionNames.indexOf("network"))?.item?.inDetails ?? false) ? I18n.tr("settings.pageDetailsHint") : I18n.tr("settings.pageHint")
                }
            }
        }
        // Close, at the top right on every section and on the sidebar alone (compact): the titles and Back are at the
        // left, and the tabs of Appearance and System on the row below their title. Offset by its own padding, so the
        // glyph lines up with the content edge and the section title.
        PanelIconButton {
            anchors {
                top: parent.top
                right: parent.right
                margins: Theme.dialogPadding - 7
            }
            iconName: "close"
            tooltip: I18n.tr("common.close")
            onClicked: ShellState.close()
        }
    }
}
