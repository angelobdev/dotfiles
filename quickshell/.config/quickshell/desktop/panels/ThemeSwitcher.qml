import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import ".."
import "../components"
import "../services"
import "../components/FileUrl.js" as FileUrl

// The theme switcher (Super + Ctrl + T): each theme on the wallpaper it would show, with a mock-up of its colours,
// in a row to move through and apply with Enter. Settings → Appearance keeps the rest of the theme options.
Overlay {
    id: root
    panelName: "themes"
    dialog: true
    // The dynamic theme only where it can be generated (matugen installed).
    readonly property var themes: Theming.themeItems.filter(theme => !(theme.dynamic && !Theming.dynamic.available))
    // Theme id -> {wallpaper, thumb, ready}, from theme.py previews.
    property var previews: ({})
    function apply(index) {
        const theme = themes[index];
        if (!theme)
            return;
        if (theme.dynamic)
            Theming.generate();
        else
            Theming.setTheme(theme.id);
        ShellState.close();
    }
    function readPreviews(text) {
        try {
            const next = {};
            for (const entry of JSON.parse(text))
                next[entry.id] = entry;
            previews = next;
        } catch (failure) {}
    }
    onOpened: {
        Theming.query(["listing", "pack"]);
        carousel.start();
        if (!previewReader.running)
            previewReader.running = true;
    }
    // The applied theme stays in the middle until the list arrives.
    onThemesChanged: if (open)
        Qt.callLater(carousel.start)
    // Thumbnails it lacks are made once the ones there are show.
    Process {
        id: previewReader
        command: ["python3", Theming.helper, "previews"]
        stdout: StdioCollector {
            onStreamFinished: {
                root.readPreviews(text);
                if (Object.values(root.previews).some(entry => entry.wallpaper !== "" && !entry.ready) && !thumbMaker.running)
                    thumbMaker.running = true;
            }
        }
    }
    Process {
        id: thumbMaker
        command: ["python3", Theming.helper, "previews", "--make"]
        stdout: StdioCollector {
            onStreamFinished: root.readPreviews(text)
        }
    }
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
                title: I18n.tr("theming.switcher")
                settingsSection: "appearance"
            }
            Carousel {
                id: carousel
                Layout.fillWidth: true
                model: root.themes
                appliedIndex: root.themes.findIndex(theme => theme.dynamic ? Theming.current === "dynamic" : theme.id === Theming.current)
                label: {
                    const theme = root.themes[currentIndex];
                    return !theme ? "" : theme.dynamic ? I18n.tr("theming.dynamic") : theme.name;
                }
                hint: I18n.tr("theming.switcherKeys")
                onActivated: index => root.apply(index)
                card: Item {
                    id: themeCard
                    property var modelData: ({})
                    readonly property bool dynamicCard: modelData.dynamic === true
                    readonly property var entry: root.previews[modelData.id] ?? {}
                    readonly property string image: dynamicCard ? Theming.wallpaperThumb : entry.ready ? entry.thumb : ""
                    readonly property var colors: modelData.preview ?? {
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
                    Rectangle {
                        anchors.fill: parent
                        color: themeCard.colors.bg
                    }
                    Image {
                        anchors.fill: parent
                        visible: themeCard.image !== ""
                        source: visible ? FileUrl.of(themeCard.image) : ""
                        sourceSize: Qt.size(480, 300)
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                    }
                    // A bar along the top and a window with text and a button, in the colours of the theme.
                    Rectangle {
                        anchors {
                            left: parent.left
                            right: parent.right
                            top: parent.top
                        }
                        height: 14
                        color: themeCard.colors.base
                        opacity: 0.92
                    }
                    Rectangle {
                        x: parent.width * 0.12
                        y: parent.height * 0.24
                        width: parent.width * 0.62
                        height: parent.height * 0.6
                        radius: Theme.corner(8)
                        color: themeCard.colors.raised
                        border.color: themeCard.colors.border
                        Text {
                            x: 12
                            y: 10
                            text: "Aa"
                            color: themeCard.colors.fg
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(20)
                            font.bold: true
                        }
                        Text {
                            x: 12
                            y: 40
                            text: I18n.tr("theming.previewText")
                            color: themeCard.colors.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                        Row {
                            x: 12
                            anchors.bottom: parent.bottom
                            anchors.bottomMargin: 12
                            spacing: 4
                            Repeater {
                                model: (themeCard.colors.ansi ?? []).slice(1, 7)
                                Rectangle {
                                    required property string modelData
                                    width: 12
                                    height: 12
                                    radius: Theme.corner(6)
                                    color: modelData
                                }
                            }
                        }
                        Rectangle {
                            anchors {
                                right: parent.right
                                bottom: parent.bottom
                                margins: 10
                            }
                            width: 52
                            height: 20
                            radius: Theme.corner(10)
                            color: themeCard.colors.accent
                            Text {
                                anchors.centerIn: parent
                                text: I18n.tr("theming.previewButton")
                                color: themeCard.colors.accentFg
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(10)
                                font.bold: true
                            }
                        }
                    }
                }
            }
        }
    }
}
