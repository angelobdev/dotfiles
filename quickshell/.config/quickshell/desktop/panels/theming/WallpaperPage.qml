import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import "../.."
import "../../components"
import "../../services"
import "../../components/FileUrl.js" as FileUrl

// The wallpaper page of Settings → Appearance (panels/theming/ThemingView.qml), built the first time its tab shows.
ColumnLayout {
    id: page
    // The Theming panel: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: wallpaperGrid
    spacing: 10
    RowLayout {
        Layout.fillWidth: true
        visible: Theming.missingWallpapers
        Text {
            Layout.fillWidth: true
            text: Theming.downloading ? I18n.tr("theming.downloading") : I18n.tr("theming.notDownloaded")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        ActionButton {
            outlined: true
            text: I18n.tr("theming.download")
            enabled: !Theming.downloading
            onClicked: Theming.fetch()
        }
    }
    GridView {
        id: wallpaperGrid
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 230)))
        cellHeight: Math.round(cellWidth * 0.62)
        // Keyed by file: a thumbnail or a download that lands updates its cell, not the whole grid.
        model: ScriptModel {
            values: Theming.wallpaperItems
            objectProp: "path"
        }
        keyNavigationEnabled: true
        function choose(item) {
            if (!item)
                return;
            if (item.custom)
                ShellState.toggle("wallpaper");
            else if (item.downloaded)
                Theming.setWallpaper(item.path);
        }
        Keys.onReturnPressed: choose(Theming.wallpaperItems[currentIndex])
        Keys.onEnterPressed: choose(Theming.wallpaperItems[currentIndex])
        delegate: Item {
            id: wallCell
            required property var modelData
            required property int index
            readonly property bool active: !modelData.custom && modelData.path === Theming.wallpaper
            width: wallpaperGrid.cellWidth
            height: wallpaperGrid.cellHeight
            Rectangle {
                id: frame
                anchors {
                    fill: parent
                    margins: 6
                }
                radius: Theme.corner(12)
                color: Theme.tile
                clip: true
                Image {
                    anchors {
                        fill: parent
                        margins: 3
                    }
                    visible: wallCell.modelData.thumb !== ""
                    // Cached JPEG thumbnails: Qt here cannot decode WebP, and full-size 8K images would be slow.
                    source: visible ? FileUrl.of(wallCell.modelData.thumb) : ""
                    sourceSize: Qt.size(480, 300)
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                    cache: true
                }
                ColumnLayout {
                    anchors.centerIn: parent
                    visible: wallCell.modelData.thumb === ""
                    spacing: 6
                    Icon {
                        Layout.alignment: Qt.AlignHCenter
                        name: "image"
                        color: Theme.muted
                        width: 26
                        height: 26
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: wallCell.modelData.custom ? I18n.tr("theming.custom") : !wallCell.modelData.downloaded ? (Theming.downloading ? I18n.tr("theming.downloading") : I18n.tr("theming.notDownloaded")) : I18n.tr("theming.preparing")
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                    }
                }
            }
            // Outline drawn on top so the thumbnail cannot cover it.
            Rectangle {
                anchors.fill: frame
                radius: Theme.corner(12)
                color: "transparent"
                border.width: wallCell.active || wallpaperGrid.currentIndex === wallCell.index && wallpaperGrid.activeFocus ? 2 : 1
                border.color: wallCell.active ? Theme.accent : wallpaperGrid.currentIndex === wallCell.index && wallpaperGrid.activeFocus ? Theme.handleFocus : Theme.stroke
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    wallpaperGrid.currentIndex = wallCell.index;
                    wallpaperGrid.choose(wallCell.modelData);
                }
            }
        }
        ScrollBar.vertical: ScrollBar {}
    }
}
