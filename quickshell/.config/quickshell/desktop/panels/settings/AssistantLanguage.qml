import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// Settings → Assistant: the language Claude Code dictates and answers in (DESKTOP_AI_LANGUAGE, through
// HyprSettings into settings.lua). Default: the interface language.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 6
    readonly property var languages: ["", "english", "italian", "spanish", "french", "german", "portuguese"]
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
