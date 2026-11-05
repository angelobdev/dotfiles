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
    // "glass" is a page of the Theme tab, reached from the card of a theme with liquid glass.
    // "store" is a page of the Icons tab: the KDE Store, for cursor or icon themes (Store.kind).
    readonly property var tabs: ["theme", "wallpaper", "font", "icons", "glass", "store"]
    readonly property var cycle: ["theme", "wallpaper", "font", "icons"]
    readonly property Item sansList: sansProxy.list ?? themeGrid
    function fileUrl(path) {
        return "file://" + path.split("/").map(encodeURIComponent).join("/");
    }
    function showTab(name) {
        tab = name;
        if (name === "wallpaper")
            Theming.makeThumbs();
        Qt.callLater(() => {
            const view = [themeGrid, wallpaperGrid, sansList, iconList, glassBack, storeSearch][tabs.indexOf(name)];
            view.forceActiveFocus();
        });
    }
    function openStore(kind) {
        if (Store.kind !== kind || Store.items.length === 0)
            Store.search(kind, "");
        Store.refreshInstalled();
        showTab("store");
    }
    function cycleTab(step) {
        const from = Math.max(0, cycle.indexOf(tab === "glass" ? "theme" : tab === "store" ? "icons" : tab));
        showTab(cycle[(from + step + cycle.length) % cycle.length]);
    }
    // Labels of the glass options theme.py offers (GLASS_TUNING); an unknown one shows its own name.
    function glassLabel(option) {
        const labels = {
            blur_strength: I18n.tr("theming.glassOptions.blurStrength"),
            refraction_strength: I18n.tr("theming.glassOptions.refractionStrength"),
            chromatic_aberration: I18n.tr("theming.glassOptions.chromaticAberration"),
            edge_thickness_px: I18n.tr("theming.glassOptions.edgeThicknessPx"),
            edge_height: I18n.tr("theming.glassOptions.edgeHeight"),
            fresnel_reflection: I18n.tr("theming.glassOptions.fresnelReflection"),
            specular_strength: I18n.tr("theming.glassOptions.specularStrength"),
            bevel_strength: I18n.tr("theming.glassOptions.bevelStrength"),
            noise_strength: I18n.tr("theming.glassOptions.noiseStrength")
        };
        return labels[option] ?? option;
    }
    function glassText(entry, value) {
        return entry.step >= 1 ? String(Math.round(value)) + " px" : Number(value).toFixed(2);
    }
    // A theme without liquid glass (another theme chosen meanwhile) has no glass page.
    Connections {
        target: Theming
        function onGlassChanged() {
            if (root.tab === "glass" && !Theming.glass)
                root.showTab("theme");
        }
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
                    current: root.tab === "glass" ? "theme" : root.tab === "store" ? "icons" : root.tab
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
                                            source: visible ? root.fileUrl(Theming.wallpaperThumb) : ""
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
                                                text: "Lorem ipsum"
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
                                                text: "OK"
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
                                            onClicked: root.showTab("glass")
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
                            font.pixelSize: Theme.textSize(12)
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
                            font.pixelSize: Theme.textSize(13)
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
                                    font.pixelSize: Theme.textSize(12)
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
                                        implicitHeight: Theme.hit(36)
                                        alignLeft: true
                                        text: modelData === "" ? I18n.tr("theming.themeDefaultNamed", [fontColumn.themeFamily]) : modelData
                                        font.family: modelData === "" ? fontColumn.themeFamily : modelData
                                        font.pixelSize: Theme.textSize(14)
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
                            font.pixelSize: Theme.textSize(12)
                        }
                        ChoiceCombo {
                            Accessible.name: I18n.tr("theming.size")
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
                    // The shell's own text (bar, panels, notifications), applied at once; apps follow the size above.
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Text {
                            text: I18n.tr("theming.shellText")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(12)
                        }
                        ChoiceChips {
                            Accessible.name: I18n.tr("theming.shellText")
                            options: [1, 1.15, 1.3, 1.5].map(scale => ({
                                        name: String(scale),
                                        label: Math.round(scale * 100) + "%"
                                    }))
                            current: String(Theme.textScale)
                            onChosen: name => Theming.setTextScale(Number(name))
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: previewColumn.implicitHeight + 20
                        radius: Theme.corner(12)
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
                // Icons: each pack with its own sample icons, and where the shell glyphs come from. The cursor
                // theme and size come first.
                ColumnLayout {
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Text {
                            text: I18n.tr("theming.cursor")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(12)
                        }
                        ChoiceCombo {
                            Accessible.name: I18n.tr("theming.cursor")
                            options: [
                                {
                                    name: "",
                                    label: I18n.tr("theming.themeDefaultNamed", [Theming.cursors.theme ?? ""])
                                }
                            ].concat((Theming.cursors.themes ?? []).map(t => ({
                                        name: t.id,
                                        label: t.download ? I18n.tr("theming.cursorDownload", [t.name]) : t.name
                                    })))
                            current: Theming.cursors.chosen?.theme ?? ""
                            onChosen: name => Theming.setCursor(name, undefined)
                        }
                        ChoiceChips {
                            Accessible.name: I18n.tr("theming.cursorSize")
                            options: (Theming.cursors.sizes ?? []).map(size => ({
                                        name: String(size),
                                        label: String(size)
                                    }))
                            current: String(Theming.cursors.size ?? 24)
                            onChosen: name => Theming.setCursor(undefined, Number(name))
                        }
                        Item {
                            Layout.fillWidth: true
                        }
                        ActionButton {
                            text: I18n.tr("store.getMore")
                            onClicked: root.openStore("cursors")
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Text {
                            text: I18n.tr("theming.shellIcons")
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(12)
                        }
                        ChoiceCombo {
                            Accessible.name: I18n.tr("theming.shellIcons")
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
                            text: I18n.tr("store.getMore")
                            onClicked: root.openStore("icons")
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
                // Glass: the Hyprglass options of the current theme, each saved as it is released.
                ColumnLayout {
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        ActionButton {
                            id: glassBack
                            iconName: "arrow-left"
                            text: I18n.tr("theming.glassBack")
                            onClicked: root.showTab("theme")
                        }
                        Text {
                            Layout.fillWidth: true
                            text: I18n.tr("theming.glassTitle", [Theming.themes.find(t => t.id === Theming.current)?.name ?? Theming.current])
                            textFormat: Text.PlainText
                            elide: Text.ElideRight
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(14)
                            font.bold: true
                        }
                        ActionButton {
                            text: I18n.tr("theming.glassReset")
                            enabled: (Theming.glass ?? []).some(entry => entry.value !== entry.default)
                            onClicked: Theming.resetGlass()
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("theming.glassHint")
                        wrapMode: Text.Wrap
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                    }
                    Flickable {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentHeight: glassRows.implicitHeight
                        boundsBehavior: Flickable.StopAtBounds
                        ColumnLayout {
                            id: glassRows
                            width: parent.width
                            spacing: 4
                            Repeater {
                                // By position, so the rows (and the focused slider) survive each refresh.
                                model: (Theming.glass ?? []).length
                                RowLayout {
                                    id: glassRow
                                    required property int index
                                    readonly property var entry: Theming.glass?.[index] ?? {
                                        option: "",
                                        value: 0,
                                        default: 0,
                                        min: 0,
                                        max: 1,
                                        step: 0.05
                                    }
                                    Layout.fillWidth: true
                                    spacing: 12
                                    Text {
                                        Layout.preferredWidth: 200
                                        text: root.glassLabel(glassRow.entry.option)
                                        elide: Text.ElideRight
                                        color: Theme.text
                                        font.family: Theme.font
                                        font.pixelSize: Theme.textSize(13)
                                    }
                                    ControlSlider {
                                        id: glassSlider
                                        // From the first move until the saved value comes back, the slider keeps
                                        // its own value instead of snapping back to the old one.
                                        property bool holding: false
                                        Layout.fillWidth: true
                                        from: glassRow.entry.min
                                        to: glassRow.entry.max
                                        stepSize: glassRow.entry.step
                                        snapMode: Slider.SnapAlways
                                        Accessible.name: root.glassLabel(glassRow.entry.option)
                                        Binding on value {
                                            when: !glassSlider.pressed && !glassSlider.holding
                                            value: glassRow.entry.value
                                        }
                                        function commit() {
                                            glassCommit.stop();
                                            if (Math.abs(value - glassRow.entry.value) > glassRow.entry.step / 2)
                                                Theming.setGlass(glassRow.entry.option, value);
                                            else
                                                holding = false;
                                        }
                                        // Each change reloads Hyprland: a drag commits on release, arrow keys after a pause.
                                        onMoved: {
                                            holding = true;
                                            if (!pressed)
                                                glassCommit.restart();
                                        }
                                        onPressedChanged: if (!pressed && holding)
                                            commit()
                                        Connections {
                                            target: glassRow
                                            function onEntryChanged() {
                                                if (!glassSlider.pressed && !glassCommit.running)
                                                    glassSlider.holding = false;
                                            }
                                        }
                                        Timer {
                                            id: glassCommit
                                            interval: 450
                                            onTriggered: glassSlider.commit()
                                        }
                                    }
                                    Text {
                                        Layout.preferredWidth: 64
                                        horizontalAlignment: Text.AlignRight
                                        text: root.glassText(glassRow.entry, glassSlider.value)
                                        color: Math.abs(glassSlider.value - glassRow.entry.default) > glassRow.entry.step / 2 ? Theme.accent : Theme.muted
                                        font.family: Theme.font
                                        font.pixelSize: Theme.textSize(12)
                                        HoverHandler {
                                            id: valueHover
                                        }
                                        ToolTip.visible: valueHover.hovered
                                        ToolTip.text: I18n.tr("theming.glassDefault", [root.glassText(glassRow.entry, glassRow.entry.default)])
                                    }
                                }
                            }
                        }
                        ScrollBar.vertical: ScrollBar {}
                    }
                }
                // Store: cursor or icon themes from store.kde.org, most downloaded first; each card installs one of
                // its files, and removes what it installed.
                ColumnLayout {
                    spacing: 10
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        ActionButton {
                            iconName: "arrow-left"
                            text: I18n.tr("theming.tabs.icons")
                            onClicked: root.showTab("icons")
                        }
                        InputField {
                            id: storeSearch
                            Layout.fillWidth: true
                            placeholderText: Store.kind === "cursors" ? I18n.tr("store.searchCursors") : I18n.tr("store.searchIcons")
                            onAccepted: Store.search(Store.kind, text)
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: Store.error !== "" || Store.message !== ""
                        text: Store.error || Store.message
                        color: Store.error !== "" ? Theme.danger : Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                        wrapMode: Text.Wrap
                    }
                    GridView {
                        id: storeGrid
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 260)))
                        cellHeight: Theme.hit(292)
                        model: Store.items
                        onAtYEndChanged: if (atYEnd && count > 0)
                            Store.next()
                        delegate: Item {
                            id: storeCard
                            required property var modelData
                            readonly property var folders: Store.foldersOf(modelData.id)
                            property int file: modelData.files[0]?.index ?? 1
                            width: storeGrid.cellWidth
                            height: storeGrid.cellHeight
                            Rectangle {
                                anchors.fill: parent
                                anchors.margins: 5
                                radius: Theme.corner(12)
                                color: Theme.tile
                                clip: true
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 4
                                    Image {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 110
                                        source: storeCard.modelData.preview
                                        fillMode: Image.PreserveAspectFit
                                        asynchronous: true
                                        sourceSize: Qt.size(440, 220)
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: storeCard.modelData.name
                                        color: Theme.text
                                        elide: Text.ElideRight
                                        font.family: Theme.font
                                        font.pixelSize: Theme.textSize(13)
                                        font.bold: true
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        text: I18n.tr("store.by", [storeCard.modelData.author]) + " · " + I18n.tr("store.downloads", [storeCard.modelData.downloads.toLocaleString(I18n.locale, "f", 0)])
                                        color: Theme.muted
                                        elide: Text.ElideRight
                                        font.family: Theme.font
                                        font.pixelSize: Theme.textSize(11)
                                    }
                                    Item {
                                        Layout.fillHeight: true
                                    }
                                    // The file on its own row (names are long), the buttons below it on the right.
                                    ChoiceCombo {
                                        Layout.fillWidth: true
                                        // Narrower than its longest file name: the shown name ends with an ellipsis.
                                        Layout.minimumWidth: 0
                                        Layout.maximumWidth: parent.width
                                        visible: storeCard.modelData.files.length > 1
                                        Accessible.name: storeCard.modelData.name
                                        options: storeCard.modelData.files.map(f => ({
                                                    name: String(f.index),
                                                    label: f.name
                                                }))
                                        current: String(storeCard.file)
                                        onChosen: name => storeCard.file = Number(name)
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 6
                                        Item {
                                            Layout.fillWidth: true
                                        }
                                        ActionButton {
                                            visible: storeCard.folders.length > 0
                                            text: I18n.tr("store.remove")
                                            destructive: true
                                            onClicked: storeCard.folders.forEach(folder => Store.remove(folder))
                                        }
                                        ActionButton {
                                            text: Store.installing === storeCard.modelData.id ? I18n.tr("store.installing") : I18n.tr("store.install")
                                            enabled: Store.installing === 0 && storeCard.modelData.files.length > 0
                                            highlighted: true
                                            onClicked: Store.install(storeCard.modelData.id, storeCard.file)
                                        }
                                    }
                                }
                            }
                        }
                        ScrollBar.vertical: ScrollBar {}
                        Text {
                            anchors.centerIn: parent
                            visible: storeGrid.count === 0
                            text: Store.searching ? I18n.tr("store.loading") : I18n.tr("store.empty")
                            color: Theme.muted
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("store.hint")
                        color: Theme.muted
                        wrapMode: Text.Wrap
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(11)
                    }
                }
            }
            // Fonts and icons reach the shell after a restart; the rest of the desktop has them already.
            Rectangle {
                Layout.fillWidth: true
                visible: Theming.restartTab !== ""
                implicitHeight: restartRow.implicitHeight + 16
                radius: Theme.corner(12)
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
                        font.pixelSize: Theme.textSize(12)
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
                font.pixelSize: Theme.textSize(12)
            }
            Text {
                // Wraps instead of widening the layout past the panel (wide theme fonts, long translations).
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: Theming.busy ? I18n.tr("theming.working") : Tablet.active ? "" : I18n.tr("theming.navigationHint")
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
            }
        }
    }
    // One option of the panel: its label and a drop-down of its choices.
    component Setting: RowLayout {
        id: setting
        property string label: ""
        property alias options: combo.options
        property alias current: combo.current
        signal chosen(string name)
        spacing: 8
        Text {
            text: setting.label
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        ChoiceCombo {
            id: combo
            Accessible.name: setting.label
            onChosen: name => setting.chosen(name)
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
                implicitHeight: Theme.hit(34)
                placeholderText: entry.placeholder
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
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
            font.pixelSize: Theme.textSize(11)
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
