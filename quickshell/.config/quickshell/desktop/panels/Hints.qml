import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Io
import Quickshell.Hyprland
import ".."
import "../components"

Overlay {
    id: root
    panelName: "hints"
    property var bindings: []
    property string error: ""
    readonly property var categories: [I18n.tr("launcher.title"), I18n.tr("hints.categories.shell"), I18n.tr("hints.categories.screenCapture"), I18n.tr("hints.categories.windows"), I18n.tr("hints.categories.workspaces"), I18n.tr("hints.categories.mouse"), I18n.tr("hints.categories.audioBrightness"), I18n.tr("session.title"), I18n.tr("hints.categories.other")]
    function category(bind) {
        const name = (bind.description || "").toLowerCase();
        if ((bind.key || "").startsWith("XF86Audio") || (bind.key || "").startsWith("XF86MonBrightness"))
            return I18n.tr("hints.categories.audioBrightness");
        if ((bind.key || "").startsWith("mouse:"))
            return I18n.tr("hints.categories.mouse");
        if (/screenshot|recording/.test(name))
            return I18n.tr("hints.categories.screenCapture");
        if (/workspace|scratchpad/.test(name))
            return I18n.tr("hints.categories.workspaces");
        if (/lock|suspend|logout|reboot|shut down|session/.test(name))
            return I18n.tr("session.title");
        if (/applications|control center|notifications|quickshell|network|wi-fi|sound.*devices|battery|calendar|hints|wallpaper|clipboard/.test(name))
            return I18n.tr("hints.categories.shell");
        if (/browser|terminal|kitty|1password|calculator/.test(name))
            return I18n.tr("launcher.title");
        if (/window|focus|floating|fullscreen|^move |tiling|split|pseudo/.test(name))
            return I18n.tr("hints.categories.windows");
        return I18n.tr("hints.categories.other");
    }
    function shortcut(bind) {
        const parts = [];
        for (const [mask, label] of [[64, "Super"], [4, "Ctrl"], [1, "Shift"], [8, "Alt"], [128, "Mod5"]])
            if ((bind.modmask & mask) !== 0)
                parts.push(label);
        const names = {
            Return: I18n.tr("keys.enter"),
            Print: I18n.tr("keys.print"),
            Space: I18n.tr("keys.space"),
            space: I18n.tr("keys.space"),
            left: "←",
            right: "→",
            up: "↑",
            down: "↓",
            "mouse:272": I18n.tr("keys.leftMouse"),
            "mouse:273": I18n.tr("keys.rightMouse")
        };
        parts.push(names[bind.key] || bind.key || ("code:" + bind.keycode));
        return parts.join(" + ");
    }
    function refreshBindings() {
        if (!reader.running)
            reader.running = true;
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "configreloaded" && root.visible)
                root.refreshBindings();
        }
    }
    Connections {
        target: I18n
        function onLanguageChanged() { if (root.visible) root.refreshBindings(); }
        function onItalianChanged() { if (root.visible) root.refreshBindings(); }
        function onEnglishChanged() { if (root.visible) root.refreshBindings(); }
    }
    onOpened: {
        search.clear();
        error = "";
        search.forceActiveFocus();
        refreshBindings();
    }
    Process {
        id: reader
        command: ["hyprctl", "-j", "binds"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.bindings = JSON.parse(text).map(b => ({
                                keys: root.shortcut(b),
                                name: I18n.bindDescription(b.description || b.dispatcher),
                                submap: b.submap || "",
                                release: b.release,
                                category: root.category(b)
                            })).sort((a, b) => root.categories.indexOf(a.category) - root.categories.indexOf(b.category));
                } catch (e) {
                    root.error = I18n.tr("hints.errors.readFailed");
                }
            }
        }
        onExited: (code, status) => {
            if (code !== 0)
                root.error = I18n.tr("hints.errors.noBindings");
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(820, parent.width - 48)
        height: Math.min(650, parent.height - 96)
        ColumnLayout {
            anchors {
                fill: parent
                margins: 22
            }
            spacing: 14
            Heading {
                text: I18n.tr("hints.title")
            }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: I18n.tr("hints.searchPlaceholder")
            }
            RowLayout {
                Text {
                    text: I18n.tr("hints.shortcutColumn")
                    Layout.preferredWidth: 280
                    color: Theme.muted
                    font.pixelSize: 12
                }
                Text {
                    text: I18n.tr("hints.actionColumn")
                    color: Theme.muted
                    font.pixelSize: 12
                }
            }
            ListView {
                id: list
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 3
                model: root.bindings.filter(b => (b.keys + " " + b.name + " " + b.submap + " " + b.category).toLowerCase().includes(search.text.toLowerCase()))
                section.property: "category"
                section.criteria: ViewSection.FullString
                section.delegate: Item {
                    required property string section
                    width: list.width
                    height: 38
                    Text {
                        anchors {
                            left: parent.left
                            bottom: parent.bottom
                            bottomMargin: 8
                        }
                        text: section
                        color: Theme.muted
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        font.letterSpacing: 0.6
                    }
                }
                delegate: Rectangle {
                    required property var modelData
                    required property int index
                    width: list.width
                    height: Math.max(40, description.implicitHeight + 16)
                    radius: 9
                    color: index % 2 === 0 ? Theme.raised : "transparent"
                    RowLayout {
                        anchors {
                            fill: parent
                            leftMargin: 10
                            rightMargin: 10
                        }
                        spacing: 14
                        Text {
                            text: modelData.keys
                            Layout.preferredWidth: 256
                            color: Theme.accent
                            font.family: Theme.font
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                        Text {
                            id: description
                            text: modelData.name + (modelData.submap ? " [" + modelData.submap + "]" : "") + (modelData.release ? I18n.tr("hints.releaseSuffix") : "")
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            color: Theme.text
                            font.pixelSize: 13
                            textFormat: Text.PlainText
                        }
                    }
                }
                ScrollBar.vertical: ScrollBar {}
            }
            Text {
                visible: root.error !== ""
                text: root.error
                color: Theme.danger
            }
            Text {
                visible: !reader.running && list.count === 0 && !root.error
                text: I18n.tr("hints.empty")
                color: Theme.muted
            }
            RowLayout {
                Text {
                    text: I18n.plural("hints.shortcutCount.one", "hints.shortcutCount.other", root.bindings.length)
                    color: Theme.muted
                    font.pixelSize: 12
                }
                Item {
                    Layout.fillWidth: true
                }
                ActionButton {
                    text: I18n.tr("common.close")
                    onClicked: ShellState.close()
                }
            }
        }
    }
}
