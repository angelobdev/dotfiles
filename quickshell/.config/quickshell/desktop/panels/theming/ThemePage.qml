import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"
import "../../components/FileUrl.js" as FileUrl

// The theme page of the Theming panel (panels/ThemingPanel.qml), built the first time its tab shows.
ColumnLayout {
    id: page
    // The Theming panel: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: themeGrid
    spacing: 10
    // Options: a label and a drop-down each, wrapping onto as many lines as the width needs.
    Flow {
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
        // Dynamic theme: light or dark (Auto lets the image decide).
        Setting {
            visible: Theming.dynamic.available
            label: I18n.tr("theming.dynamicMode")
            options: [
                {
                    name: "auto",
                    label: I18n.tr("theming.dynamicModes.auto")
                },
                {
                    name: "dark",
                    label: I18n.tr("theming.dynamicModes.dark")
                },
                {
                    name: "light",
                    label: I18n.tr("theming.dynamicModes.light")
                }
            ]
            current: Theming.dynamic.mode
            onChosen: name => Theming.setDynamic("mode", name)
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
    GridView {
        id: themeGrid
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 230)))
        cellHeight: 190
        model: Theming.themeItems
        keyNavigationEnabled: true
        // The dynamic card generates from the current wallpaper, also when already active.
        function choose(item) {
            if (item?.dynamic)
                Theming.generate();
            else if (item)
                Theming.setTheme(item.id);
        }
        Keys.onReturnPressed: choose(Theming.themeItems[currentIndex])
        Keys.onEnterPressed: choose(Theming.themeItems[currentIndex])
        delegate: Item {
            id: themeCell
            required property var modelData
            required property int index
            readonly property bool dynamicCard: modelData.dynamic === true
            readonly property bool unavailable: dynamicCard && !Theming.dynamic.available
            // Before its first generation the dynamic card draws its mock-up in the current colours.
            readonly property var preview: modelData.preview ?? {
                bg: Theme.background,
                base: Theme.raised,
                raised: Theme.tile,
                border: Theme.stroke,
                fg: Theme.text,
                muted: Theme.muted,
                accent: Theme.accent,
                accentFg: Theme.accentText,
                ansi: []
            }
            readonly property bool active: modelData.id === Theming.current
            width: themeGrid.cellWidth
            height: themeGrid.cellHeight
            Rectangle {
                anchors {
                    fill: parent
                    margins: 6
                }
                radius: Theme.corner(14)
                color: themeMouse.containsMouse || themeGrid.currentIndex === themeCell.index && themeGrid.activeFocus ? Theme.raised : Theme.tile
                border.width: themeCell.active ? 2 : 1
                border.color: themeCell.active ? Theme.accent : Theme.stroke
                ColumnLayout {
                    anchors {
                        fill: parent
                        margins: 10
                    }
                    spacing: 8
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Theme.corner(8)
                        color: themeCell.preview.bg
                        clip: themeCell.dynamicCard
                        // The dynamic mock-up sits on the wallpaper it takes its colours from.
                        Image {
                            anchors.fill: parent
                            visible: themeCell.dynamicCard && Theming.wallpaperThumb !== ""
                            source: visible ? FileUrl.of(Theming.wallpaperThumb) : ""
                            sourceSize: Qt.size(480, 300)
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            opacity: themeCell.unavailable ? 0.35 : 1
                        }
                        Rectangle {
                            visible: !themeCell.unavailable
                            anchors {
                                left: parent.left
                                right: parent.right
                                top: parent.top
                            }
                            height: 12
                            radius: Theme.corner(8)
                            color: themeCell.preview.base
                        }
                        Rectangle {
                            visible: !themeCell.unavailable
                            x: 12
                            y: 22
                            width: parent.width * 0.55
                            height: parent.height - 34
                            radius: Theme.corner(6)
                            color: themeCell.preview.raised
                            border.color: themeCell.preview.border
                            Text {
                                x: 8
                                y: 6
                                text: "Aa"
                                color: themeCell.preview.fg
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(15)
                                font.bold: true
                            }
                            Text {
                                x: 8
                                y: 28
                                text: I18n.tr("theming.previewText")
                                color: themeCell.preview.muted
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(10)
                            }
                        }
                        Text {
                            anchors {
                                fill: parent
                                margins: 12
                            }
                            visible: themeCell.unavailable
                            text: I18n.tr("theming.dynamicInstall")
                            wrapMode: Text.WordWrap
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(12)
                        }
                        Rectangle {
                            visible: !themeCell.unavailable
                            anchors {
                                right: parent.right
                                bottom: parent.bottom
                                margins: 12
                            }
                            width: 46
                            height: 18
                            radius: Theme.corner(9)
                            color: themeCell.preview.accent
                            Text {
                                anchors.centerIn: parent
                                text: I18n.tr("theming.previewButton")
                                color: themeCell.preview.accentFg
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(10)
                                font.bold: true
                            }
                        }
                    }
                    Row {
                        spacing: 3
                        // Keeps the card height when the dynamic theme has no colours yet.
                        Layout.preferredHeight: 14
                        Repeater {
                            model: themeCell.preview.ansi.slice(1, 7).concat(themeCell.preview.ansi.slice(9, 11))
                            Rectangle {
                                required property string modelData
                                width: 14
                                height: 14
                                radius: Theme.corner(7)
                                color: modelData
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: themeCell.dynamicCard ? I18n.tr("theming.dynamic") : themeCell.modelData.name
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                            font.bold: themeCell.active
                        }
                        Text {
                            visible: themeCell.dynamicCard && !themeCell.active && !themeCell.unavailable
                            text: I18n.tr("theming.dynamicHint")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                        Text {
                            visible: themeCell.active
                            text: I18n.tr("theming.current")
                            color: Theme.accent
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                        // Opens the glass page; the MouseArea of the card lies beneath it.
                        CompactIconButton {
                            visible: themeCell.active && !!Theming.glass
                            iconName: "controls"
                            iconSize: 16
                            tooltip: I18n.tr("theming.glassSettings")
                            onClicked: page.panel.showTab("glass")
                        }
                    }
                }
            }
            // Beneath the content of the card, so buttons on it take their own clicks.
            MouseArea {
                id: themeMouse
                z: -1
                anchors.fill: parent
                hoverEnabled: true
                enabled: !themeCell.unavailable
                onClicked: {
                    themeGrid.currentIndex = themeCell.index;
                    themeGrid.choose(themeCell.modelData);
                }
            }
        }
        ScrollBar.vertical: ScrollBar {}
    }
}
