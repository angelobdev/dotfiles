import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."
import "../../components"
import "../../services"

// Settings → System → Profiles: the profiles of the installer (profiles.py list), each with what of it is on this
// system. Install and Remove show the plan of the installer first (profiles.py plan, then its dry-run); Apply runs it in the
// background with jobs.py, behind one pkexec prompt, with its progress and log here. The list is read again after it.
ColumnLayout {
    id: root
    // On screen: the list is read again each time it shows.
    property bool shown: false
    property var listed: []
    property string error: ""
    // The plan on screen: { action, name, apply, blocked, preview (its dry-run, once read) }, or null.
    property var review: null
    // The profile the last Apply was for, and its action, for the result line.
    property var applied: null
    readonly property bool busy: job.running || planner.running || previewer.running
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/profiles.py"
    spacing: 10
    onShownChanged: if (shown)
        refresh()
    Component.onCompleted: if (shown)
        refresh()
    function refresh() {
        if (!reader.running && !job.running)
            reader.running = true;
    }
    function plan(action, name) {
        if (busy)
            return;
        review = null;
        error = "";
        planner.command = ["python3", helper, "plan", action, name];
        planner.action = action;
        planner.name = name;
        planner.running = true;
    }
    function apply() {
        if (!review || review.blocked || job.running)
            return;
        applied = {
            action: review.action,
            name: review.name
        };
        job.start(review.apply, true, title(review.action, review.name));
        review = null;
    }
    function title(action, name) {
        return I18n.tr(action === "install" ? "settings.profiles.installTitle" : "settings.profiles.removeTitle", [name]);
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
    // The plan: profiles.py says which installer commands, then the dry-run shows what they do.
    Process {
        id: planner
        property string action
        property string name
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const value = JSON.parse(text);
                    root.review = {
                        action: planner.action,
                        name: planner.name,
                        apply: value.apply,
                        blocked: value.blocked ?? "",
                        preview: ""
                    };
                    previewer.command = value.preview;
                    previewer.running = true;
                } catch (failure) {}
            }
        }
        stderr: StdioCollector {
            onStreamFinished: if (text.trim() !== "")
                root.error = text.trim()
        }
    }
    Process {
        id: previewer
        stdout: StdioCollector {
            id: previewText
        }
        stderr: StdioCollector {
            id: previewErrors
        }
        onExited: if (root.review)
            root.review = Object.assign({}, root.review, {
                preview: (previewText.text + previewErrors.text).trim()
            })
    }
    Job {
        id: job
        name: "profile"
        onFinished: root.refresh()
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
                            enabled: !root.busy
                            text: I18n.tr(profileRow.modelData.done > 0 ? "settings.profiles.complete" : "settings.profiles.install")
                            onClicked: root.plan("install", profileRow.modelData.name)
                        }
                        ActionButton {
                            visible: !profileRow.core && profileRow.modelData.recorded
                            enabled: !root.busy
                            destructive: true
                            text: I18n.tr("settings.profiles.remove")
                            onClicked: root.plan("remove", profileRow.modelData.name)
                        }
                    }
                }
            }
        }
    }
    // The plan before Apply: the installer's dry-run, as its preview prints it.
    Rectangle {
        Layout.fillWidth: true
        visible: root.review !== null || planner.running
        implicitHeight: reviewRows.implicitHeight + 24
        radius: Theme.corner(12)
        color: Theme.tile
        ColumnLayout {
            id: reviewRows
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 12
            }
            spacing: 8
            Text {
                Layout.fillWidth: true
                text: root.review ? I18n.tr(root.review.action === "install" ? "settings.profiles.reviewInstall" : "settings.profiles.reviewRemove", [root.review.name]) : I18n.tr("settings.profiles.reading")
                wrapMode: Text.WordWrap
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(13)
                font.weight: Font.DemiBold
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.min(previewLines.implicitHeight, 220)
                visible: (root.review?.preview ?? "") !== ""
                clip: true
                contentWidth: availableWidth
                Text {
                    id: previewLines
                    width: parent.width
                    text: root.review?.preview ?? ""
                    textFormat: Text.PlainText
                    wrapMode: Text.WrapAnywhere
                    color: Theme.text
                    font.family: "monospace"
                    font.pixelSize: Theme.textSize(11)
                }
            }
            Text {
                Layout.fillWidth: true
                visible: previewer.running
                text: I18n.tr("settings.profiles.reading")
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
            Text {
                Layout.fillWidth: true
                visible: (root.review?.blocked ?? "") !== ""
                text: root.review?.blocked ?? ""
                textFormat: Text.PlainText
                wrapMode: Text.WordWrap
                color: Theme.danger
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
            }
            RowLayout {
                spacing: 8
                ActionButton {
                    highlighted: true
                    destructive: root.review?.action === "remove"
                    text: I18n.tr("settings.profiles.apply")
                    enabled: root.review !== null && !previewer.running && root.review.blocked === "" && !job.running
                    onClicked: root.apply()
                }
                ActionButton {
                    text: I18n.tr("common.cancel")
                    enabled: !planner.running
                    onClicked: root.review = null
                }
            }
        }
    }
    // The last Apply: its progress, its result and, while it runs or when it failed, the end of its log.
    Text {
        Layout.fillWidth: true
        visible: root.applied !== null || job.running
        text: {
            const name = root.applied ? root.title(root.applied.action, root.applied.name) : I18n.tr("settings.profiles.busy");
            if (job.running)
                return I18n.tr("settings.profiles.running", [name]);
            if (job.record.status === 0)
                return I18n.tr("settings.profiles.done", [name]);
            return I18n.tr("settings.profiles.failed", [name, job.record.status ?? -1]);
        }
        wrapMode: Text.WordWrap
        color: job.running || job.record.status === 0 ? Theme.text : Theme.danger
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
    Rectangle {
        Layout.fillWidth: true
        visible: job.log.length > 0 && (job.running || job.failed)
        implicitHeight: jobLog.implicitHeight + 16
        radius: Theme.corner(10)
        color: Theme.tile
        Text {
            id: jobLog
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 8
            }
            text: job.log.slice(-10).join("\n")
            textFormat: Text.PlainText
            wrapMode: Text.WrapAnywhere
            color: Theme.text
            font.family: "monospace"
            font.pixelSize: Theme.textSize(10)
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        ActionButton {
            text: reader.running ? I18n.tr("settings.profiles.checking") : I18n.tr("settings.profiles.checkAgain")
            enabled: !reader.running && !job.running
            onClicked: root.refresh()
        }
        ActionButton {
            text: I18n.tr("settings.profiles.openManager")
            enabled: !root.busy
            onClicked: Quickshell.execDetached(["kitty", "--class", "desktop-updates", "--title", I18n.tr("settings.profiles.managerTitle"), Quickshell.env("HOME") + "/.local/bin/desktop-manager"])
        }
    }
}
