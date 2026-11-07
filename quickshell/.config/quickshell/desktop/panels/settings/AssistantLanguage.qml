import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// Settings -> Assistant: which coding agent opens in the console (Config.aiAgent in shell.json), its default
// working folder (Config.aiDirectory), Antigravity quota statusline integration when Antigravity is selected,
// and Claude Code dictation and reply language when Claude Code is selected.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 14
    readonly property string effectiveAgent: Config.aiAgent !== "" ? Config.aiAgent : Agent.probedAgent
    readonly property var baseAgents: [
        { name: "antigravity", label: "Antigravity" },
        { name: "claude", label: "Claude Code" },
        { name: "codex", label: "Codex" },
        { name: "gemini", label: "Gemini CLI" },
        { name: "opencode", label: "OpenCode" },
        { name: "pi", label: "Pi" }
    ]
    readonly property var knownAgents: [{
            name: "",
            label: Agent.autoName !== "" ? I18n.tr("settings.hypr.agentAutoDetected", [Agent.autoName]) : I18n.tr("settings.hypr.agentAuto")
        }].concat(baseAgents.map(item => ({
                name: item.name,
                label: !Agent.probeLoaded || Agent.installedAgents.includes(item.name) ? item.label : I18n.tr("settings.hypr.agentNotInstalled", [item.label])
            })))
    readonly property var agentOptions: knownAgents.some(item => item.name === Config.aiAgent) ? knownAgents : knownAgents.concat([{
                name: Config.aiAgent,
                label: Config.aiAgent
            }])
    readonly property var languages: ["", "english", "italian", "spanish", "french", "german", "portuguese"]
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 6
        Text {
            text: I18n.tr("settings.hypr.agentGroup")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
            font.weight: Font.DemiBold
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: agentRows.implicitHeight + 20
            radius: Theme.corner(12)
            color: Theme.tile
            ColumnLayout {
                id: agentRows
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 10
                    leftMargin: 14
                    rightMargin: 14
                }
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: I18n.tr("settings.hypr.agent")
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                        }
                        Text {
                            Layout.fillWidth: true
                            text: I18n.tr("settings.hypr.agentHint")
                            wrapMode: Text.WordWrap
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                    }
                    ActionButton {
                        visible: Config.isSet("aiAgent")
                        compact: true
                        text: I18n.tr("settings.reset")
                        onClicked: Config.reset("aiAgent")
                    }
                    ChoiceCombo {
                        Accessible.name: I18n.tr("settings.hypr.agent")
                        enabled: !Config.unreadable
                        options: root.agentOptions
                        current: Config.aiAgent
                        onChosen: name => Config.set("aiAgent", name, "")
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: Theme.stroke
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: I18n.tr("settings.hypr.agentDirectory")
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                        }
                        Text {
                            Layout.fillWidth: true
                            text: I18n.tr("settings.hypr.agentDirectoryHint")
                            wrapMode: Text.WordWrap
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                    }
                    ActionButton {
                        visible: Config.isSet("aiDirectory")
                        compact: true
                        text: I18n.tr("settings.reset")
                        onClicked: Config.reset("aiDirectory")
                    }
                    InputField {
                        id: directoryField
                        implicitWidth: 220
                        enabled: !Config.unreadable
                        text: Config.aiDirectory
                        placeholderText: "~/.dotfiles"
                        Accessible.name: I18n.tr("settings.hypr.agentDirectory")
                        onEditingFinished: {
                            if (text.trim() !== Config.aiDirectory)
                                Config.set("aiDirectory", text.trim(), "");
                        }
                        Keys.onEscapePressed: text = Config.aiDirectory
                    }
                }
            }
        }
    }
    // Antigravity-only: statusLine hook in ~/.gemini/antigravity-cli/settings.json for live quota buckets.
    ColumnLayout {
        Layout.fillWidth: true
        visible: root.effectiveAgent === "antigravity"
        spacing: 6
        Text {
            text: I18n.tr("settings.hypr.agyGroup")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
            font.weight: Font.DemiBold
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: agyRow.implicitHeight + 20
            radius: Theme.corner(12)
            color: Theme.tile
            RowLayout {
                id: agyRow
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 10
                    leftMargin: 14
                    rightMargin: 14
                }
                spacing: 14
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: I18n.tr("settings.hypr.agyStatusline")
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("settings.hypr.agyStatuslineHint")
                        wrapMode: Text.WordWrap
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(11)
                    }
                }
                ControlSwitch {
                    checked: Agent.agyStatusline
                    Accessible.name: I18n.tr("settings.hypr.agyStatusline")
                    onToggled: Agent.setAgyStatusline(checked)
                }
            }
        }
    }
    // Claude Code-only (unless already customized): DESKTOP_AI_LANGUAGE passed via --settings.
    ColumnLayout {
        Layout.fillWidth: true
        visible: root.effectiveAgent === "claude" || HyprSettings.language !== ""
        spacing: 6
        Text {
            text: I18n.tr("settings.hypr.assistantGroup")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
            font.weight: Font.DemiBold
        }
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: languageRow.implicitHeight + 20
            radius: Theme.corner(12)
            color: Theme.tile
            RowLayout {
                id: languageRow
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: 10
                    leftMargin: 14
                    rightMargin: 14
                }
                spacing: 14
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Text {
                        text: I18n.tr("settings.hypr.assistantLanguage")
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("settings.hypr.assistantLanguageHint")
                        wrapMode: Text.WordWrap
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(11)
                    }
                }
                ChoiceCombo {
                    Accessible.name: I18n.tr("settings.hypr.assistantLanguage")
                    options: root.languages.map(name => ({
                                name: name,
                                label: I18n.tr({
                                    "": "settings.hypr.languages.default",
                                    english: "settings.hypr.languages.english",
                                    italian: "settings.hypr.languages.italian",
                                    spanish: "settings.hypr.languages.spanish",
                                    french: "settings.hypr.languages.french",
                                    german: "settings.hypr.languages.german",
                                    portuguese: "settings.hypr.languages.portuguese"
                                }[name])
                            }))
                    current: HyprSettings.language
                    onChosen: name => HyprSettings.setLanguage(name)
                }
            }
        }
    }
}
