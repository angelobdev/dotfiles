import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// The Claude Code assistant, opened from its bar icon: what Claude is doing, the subscription usage its
// status line reports (agent.py), and the drop-down console.
Overlay {
    id: root
    panelName: "agent"
    property date now: new Date()
    onOpened: now = new Date()
    function stateText() {
        if (!Agent.available)
            return I18n.tr("assistant.states.missing");
        if (!Agent.running)
            return I18n.tr("assistant.states.off");
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
        return I18n.locale.toString(date, I18n.tr("assistant.timeFormat"));
    }
    // Today "at 22:37", another day "Sun 20:50": todayKey or otherKey with the time in it.
    function when(seconds, todayKey, otherKey) {
        const date = new Date(seconds * 1000);
        if (date.toDateString() === now.toDateString())
            return I18n.tr(todayKey, [clock(date)]);
        return I18n.tr(otherKey, [I18n.locale.toString(date, I18n.tr("assistant.dayTimeFormat"))]);
    }
    Timer {
        interval: 30000
        repeat: true
        running: root.open
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
                font.pixelSize: 13
            }
            Text {
                text: meter.known ? Math.round(meter.used) + "%" : "–"
                color: meter.used >= 90 ? Theme.danger : Theme.text
                font.family: Theme.font
                font.pixelSize: 13
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
            font.pixelSize: 11
        }
    }
    SidePanelCard {
        height: Math.min(layout.implicitHeight + 2 * Theme.panelPadding, parent.height - 76)
        ColumnLayout {
            id: layout
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: Theme.panelPadding
            }
            spacing: 14
            PanelHeader {
                title: I18n.tr("assistant.claude")
                Layout.fillWidth: true
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
                        font.pixelSize: 15
                        wrapMode: Text.Wrap
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: text !== ""
                        text: Agent.running ? Agent.detail : ""
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: 12
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
                        font.pixelSize: 11
                    }
                }
            }
            Heading {
                text: Agent.plan !== "" ? I18n.tr("assistant.usage.titlePlan", [Agent.plan]) : I18n.tr("assistant.usage.title")
                font.pixelSize: 14
                Layout.topMargin: 4
            }
            Meter {
                label: I18n.tr("assistant.usage.session")
                window: Agent.usage.fiveHour ?? null
                now: root.now
                resets: window?.resets ? root.when(window.resets, "assistant.usage.resetsAt", "assistant.usage.resetsOn") : ""
            }
            Meter {
                label: I18n.tr("assistant.usage.week")
                window: Agent.usage.sevenDay ?? null
                now: root.now
                resets: window?.resets ? root.when(window.resets, "assistant.usage.resetsAt", "assistant.usage.resetsOn") : ""
            }
            Text {
                Layout.fillWidth: true
                text: Agent.usage.limitsUpdated ? root.when(Agent.usage.limitsUpdated, "assistant.usage.updatedAt", "assistant.usage.updatedOn") : I18n.tr("assistant.usage.empty")
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: 11
                wrapMode: Text.Wrap
            }
            Text {
                Layout.fillWidth: true
                visible: Agent.running && (Agent.usage.model ?? "") !== ""
                text: Agent.usage.context !== null && Agent.usage.context !== undefined ? I18n.tr("assistant.usage.modelContext", [Agent.usage.model, Math.round(Agent.usage.context)]) : Agent.usage.model ?? ""
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: 11
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
    }
}
