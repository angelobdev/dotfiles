import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// The Claude Code assistant: what Claude is doing, the subscription usage its status line reports
// (agent.py), and the drop-down console. The assistant panel (its bar icon) and Settings → Assistant show it.
ColumnLayout {
    id: root
    // On screen: the clock that dates the usage runs only then.
    property bool shown: false
    readonly property Item focusItem: root
    spacing: 14
    property date now: new Date()
    // The usage of the subscription: Claude Code reports it, so with herdr only while one of its agents runs.
    readonly property bool claudeShown: Agent.herdr ? Agent.agents.some(agent => agent.app === "claude-code") : Agent.claude
    onShownChanged: if (shown)
        now = new Date()
    function stateText() {
        if (!Agent.available)
            return I18n.tr("assistant.states.missing");
        if (!Agent.running)
            return Agent.primaryAgent ? I18n.tr("assistant.states.off", [Agent.primaryAgent.name]) : I18n.tr("assistant.states.offAny");
        return stateName(Agent.state);
    }
    function stateName(state) {
        switch (state) {
        case "running":
            return I18n.tr("assistant.states.running");
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
    // herdr: every agent, the one needing attention first; a click shows it in the console.
    ColumnLayout {
        visible: Agent.herdr
        Layout.fillWidth: true
        spacing: 4
        Text {
            visible: Agent.agents.length === 0
            Layout.fillWidth: true
            text: I18n.tr("assistant.noAgents")
            wrapMode: Text.Wrap
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(13)
        }
        Repeater {
            model: Agent.agents
            ActionButton {
                id: agentRow
                required property var modelData
                Layout.fillWidth: true
                implicitHeight: agentText.implicitHeight + 16
                alignLeft: true
                onClicked: Agent.showAgent(modelData.address)
                RowLayout {
                    anchors {
                        fill: parent
                        leftMargin: 12
                        rightMargin: 12
                    }
                    spacing: 10
                    Rectangle {
                        Layout.alignment: Qt.AlignTop
                        Layout.topMargin: 6
                        implicitWidth: 8
                        implicitHeight: 8
                        radius: 4
                        color: ["permission", "error"].includes(agentRow.modelData.state) ? Theme.danger : agentRow.modelData.state === "working" ? Theme.accent : Theme.text
                    }
                    ColumnLayout {
                        id: agentText
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: agentRow.modelData.name + (agentRow.modelData.where ? " · " + agentRow.modelData.where : "")
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                        }
                        Text {
                            Layout.fillWidth: true
                            text: [root.stateName(agentRow.modelData.state), agentRow.modelData.msg].filter(part => part !== "").join(" · ")
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                    }
                }
            }
        }
    }
    RowLayout {
        visible: !Agent.herdr
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
        visible: root.claudeShown
        text: Agent.plan !== "" ? I18n.tr("assistant.usage.titlePlan", [Agent.plan]) : I18n.tr("assistant.usage.title")
        font.pixelSize: Theme.textSize(14)
        Layout.topMargin: 4
    }
    Meter {
        visible: root.claudeShown
        label: I18n.tr("assistant.usage.session")
        window: Agent.usage.fiveHour ?? null
        now: root.now
        resets: window?.resets ? root.when(window.resets, "assistant.usage.resetsAt", "assistant.usage.resetsOn") : ""
    }
    Meter {
        visible: root.claudeShown
        label: I18n.tr("assistant.usage.week")
        window: Agent.usage.sevenDay ?? null
        now: root.now
        resets: window?.resets ? root.when(window.resets, "assistant.usage.resetsAt", "assistant.usage.resetsOn") : ""
    }
    Text {
        Layout.fillWidth: true
        visible: root.claudeShown
        text: Agent.usage.limitsUpdated ? root.when(Agent.usage.limitsUpdated, "assistant.usage.updatedAt", "assistant.usage.updatedOn") : I18n.tr("assistant.usage.empty")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
        wrapMode: Text.Wrap
    }
    Text {
        Layout.fillWidth: true
        visible: root.claudeShown && Agent.running && (Agent.usage.model ?? "") !== ""
        text: Agent.usage.context !== null && Agent.usage.context !== undefined ? I18n.tr("assistant.usage.modelContext", [Agent.usage.model, Math.round(Agent.usage.context)]) : Agent.usage.model ?? ""
        textFormat: Text.PlainText
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
    ActionButton {
        Layout.fillWidth: true
        enabled: Agent.available
        highlighted: true
        iconName: "assistant"
        text: Agent.consoleOpen ? I18n.tr("assistant.hideConsole") : I18n.tr("assistant.openConsole")
        onClicked: {
            ShellState.close();
            Agent.toggleConsole();
        }
    }
}
