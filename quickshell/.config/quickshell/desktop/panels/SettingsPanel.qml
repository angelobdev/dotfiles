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

// Settings: one entry point for configuring the desktop, after GNOME Settings. A sidebar of sections on the
// left, the chosen section on the right; on a narrow screen one of the two at a time, with Back. Sections are
// built the first time they show, then kept while the panel is loaded (components/LazyPanel.qml).
Overlay {
    id: root
    panelName: "settings"
    dialog: true
    // Every section, in sidebar order and grouped under a label (settings.sidebar.<group>), after GNOME Settings. Network, Bluetooth, Displays and Sound show the views
    // of their quick panels, Appearance the Theming view; the others are built from SettingsSchema.js
    // (settings/OptionsSection.qml).
    readonly property var sections: [
        {
            name: "network",
            icon: "wifi",
            label: I18n.tr("settings.sections.network"),
            group: "connections"
        },
        {
            name: "bluetooth",
            icon: "bluetooth",
            label: I18n.tr("settings.sections.bluetooth"),
            group: "connections"
        },
        {
            name: "displays",
            icon: "monitor",
            label: I18n.tr("settings.sections.displays"),
            group: "devices"
        },
        {
            name: "sound",
            icon: "volume-high",
            label: I18n.tr("settings.sections.sound"),
            group: "devices"
        },
        {
            name: "power",
            icon: "battery-75",
            label: I18n.tr("settings.sections.power"),
            group: "devices"
        },
        {
            name: "appearance",
            icon: "palette",
            label: I18n.tr("settings.sections.appearance"),
            group: "personalization"
        },
        {
            name: "desktop",
            icon: "apps",
            label: I18n.tr("settings.sections.desktop"),
            group: "personalization"
        },
        {
            name: "assistant",
            icon: "assistant",
            label: I18n.tr("settings.sections.assistant"),
            group: "personalization"
        },
        {
            name: "keyboard",
            icon: "keyboard",
            label: I18n.tr("settings.sections.keyboard"),
            group: "input"
        },
        {
            name: "tablet",
            icon: "rotate",
            label: I18n.tr("settings.sections.tablet"),
            group: "input"
        },
        {
            name: "privacy",
            icon: "eye-off",
            label: I18n.tr("settings.sections.privacy"),
            group: "system"
        },
        {
            name: "system",
            icon: "controls",
            label: I18n.tr("settings.sections.system"),
            group: "system"
        }
    ]
    // Names that open a tab of a section: the updates panel links to System → Updates.
    readonly property var sectionAliases: ({
            updates: ["system", "updates"]
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
    // Up and down in the sidebar skip the labels.
    function sidebarStep(step) {
        let index = sidebarRows.findIndex(row => !row.heading && row.name === section);
        do
            index += step;
        while (index >= 0 && index < sidebarRows.length && sidebarRows[index].heading);
        if (index >= 0 && index < sidebarRows.length)
            showSection(sidebarRows[index].name, "");
    }
    property string section: ShellState.recall("settings/section", "appearance")
    onSectionChanged: ShellState.remember("settings/section", section)
    // Narrow screens show the sidebar or a section, not both; Back returns to the sidebar.
    readonly property bool compact: card.width < 820
    property bool showingSidebar: false
    // The page of the Appearance section, for IPC (shell.qml theming()); set when it loads.
    property var appearance: null
    // A tab asked for before its section page existed.
    property string requestedTab: ""
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
    // ShellState.openSection keeps the section asked for; another one asked while open moves there.
    onOpened: showSection(ShellState.recall("settings/section", section), "")
    // Esc goes back inside a section first (the details of a network), then closes.
    closeOnEscape: false
    contentItem.Keys.onEscapePressed: {
        const page = pages.itemAt(sectionNames.indexOf(section))?.item;
        if (!(page?.goBack?.() ?? false))
            ShellState.close();
    }
    Connections {
        target: ShellState
        function onSectionRequested(name, section) {
            if (name === root.panelName)
                root.showSection(section, "");
        }
    }
    Card {
        id: card
        anchors.centerIn: parent
        width: Math.min(1240, parent.width - 48)
        height: Math.min(760, parent.height - 96)
        RowLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: Theme.dialogPadding
            // Sidebar: the panel title and one row per section.
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
                ListView {
                    id: sidebar
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
                    Keys.onUpPressed: root.sidebarStep(-1)
                    Keys.onDownPressed: root.sidebarStep(1)
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
                            text: sidebarRow.modelData.label
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
                            text: sidebarRow.modelData.label
                            highlighted: sidebarRow.modelData.name === root.section
                            onClicked: root.showSection(sidebarRow.modelData.name, "")
                        }
                    }
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
                        sidebar.forceActiveFocus();
                    }
                }
                StackLayout {
                    Layout.fillWidth: true
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
                            property bool visited: false
                            active: visited || root.section === modelData.name
                            onLoaded: {
                                visited = true;
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
                                    keyboard: keyboardView
                                })[modelData.name] ?? optionsView
                            // Appearance: the theme, wallpaper, font, icons and cursors (panels/theming).
                            Component {
                                id: appearanceView
                                ThemingView {
                                    title: page.modelData.label
                                    active: root.open && root.section === "appearance" && (!root.compact || !root.showingSidebar)
                                }
                            }
                            // Network: the title follows the network whose details are open, with Back to the list.
                            Component {
                                id: networkView
                                ColumnLayout {
                                    readonly property Item focusItem: network.focusItem
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
                                            text: network.inDetails ? network.title : page.modelData.label
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
                                        text: page.modelData.label
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
                                        text: page.modelData.label
                                    }
                                    DisplayView {
                                        id: displays
                                        Layout.fillWidth: true
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
                                        text: page.modelData.label
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
                                        text: page.modelData.label
                                    }
                                    AgentView {
                                        id: assistant
                                        Layout.fillWidth: true
                                        shown: page.shownHere
                                    }
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
                                    title: page.modelData.label
                                    shown: page.shownHere
                                }
                            }
                            // Keyboard: the on-screen keyboard options, then the layout and personal shortcuts.
                            Component {
                                id: keyboardView
                                OptionsSection {
                                    section: page.modelData.name
                                    title: page.modelData.label
                                    KeyboardHyprland {}
                                }
                            }
                            Component {
                                id: optionsView
                                OptionsSection {
                                    section: page.modelData.name
                                    title: page.modelData.label
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
