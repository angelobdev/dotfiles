import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "../components/FileUrl.js" as FileUrl

// The wallpaper switcher (Super + Ctrl + W): the wallpapers of the current theme in a row to move through and apply
// with Enter. Super + Shift + W opens the picker that browses any folder.
Overlay {
    id: root
    panelName: "wallpapers"
    dialog: true
    // Downloaded images of the set; the tile for an image of your own belongs to the picker.
    readonly property var wallpapers: Theming.wallpaperItems.filter(entry => !entry.custom && entry.downloaded)
    function apply(index) {
        const entry = wallpapers[index];
        if (!entry)
            return;
        if (entry.path !== Theming.wallpaper)
            Theming.setWallpaper(entry.path);
        ShellState.close();
    }
    onOpened: {
        Theming.query(["pack"]);
        carousel.start();
    }
    onWallpapersChanged: if (open)
        Qt.callLater(carousel.start)
    Card {
        anchors.centerIn: parent
        width: Math.min(Theme.dialogWide, parent.width - 48)
        height: layout.implicitHeight + 2 * Theme.dialogPadding
        ColumnLayout {
            id: layout
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: Theme.dialogPadding
            }
            spacing: 14
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("wallpaper.switcher")
                settingsSection: "appearance"
            }
            Text {
                Layout.fillWidth: true
                visible: root.wallpapers.length === 0
                text: Theming.missingWallpapers ? I18n.tr("wallpaper.switcherMissing") : I18n.tr("wallpaper.switcherEmpty")
                wrapMode: Text.Wrap
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(13)
            }
            Carousel {
                id: carousel
                Layout.fillWidth: true
                visible: root.wallpapers.length > 0
                model: root.wallpapers
                appliedIndex: root.wallpapers.findIndex(entry => entry.path === Theming.wallpaper)
                label: root.wallpapers[currentIndex]?.name ?? ""
                hint: I18n.tr("wallpaper.switcherKeys")
                onActivated: index => root.apply(index)
                card: Item {
                    id: wallpaperCard
                    property var modelData: ({})
                    Rectangle {
                        anchors.fill: parent
                        color: Theme.raised
                    }
                    // The thumbnail when it is made, else the image itself, scaled down while it loads.
                    Image {
                        anchors.fill: parent
                        source: FileUrl.of(wallpaperCard.modelData.thumb || wallpaperCard.modelData.path || "")
                        sourceSize: Qt.size(480, 300)
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                    }
                }
            }
        }
    }
}
