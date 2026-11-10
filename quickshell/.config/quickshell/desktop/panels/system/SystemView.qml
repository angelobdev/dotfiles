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
        property string label
        property string value
        Layout.fillWidth: true
        visible: value !== ""
        spacing: 14
        Text {
            Layout.preferredWidth: 180
            text: parent.label
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(13)
        }
        Text {
            Layout.fillWidth: true
            text: parent.value
            textFormat: Text.PlainText
            wrapMode: Text.WrapAnywhere
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.textSize(13)
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Heading {
            Layout.fillWidth: true
            text: root.title
        }
        ChoiceChips {
            Layout.fillWidth: false
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
                Fact {
                    label: I18n.tr("settings.system.distribution")
                    value: root.about.distribution ?? ""
                }
                Fact {
                    label: I18n.tr("settings.system.model")
                    value: root.about.model ?? ""
                }
                Fact {
                    label: I18n.tr("settings.system.processor")
                    value: (root.about.processor?.name ?? "") === "" ? "" : root.about.processor.threads > 1 ? I18n.tr("settings.system.threads", [root.about.processor.name, root.about.processor.threads]) : root.about.processor.name
                }
                Fact {
                    label: I18n.tr("settings.system.memory")
                    value: root.about.memory ?? ""
                }
                Fact {
                    label: I18n.tr("settings.system.kernel")
                    value: root.about.kernel ?? ""
                }
                Fact {
                    label: "Hyprland"
                    value: root.about.hyprland ?? ""
                }
                Fact {
                    label: "Quickshell"
                    value: root.about.quickshell ?? ""
                }
                Fact {
                    label: I18n.tr("settings.system.desktop")
                    value: (root.about.repository?.commit ?? "") === "" ? "" : I18n.tr(root.about.repository.changed ? "settings.system.commitChanged" : "settings.system.commit", [root.about.repository.commit, root.about.repository.date])
                }
                Fact {
                    label: I18n.tr("settings.system.repository")
                    value: root.about.repository?.path ?? ""
                }
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
                            text: I18n.tr("settings.system.openFolder")
                            onClicked: root.openPath(root.directory)
                        }
                        ActionButton {
                            visible: root.ownFiles.includes("hypr.lua")
                            text: I18n.tr("settings.system.openFile", ["hypr.lua"])
                            onClicked: root.openPath(root.directory + "/hypr.lua")
                        }
                        ActionButton {
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
