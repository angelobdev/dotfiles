import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// The layout page of Settings → Appearance (panels/theming/ThemingView.qml), built the first time its tab shows:
// the window rounding, border and gaps, for every theme, one under the other.
ColumnLayout {
    id: page
    // The Theming view: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: options
    spacing: 10
    // A label and a drop-down each, in a column with the drop-downs lined up.
    ColumnLayout {
        id: options
        Layout.fillWidth: true
        spacing: 10
        // Windows: corner rounding and border width; the border colours come from the theme.
        Setting {
            labelWidth: 200
            label: I18n.tr("theming.windowRounding")
            options: [0, 4, 8, 12, 16, 20, 24].map(value => ({
                        name: String(value),
                        label: I18n.tr("theming.pixels", [value])
                    }))
            current: String(Theming.windows.rounding)
            onChosen: name => Theming.setWindowStyle("rounding", Number(name))
        }
        Setting {
            labelWidth: 200
            label: I18n.tr("theming.windowBorder")
            options: [0, 1, 2, 3, 4].map(value => ({
                        name: String(value),
                        label: value === 0 ? I18n.tr("theming.windowBorderNone") : I18n.tr("theming.pixels", [value])
                    }))
            current: String(Theming.windows.borderSize)
            onChosen: name => Theming.setWindowStyle("border", Number(name))
        }
        // Gaps between windows and to the screen edges (Hyprland gaps_in / gaps_out).
        Setting {
            labelWidth: 200
            label: I18n.tr("theming.windowGapsIn")
            options: [0, 2, 4, 6, 8, 12, 16].map(value => ({
                        name: String(value),
                        label: I18n.tr("theming.pixels", [value])
                    }))
            current: String(Theming.windows.gapsIn)
            onChosen: name => Theming.setWindowStyle("gapsIn", Number(name))
        }
        Setting {
            labelWidth: 200
            label: I18n.tr("theming.windowGapsOut")
            options: [0, 4, 8, 12, 16, 24, 32].map(value => ({
                        name: String(value),
                        label: I18n.tr("theming.pixels", [value])
                    }))
            current: String(Theming.windows.gapsOut)
            onChosen: name => Theming.setWindowStyle("gapsOut", Number(name))
        }
    }
    Item {
        Layout.fillHeight: true
    }
}
