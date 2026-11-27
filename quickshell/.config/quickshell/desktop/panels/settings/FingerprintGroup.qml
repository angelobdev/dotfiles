pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."
import "../../components"

// Settings → Privacy: the fingerprints of the user (fingerprint.py, through fprintd). The enrolled fingers with
// Remove, and Add, which asks for the password of the user (polkit) and then follows each touch of the reader.
ColumnLayout {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/fingerprint.py"
    readonly property var all: ["right-index-finger", "left-index-finger", "right-thumb", "left-thumb", "right-middle-finger", "left-middle-finger", "right-ring-finger", "left-ring-finger", "right-little-finger", "left-little-finger"]
    // fingerprint.py list: {device, fingers, stages}.
    property var info: ({})
    readonly property bool reader: (info.device ?? "") !== ""
    readonly property var enrolled: Array.isArray(info.fingers) ? info.fingers : []
    readonly property var free: all.filter(finger => !enrolled.includes(finger))
    property string chosen: ""
    // While enrolling: the last report of fprintd ({result, done, stage, stages}), and what went wrong.
    property var progress: null
    property string error: ""
    property string removing: ""
    readonly property bool enrolling: enroller.running
    // The right-index-finger of fprintd as rightIndexFinger in the catalogs.
    function fingerKey(finger) {
        return "fingerprint.fingers." + finger.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    }
    // The results of fprintd, as the dialog says them.
    function resultKey(result) {
        return ({
                "enroll-started": "fingerprint.results.touch",
                "enroll-stage-passed": "fingerprint.results.again",
                "enroll-retry-scan": "fingerprint.results.retry",
                "enroll-swipe-too-short": "fingerprint.results.retry",
                "enroll-finger-not-centered": "fingerprint.results.centre",
                "enroll-remove-and-retry": "fingerprint.results.lift",
                "enroll-completed": "fingerprint.results.completed",
                "enroll-duplicate": "fingerprint.results.duplicate",
                "enroll-data-full": "fingerprint.results.full",
                "enroll-disconnected": "fingerprint.results.disconnected"
            })[result] ?? "fingerprint.results.failed";
    }
    function load() {
        if (!lister.running)
            lister.running = true;
    }
    function enroll() {
        if (enroller.running || chosen === "")
            return;
        error = "";
        progress = null;
        enroller.command = ["python3", helper, "enroll", chosen];
        enroller.running = true;
    }
    function remove(finger) {
        if (remover.running)
            return;
        // A second press confirms.
        if (removing !== finger) {
            removing = finger;
            return;
        }
        removing = "";
        error = "";
        remover.command = ["python3", helper, "delete", finger];
        remover.running = true;
    }
    Layout.fillWidth: true
    spacing: 6
    Component.onCompleted: load()
    onFreeChanged: if (!free.includes(chosen))
        chosen = free[0] ?? ""
    Process {
        id: lister
        command: ["python3", root.helper, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.info = JSON.parse(text);
                } catch (failure) {
                    root.info = {};
                }
            }
        }
    }
    Process {
        id: enroller
        stdinEnabled: true
        stdout: SplitParser {
            onRead: line => {
                try {
                    const value = JSON.parse(line);
                    root.progress = value;
                    if (value.error)
                        root.error = value.error;
                } catch (failure) {}
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "")
                    root.error = text.trim();
            }
        }
        onExited: root.load()
    }
    Process {
        id: remover
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.info = JSON.parse(text);
                } catch (failure) {}
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "")
                    root.error = text.trim();
            }
        }
    }
    Text {
        text: I18n.tr("fingerprint.title")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        font.weight: Font.DemiBold
    }
    GroupCard {
        Layout.fillWidth: true
        spacing: 10
        Text {
            Layout.fillWidth: true
            visible: !root.reader
            text: lister.running ? I18n.tr("common.loading") : I18n.tr("fingerprint.noReader")
            color: Theme.muted
            wrapMode: Text.WordWrap
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        Text {
            Layout.fillWidth: true
            visible: root.reader && root.enrolled.length === 0 && !root.enrolling
            text: I18n.tr("fingerprint.none", [root.info.device ?? ""])
            color: Theme.muted
            wrapMode: Text.WordWrap
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        Repeater {
            model: root.reader ? root.enrolled : []
            RowLayout {
                id: row
                required property string modelData
                Layout.fillWidth: true
                spacing: 10
                Icon {
                    name: "lock"
                    color: Theme.text
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                }
                Text {
                    Layout.fillWidth: true
                    text: I18n.tr(root.fingerKey(row.modelData))
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(13)
                }
                ActionButton {
                    outlined: true
                    destructive: root.removing === row.modelData
                    enabled: !root.enrolling && !remover.running
                    text: root.removing === row.modelData ? I18n.tr("fingerprint.confirmRemove") : I18n.tr("fingerprint.remove")
                    onClicked: root.remove(row.modelData)
                }
            }
        }
        // Add: the finger, then each touch until fprintd has the whole print.
        RowLayout {
            Layout.fillWidth: true
            visible: root.reader && !root.enrolling && root.free.length > 0
            spacing: 10
            ChoiceCombo {
                Layout.fillWidth: true
                options: root.free.map(finger => ({
                            name: finger,
                            label: I18n.tr(root.fingerKey(finger))
                        }))
                current: root.chosen
                onChosen: name => root.chosen = name
            }
            ActionButton {
                highlighted: true
                text: I18n.tr("fingerprint.add")
                onClicked: root.enroll()
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            visible: root.enrolling || (root.progress !== null && root.progress.done)
            spacing: 8
            Text {
                Layout.fillWidth: true
                text: root.progress ? I18n.tr(root.resultKey(root.progress.result)) : I18n.tr("fingerprint.results.waiting")
                color: root.progress && root.progress.done && root.progress.result !== "enroll-completed" ? Theme.danger : Theme.text
                wrapMode: Text.WordWrap
                font.family: Theme.font
                font.pixelSize: Theme.textSize(14)
                font.weight: Font.DemiBold
            }
            // The touches fprintd needs, filled as they pass.
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 6
                radius: 3
                color: Theme.track
                Rectangle {
                    width: parent.width * (root.progress && root.progress.stages > 0 ? Math.min(1, root.progress.stage / root.progress.stages) : 0)
                    height: parent.height
                    radius: 3
                    color: Theme.accent
                    Behavior on width {
                        NumberAnimation {
                            duration: Theme.motionFast
                        }
                    }
                }
            }
            ActionButton {
                visible: root.enrolling
                Layout.alignment: Qt.AlignRight
                outlined: true
                text: I18n.tr("common.cancel")
                onClicked: enroller.write("cancel\n")
            }
        }
        Text {
            Layout.fillWidth: true
            visible: root.error !== ""
            text: root.error
            color: Theme.danger
            wrapMode: Text.WordWrap
            textFormat: Text.PlainText
            font.family: Theme.font
            font.pixelSize: Theme.textSize(11)
        }
    }
}
