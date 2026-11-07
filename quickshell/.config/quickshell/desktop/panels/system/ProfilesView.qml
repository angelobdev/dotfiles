import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."
import "../../components"

// Settings → System → Profiles: the installer's profiles (profiles.py list), each with what of it is on this
// system. Install and Remove open the guided installer in a terminal (profiles.py install/remove), which shows the
// plan and asks for the password; the list is read again once that window closes.
ColumnLayout {
    id: root
    // On screen: the list is read again each time it shows.
    property bool shown: false
    property var listed: []
    property string error: ""
    property string busy: ""
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/profiles.py"
    spacing: 10
    onShownChanged: if (shown)
        refresh()
    Component.onCompleted: if (shown)
        refresh()
    function refresh() {
        if (!reader.running && !runner.running)
            reader.running = true;
    }
    function run(action, name) {
        if (runner.running)
            return;
        busy = name;
        runner.command = ["python3", helper, action, name];
        runner.running = true;
    }
    // A catalog key holds no dash: steam-hidpi is steamHidpi.
    function described(name) {
        const key = "settings.profiles.descriptions." + name.replace(/-(\w)/g, (match, letter) => letter.toUpperCase());
        return I18n.tr(key);
    }
    function stateText(profile) {
        if (profile.installed && !profile.recorded && profile.name !== "core")
            return I18n.tr("settings.profiles.outside");
        if (profile.installed)
            return I18n.tr("settings.profiles.installed");
        if (profile.done > 0)
            return I18n.tr("settings.profiles.partial", [profile.done, profile.total]);
        return I18n.tr("settings.profiles.notInstalled");
    }
    Process {
        id: reader
        command: ["python3", root.helper, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const value = JSON.parse(text);
                    root.listed = Array.isArray(value.profiles) ? value.profiles : [];
                    root.error = value.error ?? "";
                } catch (failure) {
                    root.listed = [];
                    root.error = text.trim();
                }
            }
        }
    }
    Process {
        id: runner
        onRunningChanged: if (!running) {
            root.busy = "";
            root.refresh();
        }
    }
    Text {
        Layout.fillWidth: true
        text: I18n.tr("settings.profiles.intro")
        wrapMode: Text.WordWrap
        color: Theme.text
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
    Text {
        Layout.fillWidth: true
        visible: root.error !== ""
        text: I18n.tr("settings.profiles.error", [root.error])
        textFormat: Text.PlainText
        wrapMode: Text.WordWrap
        color: Theme.danger
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
    ScrollView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        contentWidth: availableWidth
        clip: true
        Rectangle {
            width: parent.width
            implicitHeight: rows.implicitHeight + 24
            visible: root.listed.length > 0
            radius: Theme.corner(12)
            color: Theme.tile
            ColumnLayout {
                id: rows
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 12
                    leftMargin: 14
                    rightMargin: 14
                }
                spacing: 12
                Repeater {
                    model: root.listed
                    RowLayout {
                        id: profileRow
                        required property var modelData
                        readonly property bool core: modelData.name === "core"
                        Layout.fillWidth: true
                        spacing: 12
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                Layout.fillWidth: true
                                text: profileRow.modelData.name + (profileRow.modelData.default ? " · " + I18n.tr("settings.profiles.default") : "")
                                textFormat: Text.PlainText
                                color: Theme.text
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(13)
                                font.weight: Font.DemiBold
                            }
                            Text {
                                Layout.fillWidth: true
                                text: root.described(profileRow.modelData.name)
                                wrapMode: Text.WordWrap
                                color: Theme.muted
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(11)
                            }
                            Text {
                                Layout.fillWidth: true
                                text: profileRow.core ? root.stateText(profileRow.modelData) + " · " + I18n.tr("settings.profiles.coreHint") : root.stateText(profileRow.modelData)
                                wrapMode: Text.WordWrap
                                color: profileRow.modelData.installed ? Theme.text : Theme.muted
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(11)
                            }
                        }
                        // Install while something of it is missing (Complete when part is there), Remove while the installer has a record of it.
                        ActionButton {
                            visible: !profileRow.modelData.installed
                            enabled: !runner.running
                            text: root.busy === profileRow.modelData.name ? I18n.tr("settings.profiles.busy") : I18n.tr(profileRow.modelData.done > 0 ? "settings.profiles.complete" : "settings.profiles.install")
                            onClicked: root.run("install", profileRow.modelData.name)
                        }
                        ActionButton {
                            visible: !profileRow.core && profileRow.modelData.recorded
                            enabled: !runner.running
                            destructive: true
                            text: root.busy === profileRow.modelData.name ? I18n.tr("settings.profiles.busy") : I18n.tr("settings.profiles.remove")
                            onClicked: root.run("remove", profileRow.modelData.name)
                        }
                    }
                }
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        ActionButton {
            text: reader.running ? I18n.tr("settings.profiles.checking") : I18n.tr("settings.profiles.checkAgain")
            enabled: !reader.running && !runner.running
            onClicked: root.refresh()
        }
        ActionButton {
            text: I18n.tr("settings.profiles.openManager")
            enabled: !runner.running
            onClicked: Quickshell.execDetached(["kitty", "--class", "desktop-updates", "--title", I18n.tr("settings.profiles.managerTitle"), Quickshell.env("HOME") + "/.local/bin/desktop-manager"])
        }
    }
}
