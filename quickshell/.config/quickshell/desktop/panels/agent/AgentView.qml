import QtQuick
import QtQuick.Layouts
import Quickshell
import "../.."
import "../../components"
import "../../services"

// The AI coding assistant: what the active agent is doing, rate-limit meters when reported,
// model and context use, and the drop-down console. The assistant panel and Settings → Assistant show it.
ColumnLayout {
    id: root
    // On screen: the clock that dates the usage runs only then.
    property bool shown: false
    readonly property Item focusItem: root
    spacing: 14
    property date now: new Date()
    onShownChanged: if (shown)
        now = new Date()
    function stateText() {
        if (!Agent.available)
            return Agent.hasNamedAgent ? I18n.tr("assistant.states.missing", [Agent.name]) : I18n.tr("assistant.states.anyMissing");
        if (!Agent.running)
            return I18n.tr("assistant.states.off", [Agent.name]);
        switch (Agent.state) {
        case "working":
            return I18n.tr("assistant.states.working");
        case "permission":
            return I18n.tr("assistant.states.permission");
        case "finished":
            return I18n.tr("assistant.states.finished");
        case "error":
            return I18n.tr("assistant.states.error");
        default:
            return I18n.tr("assistant.states.ready");
        }
    }
    function clock(date) {
        return I18n.locale.toString(date, I18n.timeFormat);
    }
    // Today "at 22:37", another day "Sun 20:50": todayKey or otherKey with the time in it.
    function when(seconds, todayKey, otherKey) {
        const date = new Date(seconds * 1000);
        if (date.toDateString() === now.toDateString())
            return I18n.tr(todayKey, [clock(date)]);
        return I18n.tr(otherKey, [I18n.locale.toString(date, I18n.tr("assistant.dayFormat") + " " + I18n.timeFormat)]);
    }
    Timer {
        interval: 30000
        repeat: true
        running: root.shown
        onTriggered: root.now = new Date()
    }
    component Meter: ColumnLayout {
        id: meter
        property string label
        property var window: null
        property date now
        // "Resets at …" for this window, from the panel (it formats dates).
        property string resets
        readonly property bool known: window !== null && window !== undefined && (window.resets === null || window.resets * 1000 > now.getTime())
        readonly property real used: known ? Math.max(0, Math.min(100, window.used)) : 0
        Layout.fillWidth: true
        spacing: 6
        RowLayout {
            Layout.fillWidth: true
            Text {
                Layout.fillWidth: true
                text: meter.label
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(13)
            }
            Text {
                text: meter.known ? Math.round(meter.used) + "%" : "–"
                color: meter.used >= 90 ? Theme.danger : Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(13)
                font.bold: true
            }
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 6
            radius: 3
            color: Theme.track
            Rectangle {
                width: parent.width * meter.used / 100
                height: parent.height
                radius: 3
                color: meter.used >= 90 ? Theme.danger : Theme.accent
            }
        }
        Text {
            Layout.fillWidth: true
            text: meter.known ? meter.resets : I18n.tr("assistant.usage.unknown")
            visible: text !== ""
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(11)
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        Rectangle {
            Layout.alignment: Qt.AlignTop
            Layout.topMargin: 5
            implicitWidth: 8
            implicitHeight: 8
            radius: 4
            color: Agent.state === "permission" || Agent.state === "error" ? Theme.danger : Agent.state === "working" ? Theme.accent : Agent.running ? Theme.text : Theme.muted
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 3
            Text {
                Layout.fillWidth: true
                text: root.stateText()
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(15)
                wrapMode: Text.Wrap
            }
            Text {
                Layout.fillWidth: true
                visible: text !== ""
                text: Agent.running ? Agent.detail : ""
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
                wrapMode: Text.Wrap
                maximumLineCount: 3
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
            Text {
                visible: Agent.running && Agent.since > 0 && Agent.state !== ""
                text: I18n.tr("assistant.since", [root.clock(new Date(Agent.since))])
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
        }
    }
    Heading {
        visible: Agent.hasLimits
        text: Agent.plan !== "" ? I18n.tr("assistant.usage.titlePlan", [Agent.plan]) : I18n.tr("assistant.usage.title")
        font.pixelSize: Theme.textSize(14)
        Layout.topMargin: 4
    }
    Repeater {
        model: Agent.hasBuckets ? Agent.usage.buckets : []
        delegate: Meter {
            required property var modelData
            label: modelData.label || I18n.tr("assistant.usage.title")
            window: modelData
            now: root.now
            resets: modelData?.resets ? root.when(modelData.resets, "assistant.usage.resetsAt", "assistant.usage.resetsOn") : ""
        }
    }
    Meter {
        visible: Agent.hasLimits && !Agent.hasBuckets
        label: I18n.tr("assistant.usage.session")
        window: Agent.usage.fiveHour ?? null
        now: root.now
        resets: window?.resets ? root.when(window.resets, "assistant.usage.resetsAt", "assistant.usage.resetsOn") : ""
    }
    Meter {
        visible: Agent.hasLimits && !Agent.hasBuckets
        label: I18n.tr("assistant.usage.week")
        window: Agent.usage.sevenDay ?? null
        now: root.now
        resets: window?.resets ? root.when(window.resets, "assistant.usage.resetsAt", "assistant.usage.resetsOn") : ""
    }
    Text {
        Layout.fillWidth: true
        visible: Agent.hasLimits
        text: Agent.usage.limitsUpdated ? root.when(Agent.usage.limitsUpdated, "assistant.usage.updatedAt", "assistant.usage.updatedOn") : I18n.tr("assistant.usage.empty")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
        wrapMode: Text.Wrap
    }
    function shortPath(path) {
        const home = Quickshell.env("HOME") || "";
        if (home !== "" && path === home)
            return "~";
        if (home !== "" && path.startsWith(home + "/"))
            return "~" + path.slice(home.length);
        return path;
    }
    Text {
        Layout.fillWidth: true
        visible: (Agent.usage.model ?? "") !== "" && (Agent.running || Agent.hasLimits)
        text: Agent.running && Agent.usage.context !== null && Agent.usage.context !== undefined ? I18n.tr("assistant.usage.modelContext", [Agent.usage.model, Math.round(Agent.usage.context)]) : Agent.usage.model ?? ""
        textFormat: Text.PlainText
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
    Text {
        Layout.fillWidth: true
        visible: Agent.running && Agent.sessionDirectory !== ""
        text: I18n.tr("assistant.folder", [root.shortPath(Agent.sessionDirectory)])
        textFormat: Text.PlainText
        elide: Text.ElideMiddle
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
    ActionButton {
        Layout.fillWidth: true
        enabled: Agent.available
        highlighted: !Agent.needsRestart
        iconName: "assistant"
        text: Agent.consoleOpen ? I18n.tr("assistant.hideConsole") : I18n.tr("assistant.openConsole")
        onClicked: {
            ShellState.close();
            Agent.toggleConsole();
        }
    }
    ActionButton {
        Layout.fillWidth: true
        visible: Agent.needsRestart
        highlighted: true
        iconName: "reboot"
        text: I18n.tr("assistant.restartWith", [Agent.probedName])
        onClicked: {
            ShellState.close();
            Agent.restartConsole();
        }
    }
    ActionButton {
        Layout.fillWidth: true
        visible: Agent.available
        iconName: "folder"
        text: I18n.tr("assistant.openHere")
        onClicked: {
            ShellState.close();
            Agent.openHere();
        }
    }
}
