import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// The layout page of Settings → Appearance (panels/theming/ThemingView.qml), built the first time its tab shows:
// the bar style, the effects, and the window rounding, border and gaps, for every theme.
ColumnLayout {
    id: page
    // The Theming view: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: options
    spacing: 10
    // Options: a label and a drop-down each, wrapping onto as many lines as the width needs.
    Flow {
        id: options
        Layout.fillWidth: true
        spacing: 16
        Setting {
            label: I18n.tr("theming.bar")
            options: [
                {
                    name: "shade",
                    label: I18n.tr("theming.barShaded")
                },
                {
                    name: "transparent",
                    label: I18n.tr("theming.barTransparent")
                }
            ]
            current: Theme.barStyle
            onChosen: name => Theming.setBarStyle(name)
        }
        // Reduced: no animations, blur, shadows or glass, for less powerful machines (theme.py reduce-effects).
        Setting {
            label: I18n.tr("theming.effects")
            options: [
                {
                    name: "full",
                    label: I18n.tr("theming.effectsFull")
                },
                {
                    name: "reduced",
                    label: I18n.tr("theming.effectsReduced")
                }
            ]
            current: Theme.reduceEffects ? "reduced" : "full"
            onChosen: name => Theming.setReduceEffects(name === "reduced")
        }
        // Windows: corner rounding and border width; the border colours come from the theme.
        Setting {
            label: I18n.tr("theming.windowRounding")
            options: [0, 4, 8, 12, 16, 20, 24].map(value => ({
                        name: String(value),
                        label: String(value)
                    }))
            current: String(Theming.windows.rounding)
            onChosen: name => Theming.setWindowStyle("rounding", Number(name))
        }
        Setting {
            label: I18n.tr("theming.windowBorder")
            options: [0, 1, 2, 3, 4].map(value => ({
                        name: String(value),
                        label: value === 0 ? I18n.tr("theming.windowBorderNone") : String(value)
                    }))
            current: String(Theming.windows.borderSize)
            onChosen: name => Theming.setWindowStyle("border", Number(name))
        }
        // Gaps between windows and to the screen edges (Hyprland gaps_in / gaps_out).
        Setting {
            label: I18n.tr("theming.windowGapsIn")
            options: [0, 2, 4, 6, 8, 12, 16].map(value => ({
                        name: String(value),
                        label: String(value)
                    }))
            current: String(Theming.windows.gapsIn)
            onChosen: name => Theming.setWindowStyle("gapsIn", Number(name))
        }
        Setting {
            label: I18n.tr("theming.windowGapsOut")
            options: [0, 4, 8, 12, 16, 24, 32].map(value => ({
                        name: String(value),
                        label: String(value)
                    }))
            current: String(Theming.windows.gapsOut)
            onChosen: name => Theming.setWindowStyle("gapsOut", Number(name))
        }
    }
    Text {
        Layout.fillWidth: true
        text: I18n.tr("theming.barHint")
        elide: Text.ElideRight
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
    Item {
        Layout.fillHeight: true
    }
}
