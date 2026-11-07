import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"
import "../theming"

// Settings → Assistant: the coding agents of agents.py (one JSON file each), installed from here in a terminal
// the user sees, and the primary one that Super + A opens.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 6
    readonly property var listed: Agent.catalog.agents ?? []
    readonly property var installed: listed.filter(agent => agent.path !== "")
    readonly property var automatic: installed[0] ?? null
    Component.onCompleted: Agent.refreshCatalog()
    component GroupTitle: Text {
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        font.weight: Font.DemiBold
    }
    component Hint: Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
    GroupTitle {
        text: I18n.tr("assistant.agentsGroup")
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: rows.implicitHeight + 24
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
            spacing: 10
            Setting {
                label: I18n.tr("assistant.primary")
                enabled: root.installed.length > 0
                options: [
                    {
                        name: "",
                        label: root.automatic ? I18n.tr("assistant.primaryAutomatic", [root.automatic.name]) : I18n.tr("assistant.primaryNone")
                    }
                ].concat(root.installed.map(agent => ({
                            name: agent.id,
                            label: agent.name
                        })))
                current: root.installed.some(agent => agent.id === Config.aiPrimary) ? Config.aiPrimary : ""
                onChosen: name => Config.set("aiPrimary", name, "")
            }
            Hint {
                visible: (Agent.catalog.override ?? "") !== ""
                text: I18n.tr("assistant.primaryOverride", [Agent.catalog.override ?? ""])
            }
            Hint {
                text: Agent.herdr ? I18n.tr("assistant.primaryHerdr") : I18n.tr("assistant.primaryKitty")
            }
            Repeater {
                model: root.listed
                RowLayout {
                    id: agentRow
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 12
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: agentRow.modelData.name + (agentRow.modelData.vendor ? " · " + agentRow.modelData.vendor : "")
                            textFormat: Text.PlainText
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                        }
                        Hint {
                            text: agentRow.modelData.path !== "" ? I18n.tr("assistant.installedAt", [agentRow.modelData.path]) : agentRow.modelData.missing.length > 0 ? I18n.tr("assistant.needs", [agentRow.modelData.missing.join(", ")]) : I18n.tr("assistant.notInstalled")
                            textFormat: Text.PlainText
                        }
                    }
                    ActionButton {
                        visible: agentRow.modelData.path === "" && agentRow.modelData.install !== ""
                        enabled: !Agent.installing && agentRow.modelData.missing.length === 0
                        text: Agent.installing ? I18n.tr("assistant.installing") : I18n.tr("assistant.installAction")
                        onClicked: Agent.install(agentRow.modelData.id)
                    }
                }
            }
            Hint {
                text: I18n.tr("assistant.agentsHint")
            }
        }
    }
}
