import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"

Overlay {
    id: root
    panelName: "theming"
    dialog: true
    property string tab: "theme"
    readonly property var tabs: ["theme", "wallpaper", "font", "icons"]
    readonly property Item sansList: sansProxy.list ?? themeGrid
    function fileUrl(path) {
        return "file://" + path.split("/").map(encodeURIComponent).join("/");
    }
    function showTab(name) {
        tab = name;
        if (name === "wallpaper")
            Theming.makeThumbs();
        Qt.callLater(() => {
            const view = [themeGrid, wallpaperGrid, sansList, iconList][tabs.indexOf(name)];
            view.forceActiveFocus();
        });
    }
    function cycleTab(step) {
        showTab(tabs[(tabs.indexOf(tab) + step + tabs.length) % tabs.length]);
    }
    onOpened: {
        Theming.refresh();
        showTab(tab);
    }
    // Ctrl+Tab and Ctrl+Shift+Tab switch tabs from any page.
    Shortcut {
        enabled: root.open
        sequences: ["Ctrl+Tab", "Ctrl+PgDown"]
        onActivated: root.cycleTab(1)
    }
    Shortcut {
        enabled: root.open
        sequences: ["Ctrl+Shift+Tab", "Ctrl+PgUp"]
        onActivated: root.cycleTab(-1)
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(980, parent.width - 48)
        height: Math.min(700, parent.height - 96)
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 14
            RowLayout {
                Layout.fillWidth: true
                Heading {
                    Layout.fillWidth: true
                    text: I18n.tr("theming.title")
                }
                ChoiceChips {
                    Layout.fillWidth: false
                    options: [
                        {
                            name: "theme",
                            label: I18n.tr("theming.tabs.theme")
                        },
                        {
                            name: "wallpaper",
                            label: I18n.tr("theming.tabs.wallpaper")
                        },
                        {
                            name: "font",
                            label: I18n.tr("theming.tabs.font")
                        },
                        {
                            name: "icons",
                            label: I18n.tr("theming.tabs.icons")
                        }
                    ]
                    current: root.tab
                    onChosen: name => root.showTab(name)
                }
            }
            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: root.tabs.indexOf(root.tab)
                // Theme: a card per theme with a small mock-up of its surfaces and accent, and its colours.
                ColumnLayout {
                    spacing: 10
                    RowLayout {
                        spacing: 10
                        Text {
                            text: I18n.tr("theming.bar")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: 12
                        }
                        ChoiceChips {
                            Layout.fillWidth: false
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
                        Text {
                            Layout.fillWidth: true
                            text: I18n.tr("theming.barHint")
                            elide: Text.ElideRight
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: 11
                        }
                    }
                    GridView {
                        id: themeGrid
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 230)))
                        cellHeight: 190
                        model: Theming.themes
                        keyNavigationEnabled: true
                        Keys.onReturnPressed: Theming.setTheme(Theming.themes[currentIndex]?.id ?? "")
                        Keys.onEnterPressed: Theming.setTheme(Theming.themes[currentIndex]?.id ?? "")
                        delegate: Item {
                            id: themeCell
                            required property var modelData
                            required property int index
                            readonly property var preview: modelData.preview
                            readonly property bool active: modelData.id === Theming.current
                            width: themeGrid.cellWidth
                            height: themeGrid.cellHeight
                            Rectangle {
                                anchors {
                                    fill: parent
                                    margins: 6
                                }
                                radius: 14
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
                                        radius: 8
                                        color: themeCell.preview.bg
                                        Rectangle {
                                            anchors {
                                                left: parent.left
                                                right: parent.right
                                                top: parent.top
                                            }
                                            height: 12
                                            radius: 8
                                            color: themeCell.preview.base
                                        }
                                        Rectangle {
                                            x: 12
                                            y: 22
                                            width: parent.width * 0.55
                                            height: parent.height - 34
                                            radius: 6
                                            color: themeCell.preview.raised
                                            border.color: themeCell.preview.border
                                            Text {
                                                x: 8
                                                y: 6
                                                text: "Aa"
                                                color: themeCell.preview.fg
                                                font.family: Theme.font
                                                font.pixelSize: 15
                                                font.bold: true
                                            }
                                            Text {
                                                x: 8
                                                y: 28
                                                text: "Lorem ipsum"
                                                color: themeCell.preview.muted
                                                font.family: Theme.font
                                                font.pixelSize: 10
                                            }
                                        }
                                        Rectangle {
                                            anchors {
                                                right: parent.right
                                                bottom: parent.bottom
                                                margins: 12
                                            }
                                            width: 46
                                            height: 18
                                            radius: 9
                                            color: themeCell.preview.accent
                                            Text {
                                                anchors.centerIn: parent
                                                text: "OK"
                                                color: themeCell.preview.accentFg
                                                font.family: Theme.font
                                                font.pixelSize: 10
                                                font.bold: true
                                            }
                                        }
                                    }
                                    Row {
                                        spacing: 3
                                        Repeater {
                                            model: themeCell.preview.ansi.slice(1, 7).concat(themeCell.preview.ansi.slice(9, 11))
                                            Rectangle {
                                                required property string modelData
                                                width: 14
                                                height: 14
                                                radius: 7
                                                color: modelData
                                            }
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Text {
                                            Layout.fillWidth: true
                                            text: themeCell.modelData.name
                                            textFormat: Text.PlainText
                                            elide: Text.ElideRight
                                            color: Theme.text
                                            font.family: Theme.font
                                            font.pixelSize: 13
                                            font.bold: themeCell.active
                                        }
                                        Text {
                                            visible: themeCell.active
                                            text: I18n.tr("theming.current")
                                            color: Theme.accent
                                            font.family: Theme.font
                                            font.pixelSize: 11
                                        }
                                    }
                                }
                            }
                            MouseArea {
                                id: themeMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    themeGrid.currentIndex = themeCell.index;
                                    Theming.setTheme(themeCell.modelData.id);
                                }
                            }
                        }
                        ScrollBar.vertical: ScrollBar {}
                    }
                }
                // Wallpaper: the set of the current theme, then "Custom…" for any image.
                ColumnLayout {
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        visible: Theming.missingWallpapers
                        Text {
                            Layout.fillWidth: true
                            text: Theming.downloading ? I18n.tr("theming.downloading") : I18n.tr("theming.notDownloaded")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: 12
                        }
                        ActionButton {
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
                        model: Theming.wallpaperItems
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
                                radius: 12
                                color: Theme.tile
                                clip: true
                                Image {
                                    anchors {
                                        fill: parent
                                        margins: 3
                                    }
                                    visible: wallCell.modelData.thumb !== ""
                                    // Cached JPEG thumbnails: Qt here cannot decode WebP, and full-size 8K images would be slow.
                                    source: visible ? root.fileUrl(wallCell.modelData.thumb) : ""
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
                                        font.pixelSize: 12
                                    }
                                }
                            }
                            // Outline drawn on top so the thumbnail cannot cover it.
                            Rectangle {
                                anchors.fill: frame
                                radius: 12
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
                // Font: interface and monospace families, each shown in itself, and the size.
                ColumnLayout {
                    spacing: 12
                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: I18n.tr("theming.unified")
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: 13
                        }
                        ControlSwitch {
                            checked: Theming.fonts.chosen?.unified === true
                            onToggled: Theming.setUnified(checked)
                            Accessible.name: I18n.tr("theming.unified")
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 16
                        Repeater {
                            model: [
                                {
                                    kind: "sans",
                                    label: I18n.tr("theming.interfaceFont")
                                },
                                {
                                    kind: "mono",
                                    label: I18n.tr("theming.monospaceFont")
                                }
                            ]
                            ColumnLayout {
                                id: fontColumn
                                required property var modelData
                                required property int index
                                readonly property string chosen: Theming.fonts.chosen?.[modelData.kind] ?? ""
                                readonly property string themeFamily: Theming.fonts.theme?.[modelData.kind] ?? ""
                                // With one font everywhere the interface list has nothing to choose.
                                readonly property bool usable: modelData.kind === "mono" || Theming.fonts.chosen?.unified !== true
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                enabled: usable
                                opacity: usable ? 1 : 0.45
                                spacing: 6
                                Text {
                                    text: fontColumn.modelData.label
                                    color: Theme.muted
                                    font.family: Theme.font
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                                ListView {
                                    id: fontList
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    spacing: 2
                                    model: [""].concat(Theming.fonts[fontColumn.modelData.kind] ?? [])
                                    keyNavigationEnabled: true
                                    highlightMoveDuration: Theme.motionNormal
                                    Keys.onReturnPressed: Theming.setFont(fontColumn.modelData.kind, model[currentIndex] ?? "")
                                    Keys.onEnterPressed: Theming.setFont(fontColumn.modelData.kind, model[currentIndex] ?? "")
                                    Keys.onRightPressed: if (fontColumn.index === 0)
                                        monoProxy.list?.forceActiveFocus()
                                    Keys.onLeftPressed: if (fontColumn.index === 1)
                                        sansProxy.list?.forceActiveFocus()
                                    delegate: ActionButton {
                                        id: fontRow
                                        required property string modelData
                                        required property int index
                                        readonly property bool selected: modelData === fontColumn.chosen
                                        width: fontList.width
                                        implicitHeight: 36
                                        alignLeft: true
                                        text: modelData === "" ? I18n.tr("theming.themeDefaultNamed", [fontColumn.themeFamily]) : modelData
                                        font.family: modelData === "" ? fontColumn.themeFamily : modelData
                                        font.pixelSize: 14
                                        highlighted: selected
                                        onClicked: {
                                            fontList.currentIndex = index;
                                            Theming.setFont(fontColumn.modelData.kind, modelData);
                                        }
                                        Component.onCompleted: if (selected)
                                            fontList.currentIndex = index
                                    }
                                    Component.onCompleted: {
                                        if (fontColumn.index === 0)
                                            sansProxy.list = fontList;
                                        else
                                            monoProxy.list = fontList;
                                    }
                                    ScrollBar.vertical: ScrollBar {}
                                }
                                CustomEntry {
                                    kind: fontColumn.modelData.kind
                                    placeholder: I18n.tr("theming.otherFont")
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Text {
                            text: I18n.tr("theming.size")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: 12
                        }
                        ChoiceChips {
                            options: [9, 10, 11, 12, 13].map(size => ({
                                        name: String(size),
                                        label: String(size)
                                    }))
                            current: String(Theming.fonts.effective?.size ?? "")
                            onChosen: name => Theming.setSize(Number(name))
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        ActionButton {
                            text: I18n.tr("theming.openFonts")
                            onClicked: Theming.openFolder("fonts")
                        }
                        ActionButton {
                            text: I18n.tr("theming.rescan")
                            onClicked: Theming.rescan("fonts")
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: previewColumn.implicitHeight + 20
                        radius: 12
                        color: Theme.background
                        ColumnLayout {
                            id: previewColumn
                            anchors {
                                fill: parent
                                margins: 10
                            }
                            spacing: 4
                            Text {
                                Layout.fillWidth: true
                                text: I18n.tr("theming.previewSans")
                                elide: Text.ElideRight
                                color: Theme.text
                                font.family: Theming.fonts.effective?.sans ?? Theme.font
                                font.pixelSize: Math.round((Theming.fonts.effective?.size ?? 10) * 1.6)
                            }
                            Text {
                                Layout.fillWidth: true
                                text: "0O 1lI {} [] => fn main() { println!(\"ciao\"); }"
                                textFormat: Text.PlainText
                                elide: Text.ElideRight
                                color: Theme.muted
                                font.family: Theming.fonts.effective?.mono ?? "monospace"
                                font.pixelSize: Math.round((Theming.fonts.effective?.size ?? 10) * 1.5)
                            }
                        }
                    }
                }
                // Icons: each pack with its own sample icons, and where the shell glyphs come from.
                ColumnLayout {
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Text {
                            text: I18n.tr("theming.shellIcons")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: 12
                        }
                        ChoiceChips {
                            Layout.fillWidth: false
                            options: [
                                {
                                    name: "desktop",
                                    label: I18n.tr("theming.shellIconsDesktop")
                                },
                                {
                                    name: "pack",
                                    label: I18n.tr("theming.shellIconsPack")
                                }
                            ]
                            current: Theme.iconSource
                            onChosen: name => Theming.setShellIcons(name)
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        ActionButton {
                            text: I18n.tr("theming.openIcons")
                            onClicked: Theming.openFolder("icons")
                        }
                        ActionButton {
                            text: I18n.tr("theming.rescan")
                            onClicked: Theming.rescan("icons")
                        }
                    }
                    ListView {
                        id: iconList
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 3
                        model: [
                            {
                                id: "",
                                name: I18n.tr("theming.themeDefaultNamed", [Theming.icons.theme ?? ""]),
                                samples: (Theming.icons.themes.find(t => t.id === Theming.icons.theme)?.samples) ?? []
                            }
                        ].concat(Theming.icons.themes)
                        keyNavigationEnabled: true
                        highlightMoveDuration: Theme.motionNormal
                        Keys.onReturnPressed: Theming.setIcons(model[currentIndex]?.id ?? "")
                        Keys.onEnterPressed: Theming.setIcons(model[currentIndex]?.id ?? "")
                        delegate: ActionButton {
                            id: iconRow
                            required property var modelData
                            required property int index
                            readonly property bool selected: (modelData.id || null) === (Theming.icons.chosen ?? null)
                            width: iconList.width
                            implicitHeight: 52
                            alignLeft: true
                            highlighted: selected
                            text: modelData.name
                            rightPadding: 12 + samples.width
                            onClicked: {
                                iconList.currentIndex = index;
                                Theming.setIcons(modelData.id);
                            }
                            Component.onCompleted: if (selected)
                                iconList.currentIndex = index
                            Row {
                                id: samples
                                anchors {
                                    right: parent.right
                                    rightMargin: 14
                                    verticalCenter: parent.verticalCenter
                                }
                                spacing: 10
                                Repeater {
                                    model: iconRow.modelData.samples
                                    Image {
                                        required property string modelData
                                        width: 28
                                        height: 28
                                        source: modelData ? root.fileUrl(modelData) : ""
                                        sourceSize: Qt.size(56, 56)
                                        fillMode: Image.PreserveAspectFit
                                        asynchronous: true
                                    }
                                }
                            }
                        }
                        ScrollBar.vertical: ScrollBar {}
                    }
                    CustomEntry {
                        kind: "icons"
                        placeholder: I18n.tr("theming.otherIcons")
                    }
                }
            }
            // Fonts and icons reach the shell after a restart; the rest of the desktop has them already.
            Rectangle {
                Layout.fillWidth: true
                visible: Theming.restartTab !== ""
                implicitHeight: restartRow.implicitHeight + 16
                radius: 12
                color: Theme.tile
                RowLayout {
                    id: restartRow
                    anchors {
                        fill: parent
                        margins: 8
                        leftMargin: 14
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("theming.restartHint")
                        wrapMode: Text.Wrap
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: 12
                    }
                    ActionButton {
                        text: I18n.tr("theming.restart")
                        onClicked: Theming.restartShell()
                    }
                }
            }
            Text {
                Layout.fillWidth: true
                visible: Theming.error !== ""
                text: Theming.error
                textFormat: Text.PlainText
                wrapMode: Text.Wrap
                color: Theme.danger
                font.pixelSize: 12
            }
            Text {
                text: Theming.busy ? I18n.tr("theming.working") : I18n.tr("theming.navigationHint")
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: 12
            }
        }
    }
    // A family or icon theme installed by hand, typed in and checked before it applies.
    component CustomEntry: ColumnLayout {
        id: entry
        required property string kind
        required property string placeholder
        Layout.fillWidth: true
        spacing: 4
        RowLayout {
            Layout.fillWidth: true
            InputField {
                id: field
                Layout.fillWidth: true
                implicitHeight: 34
                placeholderText: entry.placeholder
                font.family: Theme.font
                font.pixelSize: 12
                onAccepted: Theming.applyCustom(entry.kind, text)
            }
            ActionButton {
                text: I18n.tr("theming.useCustom")
                enabled: field.text.trim() !== ""
                onClicked: Theming.applyCustom(entry.kind, field.text)
            }
        }
        Text {
            Layout.fillWidth: true
            visible: Theming.customKind === entry.kind && Theming.customError !== ""
            text: Theming.customError
            textFormat: Text.PlainText
            wrapMode: Text.Wrap
            color: Theme.danger
            font.family: Theme.font
            font.pixelSize: 11
        }
    }
    // The two font lists are created by a Repeater; these let arrow keys move between them.
    QtObject {
        id: sansProxy
        property var list: null
    }
    QtObject {
        id: monoProxy
        property var list: null
    }
}
