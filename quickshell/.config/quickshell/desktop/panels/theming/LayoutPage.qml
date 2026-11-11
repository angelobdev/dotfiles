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
    // The values the drop-downs show, as the theme layout state holds them.
    readonly property int rounding: Theming.windows.rounding ?? 0
    readonly property int borderSize: Theming.windows.borderSize ?? 0
    readonly property int gapsIn: Theming.windows.gapsIn ?? 0
    readonly property int gapsOut: Theming.windows.gapsOut ?? 0
    // The drop-downs, with the preview beside them when the page is wide and below them when it is narrow.
    GridLayout {
        Layout.fillWidth: true
        columns: page.width >= 760 ? 2 : 1
        columnSpacing: 24
        rowSpacing: 16
        // A label and a drop-down each, in a column with the drop-downs lined up.
        ColumnLayout {
            id: options
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
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
        // An illustration of a tiled screen at 1:6 (the values are screen pixels): a bar, one tall window and two
        // stacked ones. Hyprland puts gaps_in on every side of a window, so windows are 2 x gaps_in apart.
        Rectangle {
            id: preview
            readonly property real ratio: 1 / 6
            readonly property real barHeight: 7
            readonly property real edge: page.gapsOut * ratio
            readonly property real between: 2 * page.gapsIn * ratio
            readonly property real frame: page.borderSize > 0 ? Math.max(1, page.borderSize * ratio) : 0
            readonly property real columnWidth: (width - 2 * edge - between) / 2
            readonly property real areaHeight: height - barHeight - 2 * edge
            readonly property real rowHeight: (areaHeight - between) / 2
            Layout.preferredWidth: 352
            Layout.preferredHeight: 220
            Layout.alignment: Qt.AlignTop
            color: Theme.background
            border.width: 1
            border.color: Theme.stroke
            radius: 6
            Rectangle {
                width: parent.width
                height: preview.barHeight
                color: Theme.tile
                radius: 6
            }
            Repeater {
                // The focused window is the tall one.
                model: [
                    {
                        x: 0,
                        y: 0,
                        w: preview.columnWidth,
                        h: preview.areaHeight,
                        active: true
                    },
                    {
                        x: preview.columnWidth + preview.between,
                        y: 0,
                        w: preview.columnWidth,
                        h: preview.rowHeight,
                        active: false
                    },
                    {
                        x: preview.columnWidth + preview.between,
                        y: preview.rowHeight + preview.between,
                        w: preview.columnWidth,
                        h: preview.rowHeight,
                        active: false
                    }
                ]
                Rectangle {
                    id: tile
                    required property var modelData
                    x: preview.edge + modelData.x
                    y: preview.barHeight + preview.edge + modelData.y
                    width: modelData.w
                    height: modelData.h
                    color: Theme.tile
                    radius: Math.min(page.rounding * preview.ratio, Math.min(width, height) / 2)
                    border.width: preview.frame
                    border.color: modelData.active ? Theme.frameActive : Theme.frameInactive
                }
            }
        }
    }
    Item {
        Layout.fillHeight: true
    }
}
