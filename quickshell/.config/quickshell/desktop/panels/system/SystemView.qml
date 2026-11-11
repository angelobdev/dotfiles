import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."
import "../../components"
import "../../services"
import "../updates"
import "../../SettingsSchema.js" as Schema

// Settings → System: About (the computer and the desktop, from about.py), Updates (the view of the updates
// panel), Profiles (those of the installer, to install or remove: ProfilesView), Plugins (the Hyprland plugins, their rebuild
// and build cache: PluginsView) and Advanced (the folder and files of your own settings, Hyprland's config errors, and the shell
// options back to their defaults).
ColumnLayout {
    id: root
    property string title: ""
    // On screen: About and the config errors are read again each time it shows.
    property bool shown: false
    readonly property Item focusItem: root
    property string tab: ShellState.recall("settings/system", "about")
    onTabChanged: ShellState.remember("settings/system", tab)
    readonly property var tabs: ["about", "updates", "profiles", "plugins", "advanced"]
    property var about: ({})
    // The rows of About, as shown and as Copy puts them on the clipboard; folder: the row opens its value.
    readonly property var facts: {
        const about = root.about;
        const processor = about.processor?.name ?? "";
        const commit = about.repository?.commit ?? "";
        return [
            {
                label: I18n.tr("settings.system.distribution"),
                value: about.distribution ?? ""
            },
            {
                label: I18n.tr("settings.system.model"),
                value: about.model ?? ""
            },
            {
                label: I18n.tr("settings.system.processor"),
                value: processor === "" ? "" : about.processor.threads > 1 ? I18n.tr("settings.system.threads", [processor, about.processor.threads]) : processor
            },
            {
                label: I18n.tr("settings.system.memory"),
                value: about.memory ?? ""
            },
            {
                label: I18n.tr("settings.system.kernel"),
                value: about.kernel ?? ""
            },
            {
                label: "Hyprland",
                value: about.hyprland ?? ""
            },
            {
                label: "Quickshell",
                value: about.quickshell ?? ""
            },
            {
                label: I18n.tr("settings.system.desktop"),
                value: commit === "" ? "" : I18n.tr(about.repository.changed ? "settings.system.commitChanged" : "settings.system.commit", [commit, about.repository.date])
            },
            {
                label: I18n.tr("settings.system.repository"),
                value: about.repository?.path ?? "",
                folder: true
            }
        ].filter(fact => fact.value !== "");
    }
    // Copy was pressed a moment ago: its label says so.
    property bool copied: false
    property string configErrors: ""
    property var ownFiles: []
    property bool confirmReset: false
    readonly property string directory: Config.directory
    spacing: 14
    function open(name) {
        if (tabs.includes(name))
            tab = name;
        refresh();
    }
    function refresh() {
        if (!reader.running)
            reader.running = true;
        if (!errors.running)
            errors.running = true;
        if (!files.running)
            files.running = true;
        confirmReset = false;
    }
    onShownChanged: if (shown)
        refresh()
    Component.onCompleted: if (shown)
        refresh()
    function openPath(path) {
        Quickshell.execDetached(["sh", "-c", "mkdir -p \"$1\" && exec xdg-open \"$2\"", "sh", directory, path]);
    }
    // The About table as plain text, one "label: value" line per row, for a bug report.
    function copyAbout() {
        Quickshell.execDetached(["wl-copy", "--", root.facts.map(fact => fact.label + ": " + fact.value).join("\n")]);
        root.copied = true;
        copiedTimer.restart();
    }
    Timer {
        id: copiedTimer
        interval: 2000
        onTriggered: root.copied = false
    }
    Process {
        id: reader
        command: ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/about.py"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.about = JSON.parse(text);
                } catch (failure) {
                    root.about = {};
                }
            }
        }
    }
    Process {
        id: errors
        command: ["hyprctl", "configerrors"]
        stdout: StdioCollector {
            // Hyprland prints one empty line when there is nothing wrong.
            onStreamFinished: root.configErrors = text.trim()
        }
    }
    Process {
        id: files
        command: ["sh", "-c", "for f in hypr.lua shell.json; do [ -f \"$1/$f\" ] && echo \"$f\"; done; exit 0", "sh", root.directory]
        stdout: StdioCollector {
            onStreamFinished: root.ownFiles = text.split("\n").filter(name => name !== "")
        }
    }
    component Fact: RowLayout {
        id: fact
        property string label
        property string value
        // The value is a folder: a button that opens it, its text in line with the other values.
        property bool folder: false
        signal openFolder
        Layout.fillWidth: true
        visible: value !== ""
        spacing: folder ? 14 - folderButton.leftPadding : 14
        Text {
            Layout.preferredWidth: 180
            text: fact.label
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(13)
        }
        Text {
            Layout.fillWidth: true
            visible: !fact.folder
            text: fact.value
            textFormat: Text.PlainText
            wrapMode: Text.WrapAnywhere
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.textSize(13)
        }
        ActionButton {
            id: folderButton
            visible: fact.folder
            implicitHeight: Theme.hit(28)
            text: fact.value
            normalColor: Theme.accent
            tooltip: I18n.tr("settings.system.openFolder")
            onClicked: fact.openFolder()
        }
        Item {
            visible: fact.folder
            Layout.fillWidth: true
        }
    }
    Heading {
        Layout.fillWidth: true
        text: root.title
    }
    // The tabs, left-aligned under the title (as in Appearance), wrapping on a narrow panel.
    ChoiceChips {
        options: [
            {
                name: "about",
                label: I18n.tr("settings.system.about")
            },
            {
                name: "updates",
                label: I18n.tr("settings.system.updates")
            },
            {
                name: "profiles",
                label: I18n.tr("settings.system.profiles")
            },
            {
                name: "plugins",
                label: I18n.tr("settings.system.plugins")
            },
            {
                name: "advanced",
                label: I18n.tr("settings.system.advanced")
            }
        ]
        current: root.tab
        onChosen: name => root.open(name)
    }
    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: root.tabs.indexOf(root.tab)
        // About
        ColumnLayout {
            spacing: 10
            GroupCard {
                Layout.fillWidth: true
                rightPadding: 12
                spacing: 10
                Repeater {
                    model: root.facts
                    Fact {
                        required property var modelData
                        label: modelData.label
                        value: modelData.value
                        folder: modelData.folder === true
                        onOpenFolder: root.openPath(modelData.value)
                    }
                }
            }
            ActionButton {
                outlined: true
                visible: root.facts.length > 0
                text: root.copied ? I18n.tr("settings.system.copied") : I18n.tr("settings.system.copy")
                onClicked: root.copyAbout()
            }
            Item {
                Layout.fillHeight: true
            }
        }
        // Updates
        UpdatesView {
            shown: root.shown && root.tab === "updates"
        }
        // Profiles
        ProfilesView {
            shown: root.shown && root.tab === "profiles"
        }
        PluginsView {
            shown: root.shown && root.tab === "plugins"
        }
        // Advanced
        ScrollView {
            contentWidth: availableWidth
            clip: true
            ColumnLayout {
                width: parent.width
                spacing: 18
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: I18n.tr("settings.system.ownSettings")
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                        font.weight: Font.DemiBold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("settings.system.ownSettingsHint", [root.directory])
                        wrapMode: Text.WordWrap
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                    }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 8
                        ActionButton {
                            outlined: true
                            text: I18n.tr("settings.system.openFolder")
                            onClicked: root.openPath(root.directory)
                        }
                        ActionButton {
                            outlined: true
                            visible: root.ownFiles.includes("hypr.lua")
                            text: I18n.tr("settings.system.openFile", ["hypr.lua"])
                            onClicked: root.openPath(root.directory + "/hypr.lua")
                        }
                        ActionButton {
                            outlined: true
                            visible: root.ownFiles.includes("shell.json")
                            text: I18n.tr("settings.system.openFile", ["shell.json"])
                            onClicked: root.openPath(root.directory + "/shell.json")
                        }
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: I18n.tr("settings.system.configErrors")
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                        font.weight: Font.DemiBold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.configErrors === "" ? I18n.tr("settings.system.noConfigErrors") : root.configErrors
                        textFormat: Text.PlainText
                        wrapMode: Text.WrapAnywhere
                        color: root.configErrors === "" ? Theme.text : Theme.danger
                        font.family: root.configErrors === "" ? Theme.font : "monospace"
                        font.pixelSize: Theme.textSize(12)
                    }
                    ActionButton {
                        outlined: true
                        text: I18n.tr("settings.system.checkAgain")
                        enabled: !errors.running
                        onClicked: errors.running = true
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    Text {
                        text: I18n.tr("settings.system.resetTitle")
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                        font.weight: Font.DemiBold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("settings.system.resetHint")
                        wrapMode: Text.WordWrap
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                    }
                    // Two steps: the first press asks, the second resets.
                    RowLayout {
                        spacing: 8
                        ActionButton {
                            outlined: true
                            destructive: root.confirmReset
                            enabled: !Config.unreadable && Schema.options.some(option => Config.isSet(option.key))
                            text: root.confirmReset ? I18n.tr("settings.system.resetConfirm") : I18n.tr("settings.system.reset")
                            onClicked: {
                                if (!root.confirmReset) {
                                    root.confirmReset = true;
                                    return;
                                }
                                Config.resetMany(Schema.options.map(option => option.key));
                                root.confirmReset = false;
                            }
                        }
                        ActionButton {
                            outlined: true
                            visible: root.confirmReset
                            text: I18n.tr("common.cancel")
                            onClicked: root.confirmReset = false
                        }
                    }
                }
            }
        }
    }
}
