import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"

// Radio & music (Super + M), top to bottom: the header (video, close); the content, which is the stations by category
// (from the stations file, services/Radio.qml), the saved items and YouTube search, or with video on the picture of
// what plays (RadioVideo.qml, over the list, which is off meanwhile); the controls of what plays, always there; the
// legend.
Overlay {
    id: root
    panelName: "radio"
    dialog: true
    property string category: "all"
    // The shipped categories have their words; one of your own shows its name.
    readonly property var categoryKeys: ({
            jazz: "radio.categories.jazz",
            dreamwave: "radio.categories.dreamwave",
            lofi: "radio.categories.lofi",
            rnb: "radio.categories.rnb"
        })
    function categoryLabel(name) {
        return categoryKeys[name] ? I18n.tr(categoryKeys[name]) : name.charAt(0).toUpperCase() + name.slice(1);
    }
    readonly property var kindKeys: ({
            radio: "radio.kinds.radio",
            youtube: "radio.kinds.youtube",
            playlist: "radio.kinds.playlist",
            file: "radio.kinds.file"
        })
    function detail(item) {
        return item.subtitle || (kindKeys[item.kind] ? I18n.tr(kindKeys[item.kind]) : "");
    }

    readonly property var combinedStations: {
        const list = Radio.stations.slice();
        for (const item of Radio.saved) {
            const itemUrl = (item.url || "").replace(/\/+$/, "");
            if (!list.some(s => (s.url || "").replace(/\/+$/, "") === itemUrl))
                list.push(item);
        }
        return list;
    }

    readonly property var shown: {
        if (category === "youtube")
            return Radio.results;
        const q = search.text.trim().toLowerCase();
        const base = category === "saved" ? Radio.saved : category === "all" ? combinedStations : category === "radio" ? combinedStations.filter(s => s.kind === "radio") : Radio.stations.filter(s => s.category === category);
        if (!q)
            return base;
        return base.filter(s => (s.title || "").toLowerCase().includes(q) || (s.subtitle || "").toLowerCase().includes(q) || (s.category || "").toLowerCase().includes(q));
    }

    onOpened: {
        Radio.refresh();
        if (!Tablet.active && !Radio.videoOpen)
            search.forceActiveFocus();
    }
    // The picture goes with the panel; the sound, in mpv, goes on.
    onOpenChanged: if (!open)
        Radio.dropVideo()
    function toggleVideo() {
        if (Radio.videoOpen)
            Radio.dropVideo();
        else
            Radio.openVideo();
    }

    function activateItem(item) {
        if (!item)
            return;
        const normRadio = (Radio.url || "").replace(/\/+$/, "");
        const normItem = (item.url || "").replace(/\/+$/, "");
        if (Radio.active && ((normRadio !== "" && normRadio === normItem) || (item.id && Radio.stationId === item.id)))
            Radio.togglePlaying();
        else
            Radio.play(item);
    }

    function runYoutubeSearch() {
        const q = search.text.trim();
        if (!q)
            return;
        category = "youtube";
        Radio.search(q, Radio.searchType);
    }

    Card {
        anchors.centerIn: parent
        width: Math.min(680, parent.width - 32)
        height: Math.min(620, parent.height - Theme.panelClearance)
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Theme.dialogPadding
            spacing: 12

            // Header: the title, video, close.
            PanelHeader {
                title: I18n.tr("radio.title")
                Layout.fillWidth: true
                PanelIconButton {
                    iconName: "monitor"
                    enabled: Radio.hasVideo || Radio.videoOpen
                    highlighted: Radio.videoOpen
                    tone: "state"
                    tooltip: Radio.videoOpen ? I18n.tr("radio.videoOff") : I18n.tr("radio.videoOn")
                    onClicked: root.toggleVideo()
                }
            }

            // Content: the picture, with video on.
            Item {
                visible: Radio.videoOpen
                Layout.fillWidth: true
                Layout.fillHeight: true
                Loader {
                    id: videoLoader
                    anchors.fill: parent
                    active: Radio.videoOpen && Radio.videoStream !== ""
                    source: Qt.resolvedUrl("radio/RadioVideo.qml")
                    onLoaded: {
                        item.start = Radio.videoStart;
                        item.source = Radio.videoStream;
                    }
                    Connections {
                        target: videoLoader.item
                        function onFailed(message) {
                            Radio.error = message;
                            Radio.dropVideo();
                        }
                    }
                    // In step with mpv, which keeps the sound: each status moves the picture along.
                    Connections {
                        target: Radio
                        function onPositionChanged() {
                            videoLoader.item?.follow(Radio.position, Radio.paused);
                        }
                        function onPausedChanged() {
                            videoLoader.item?.follow(Radio.position, Radio.paused);
                        }
                    }
                }
                Text {
                    anchors.centerIn: parent
                    width: parent.width - 32
                    horizontalAlignment: Text.AlignHCenter
                    visible: text !== ""
                    // Without QtMultimedia the loader fails: the radio profile installs it.
                    text: videoLoader.status === Loader.Error ? I18n.tr("radio.videoMissing") : Radio.videoLoading || (videoLoader.item && videoLoader.item.loading) ? I18n.tr("radio.videoLoading") : ""
                    wrapMode: Text.Wrap
                    color: videoLoader.status === Loader.Error ? Theme.danger : Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(13)
                }
            }

            // Content: search and the list, with video off.
            ColumnLayout {
                visible: !Radio.videoOpen
                enabled: !Radio.videoOpen
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    InputField {
                        id: search
                        Layout.fillWidth: true
                        placeholderText: I18n.tr("radio.searchPlaceholder")
                        onTextChanged: stationsList.currentIndex = 0
                        Keys.onDownPressed: stationsList.currentIndex = Math.min(stationsList.count - 1, stationsList.currentIndex + 1)
                        Keys.onUpPressed: stationsList.currentIndex = Math.max(0, stationsList.currentIndex - 1)
                        onAccepted: {
                            const q = search.text.trim();
                            const current = root.shown[stationsList.currentIndex] || (root.shown.length > 0 ? root.shown[0] : null);
                            if (root.shown.length === 0 && q !== "") {
                                root.runYoutubeSearch();
                            } else if (root.category === "youtube" && q !== "" && q !== Radio.lastQuery) {
                                root.runYoutubeSearch();
                            } else if (current) {
                                root.activateItem(current);
                            } else if (q !== "") {
                                root.runYoutubeSearch();
                            }
                        }
                    }
                    ActionButton {
                        iconName: "zoom"
                        text: I18n.tr("radio.searchYoutube")
                        enabled: !Radio.searching && search.text.trim().length > 0
                        onClicked: root.runYoutubeSearch()
                    }
                }

                ChoiceChips {
                    Layout.fillWidth: true
                    current: root.category
                    options: [
                        {
                            name: "all",
                            label: I18n.tr("radio.categories.all")
                        },
                        {
                            name: "radio",
                            label: I18n.tr("radio.categories.webRadio")
                        }
                    ].concat(Radio.categories.map(name => ({
                                name: name,
                                label: root.categoryLabel(name)
                            })), [
                        {
                            name: "saved",
                            label: I18n.tr("radio.categories.saved")
                        },
                        {
                            name: "youtube",
                            label: I18n.tr("radio.categories.youtube")
                        }
                    ])
                    onChosen: name => {
                        root.category = name;
                        stationsList.currentIndex = 0;
                        if (name === "youtube" && Radio.results.length === 0 && search.text.trim() !== "")
                            root.runYoutubeSearch();
                    }
                }

                ChoiceChips {
                    visible: root.category === "youtube"
                    Layout.fillWidth: true
                    current: Radio.searchType
                    options: [
                        {
                            name: "all",
                            label: I18n.tr("radio.searchModes.all")
                        },
                        {
                            name: "playlist",
                            label: I18n.tr("radio.searchModes.playlists")
                        },
                        {
                            name: "video",
                            label: I18n.tr("radio.searchModes.videos")
                        }
                    ]
                    onChosen: name => {
                        Radio.searchType = name;
                        const q = search.text.trim() || Radio.lastQuery;
                        if (q)
                            Radio.search(q, name);
                    }
                }

                ListView {
                    id: stationsList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 4
                    model: ScriptModel {
                        values: root.shown
                        objectProp: "url"
                    }
                    delegate: RowLayout {
                        id: delegateRow
                        required property var modelData
                        required property int index
                        width: stationsList.width
                        spacing: 6
                        readonly property string normRadioUrl: (Radio.url || "").replace(/\/+$/, "")
                        readonly property string normItemUrl: (modelData.url || "").replace(/\/+$/, "")
                        readonly property bool isCurrent: Radio.active && ((normRadioUrl !== "" && normRadioUrl === normItemUrl) || (modelData.id && Radio.stationId === modelData.id))
                        readonly property bool savedEntry: Boolean(modelData.saved) || Radio.isSaved(modelData.url)
                        ActionButton {
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            implicitHeight: 48
                            alignLeft: true
                            highlighted: stationsList.currentIndex === index || delegateRow.isCurrent
                            tone: delegateRow.isCurrent ? "state" : "cursor"
                            iconName: delegateRow.isCurrent ? (Radio.playing ? "volume-high" : "pause") : modelData.kind === "radio" ? "hotspot" : modelData.kind === "playlist" ? "folder" : "play"
                            text: root.detail(modelData) ? modelData.title + "  —  " + root.detail(modelData) : modelData.title
                            onClicked: root.activateItem(modelData)
                        }
                        PanelIconButton {
                            visible: root.category === "youtube" || root.category === "saved" || delegateRow.savedEntry
                            iconName: delegateRow.savedEntry ? "trash" : "pin"
                            tooltip: delegateRow.savedEntry ? I18n.tr("radio.removeSaved") : I18n.tr("radio.saveItem")
                            onClicked: {
                                if (delegateRow.savedEntry)
                                    Radio.removeItem(modelData.url);
                                else
                                    Radio.saveItem(modelData);
                            }
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}
                    Text {
                        anchors.centerIn: parent
                        visible: stationsList.count === 0
                        text: Radio.searching ? I18n.tr("radio.searching") : root.category === "youtube" ? I18n.tr("radio.youtubeEmpty") : root.category === "saved" ? I18n.tr("radio.savedEmpty") : I18n.tr("radio.empty")
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                    }
                }
            }

            // The controls of what plays, always there.
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: controlsRow.implicitHeight + 16
                radius: Theme.corner(12)
                color: Theme.tile
                RowLayout {
                    id: controlsRow
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10
                    Icon {
                        name: Radio.kind === "radio" ? "hotspot" : "volume-high"
                        color: Radio.active ? Theme.accent : Theme.muted
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        spacing: 2
                        Text {
                            Layout.fillWidth: true
                            text: Radio.active ? Radio.title || Radio.stationTitle : I18n.tr("radio.nothingPlaying")
                            color: Radio.active ? Theme.text : Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                            font.weight: Radio.active ? Font.DemiBold : Font.Normal
                            elide: Text.ElideRight
                            textFormat: Text.PlainText
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: Radio.active && text !== ""
                            text: Radio.stationTitle && Radio.stationTitle !== Radio.title ? Radio.stationTitle + (Radio.subtitle ? " · " + Radio.subtitle : "") : Radio.subtitle
                            color: Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                            elide: Text.ElideRight
                            textFormat: Text.PlainText
                        }
                    }
                    PanelIconButton {
                        iconName: "previous"
                        enabled: Radio.active && Radio.kind !== "radio"
                        tooltip: I18n.tr("media.previous")
                        onClicked: Radio.previous()
                    }
                    PanelIconButton {
                        iconName: Radio.playing ? "pause" : "play"
                        enabled: Radio.active
                        tooltip: Radio.playing ? I18n.tr("media.pause") : I18n.tr("media.play")
                        onClicked: Radio.togglePlaying()
                    }
                    PanelIconButton {
                        iconName: "next"
                        enabled: Radio.active && Radio.kind !== "radio"
                        tooltip: I18n.tr("media.next")
                        onClicked: Radio.next()
                    }
                    PanelIconButton {
                        iconName: "stop"
                        enabled: Radio.active
                        tooltip: I18n.tr("media.stop")
                        onClicked: Radio.stop()
                    }
                }
            }

            // Footer: the legend, or what went wrong.
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: Radio.error || (Radio.searching ? I18n.tr("radio.searching") : I18n.tr("radio.hint"))
                color: Radio.error ? Theme.danger : Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
                textFormat: Text.PlainText
            }
        }
    }
}
