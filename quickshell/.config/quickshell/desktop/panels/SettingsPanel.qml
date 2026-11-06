import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "theming"
import "settings"

// Settings: one entry point for configuring the desktop, after GNOME Settings. A sidebar of sections on the
// left, the chosen section on the right; on a narrow screen one of the two at a time, with Back. Sections are
// built the first time they show, then kept while the panel is loaded (components/LazyPanel.qml).
Overlay {
    id: root
    panelName: "settings"
    dialog: true
    // Every section, in sidebar order. Appearance has its own view; the others are built from
    // SettingsSchema.js (settings/OptionsSection.qml).
    readonly property var sections: [
        {
            name: "appearance",
            icon: "palette",
            label: I18n.tr("settings.sections.appearance")
        },
        {
            name: "desktop",
            icon: "apps",
            label: I18n.tr("settings.sections.desktop")
        },
        {
            name: "keyboard",
            icon: "keyboard",
            label: I18n.tr("settings.sections.keyboard")
        },
        {
            name: "tablet",
            icon: "rotate",
            label: I18n.tr("settings.sections.tablet")
        },
        {
            name: "power",
            icon: "battery-75",
            label: I18n.tr("settings.sections.power")
        },
        {
            name: "privacy",
            icon: "eye-off",
            label: I18n.tr("settings.sections.privacy")
        }
    ]
    readonly property var sectionNames: sections.map(entry => entry.name)
    property string section: ShellState.recall("settings/section", "appearance")
    onSectionChanged: ShellState.remember("settings/section", section)
    // Narrow screens show the sidebar or a section, not both; Back returns to the sidebar.
    readonly property bool compact: card.width < 820
    property bool showingSidebar: false
    // The page of the Appearance section, for IPC (shell.qml theming()); set when it loads.
    property var appearance: null
    // A section by name, an unknown one falls back to the first. tab: a tab inside it (Appearance), "" for the
    // one it remembers.
    function showSection(name, tab) {
        section = sectionNames.includes(name) ? name : sectionNames[0];
        showingSidebar = false;
        // Set above, so the section's page is loaded by now.
        if (section === "appearance")
            appearance?.open(tab ?? "");
        else
            Qt.callLater(() => pages.itemAt(sectionNames.indexOf(section))?.item?.focusItem?.forceActiveFocus());
    }
    // ShellState.openSection keeps the section asked for; another one asked while open moves there.
    onOpened: showSection(ShellState.recall("settings/section", section), "")
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
                    spacing: 3
                    model: root.sections
                    currentIndex: Math.max(0, root.sectionNames.indexOf(root.section))
                    keyNavigationEnabled: true
                    highlightMoveDuration: Theme.motionNormal
                    Accessible.role: Accessible.List
                    Accessible.name: I18n.tr("settings.title")
                    Keys.onReturnPressed: root.showSection(root.sectionNames[currentIndex], "")
                    Keys.onEnterPressed: root.showSection(root.sectionNames[currentIndex], "")
                    delegate: ActionButton {
                        required property var modelData
                        required property int index
                        width: sidebar.width
                        implicitHeight: Theme.hit(44)
                        alignLeft: true
                        iconName: modelData.icon
                        text: modelData.label
                        highlighted: modelData.name === root.section
                        onClicked: root.showSection(modelData.name, "")
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
                            property bool visited: false
                            active: visited || root.section === modelData.name
                            onLoaded: {
                                visited = true;
                                if (modelData.name === "appearance")
                                    root.appearance = item;
                            }
                            sourceComponent: modelData.name === "appearance" ? appearanceView : optionsView
                            // Appearance: the theme, wallpaper, font, icons and cursors (panels/theming).
                            Component {
                                id: appearanceView
                                ThemingView {
                                    title: page.modelData.label
                                    active: root.open && root.section === "appearance" && (!root.compact || !root.showingSidebar)
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
