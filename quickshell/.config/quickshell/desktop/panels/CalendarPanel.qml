import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"

Overlay {
    id: root
    panelName: "calendar"
    dialog: true
    property date selected: new Date()
    property int month: selected.getMonth()
    property int year: selected.getFullYear()
    readonly property var locale: I18n.locale
    readonly property var selectedEvents: Calendar.forDay(selected)
    readonly property var days: {
        const first = new Date(year, month, 1, 12);
        const offset = (first.getDay() - (locale.firstDayOfWeek % 7) + 7) % 7;
        return Array.from({
            length: 42
        }, (_, i) => new Date(year, month, i - offset + 1, 12));
    }
    function loadEvents() {
        if (!visible)
            return;
        const first = days[0];
        const last = days[41];
        Calendar.load(new Date(first.getFullYear(), first.getMonth(), first.getDate()), new Date(last.getFullYear(), last.getMonth(), last.getDate() + 1));
    }
    // Coalesce year+month updates (and onOpened) into one load per event-loop turn.
    onDaysChanged: Qt.callLater(loadEvents)
    SystemClock {
        id: clock
        precision: SystemClock.Minutes
    }
    function eventTime(event) {
        if (event.allDay)
            return I18n.tr("calendar.allDay");
        const start = new Date(event.start), end = new Date(event.end);
        const format = I18n.tr(sameDay(start, end) ? "calendar.timeFormat" : "calendar.dateTimeFormat");
        return locale.toString(start, format) + " – " + locale.toString(end, format);
    }
    function sameDay(a, b) {
        return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
    }
    function today() {
        selected = clock.date;
        month = selected.getMonth();
        year = selected.getFullYear();
    }
    function shiftMonth(delta) {
        const date = new Date(year, month + delta, 1, 12);
        year = date.getFullYear();
        month = date.getMonth();
    }
    function moveDay(delta) {
        selected = new Date(selected.getFullYear(), selected.getMonth(), selected.getDate() + delta, 12);
        year = selected.getFullYear();
        month = selected.getMonth();
    }
    // The time zone search: open, its text and the matches (by name, region or offset, as UTC+1).
    property bool pickingZone: false
    property string zoneQuery: ""
    readonly property var zoneMatches: {
        const fold = text => text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[_/]/g, " ").replace(/−/g, "-");
        const words = fold(zoneQuery).split(/\s+/).filter(word => word !== "");
        if (!pickingZone)
            return [];
        return TimeZones.zones.filter(zone => {
            const haystack = fold(zone.name + " " + TimeZones.label(zone.offset));
            return words.every(word => haystack.includes(word));
        }).slice(0, 200);
    }
    function openZones() {
        zoneSearch.text = "";
        pickingZone = true;
        Qt.callLater(() => zoneSearch.forceActiveFocus());
    }
    function closeZones() {
        pickingZone = false;
        keyboard.forceActiveFocus();
    }
    function applyZone(name) {
        closeZones();
        TimeZones.set(name);
    }
    onOpened: {
        Weather.refresh();
        TimeZones.refresh();
        pickingZone = false;
        today();
        Qt.callLater(loadEvents);
        keyboard.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(Theme.dialogNarrow, parent.width - 48)
        height: Math.min(layout.implicitHeight + 2 * Theme.dialogPadding, parent.height - Theme.panelClearance)
        FocusScope {
            id: keyboard
            anchors.fill: parent
            Keys.onLeftPressed: root.moveDay(-1)
            Keys.onRightPressed: root.moveDay(1)
            Keys.onUpPressed: root.moveDay(-7)
            Keys.onDownPressed: root.moveDay(7)
            Keys.onPressed: event => {
                if (event.key === Qt.Key_Home)
                    root.today();
                else if (event.key === Qt.Key_PageUp)
                    root.shiftMonth(-1);
                else if (event.key === Qt.Key_PageDown)
                    root.shiftMonth(1);
                else
                    return;
                event.accepted = true;
            }
            ColumnLayout {
                id: layout
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    margins: Theme.dialogPadding
                    bottom: parent.bottom
                }
                spacing: 14
                PanelHeader {
                    Layout.fillWidth: true
                    title: I18n.tr("calendar.title")
                }
                // The system time zone: what it is, the zone of where the computer seems to be when they differ,
                // and a search to change it.
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Icon {
                            name: "clock"
                            color: Theme.muted
                            Layout.preferredWidth: 16
                            Layout.preferredHeight: 16
                        }
                        Text {
                            Layout.fillWidth: true
                            text: TimeZones.current === "" ? I18n.tr("common.loading") : I18n.tr("timezone.current", [TimeZones.displayName(TimeZones.current), TimeZones.label(TimeZones.offset)])
                            elide: Text.ElideRight
                            textFormat: Text.PlainText
                            color: Theme.muted
                            font.pixelSize: Theme.textSize(12)
                        }
                        ActionButton {
                            outlined: true
                            implicitHeight: Theme.hit(30)
                            text: root.pickingZone ? I18n.tr("common.close") : I18n.tr("timezone.change")
                            enabled: !TimeZones.busy && TimeZones.zones.length > 0
                            onClicked: root.pickingZone ? root.closeZones() : root.openZones()
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true
                        visible: !!TimeZones.suggested && !root.pickingZone && !TimeZones.busy
                        implicitHeight: suggestion.implicitHeight + 16
                        radius: Theme.corner(10)
                        color: Theme.active
                        RowLayout {
                            id: suggestion
                            anchors {
                                fill: parent
                                margins: 8
                                leftMargin: 12
                            }
                            spacing: 10
                            Text {
                                Layout.fillWidth: true
                                text: TimeZones.suggested ? I18n.tr("timezone.suggestion", [TimeZones.displayName(TimeZones.suggested.name), TimeZones.label(TimeZones.suggested.offset)]) : ""
                                wrapMode: Text.WordWrap
                                textFormat: Text.PlainText
                                color: Theme.text
                                font.pixelSize: Theme.textSize(12)
                            }
                            ActionButton {
                                highlighted: true
                                implicitHeight: Theme.hit(30)
                                text: I18n.tr("timezone.use")
                                onClicked: TimeZones.set(TimeZones.suggested.name)
                            }
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        visible: root.pickingZone
                        spacing: 6
                        InputField {
                            id: zoneSearch
                            Layout.fillWidth: true
                            placeholderText: I18n.tr("timezone.search")
                            onTextChanged: {
                                root.zoneQuery = text;
                                zoneList.currentIndex = 0;
                            }
                            Keys.onUpPressed: zoneList.currentIndex = Math.max(0, zoneList.currentIndex - 1)
                            Keys.onDownPressed: zoneList.currentIndex = Math.min(zoneList.count - 1, zoneList.currentIndex + 1)
                            Keys.onReturnPressed: {
                                if (zoneList.currentIndex >= 0 && zoneList.currentIndex < root.zoneMatches.length)
                                    root.applyZone(root.zoneMatches[zoneList.currentIndex].name);
                            }
                            Keys.onEnterPressed: {
                                if (zoneList.currentIndex >= 0 && zoneList.currentIndex < root.zoneMatches.length)
                                    root.applyZone(root.zoneMatches[zoneList.currentIndex].name);
                            }
                            Keys.onEscapePressed: event => {
                                root.closeZones();
                                event.accepted = true;
                            }
                        }
                        ListView {
                            id: zoneList
                            Layout.fillWidth: true
                            Layout.preferredHeight: Theme.hit(200)
                            clip: true
                            model: root.zoneMatches
                            highlightMoveDuration: 0
                            boundsBehavior: Flickable.StopAtBounds
                            delegate: ActionButton {
                                required property var modelData
                                required property int index
                                width: ListView.view.width
                                implicitHeight: Theme.hit(34)
                                alignLeft: true
                                text: TimeZones.displayName(modelData.name) + "  ·  " + TimeZones.label(modelData.offset)
                                highlighted: ListView.isCurrentItem
                                tone: "cursor"
                                onClicked: root.applyZone(modelData.name)
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            visible: zoneList.count === 0
                            text: I18n.tr("timezone.noMatches")
                            color: Theme.muted
                            font.pixelSize: Theme.textSize(12)
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: TimeZones.busy || TimeZones.error !== "" || TimeZones.changed
                        text: TimeZones.busy ? I18n.tr("timezone.waiting") : TimeZones.error !== "" ? TimeZones.error : I18n.tr("timezone.restartNote")
                        wrapMode: Text.WordWrap
                        textFormat: Text.PlainText
                        color: TimeZones.error !== "" && !TimeZones.busy ? Theme.danger : Theme.muted
                        font.pixelSize: Theme.textSize(11)
                    }
                }
                // Weather: now, then every two hours; the place and the time of the reading below.
                ColumnLayout {
                    Layout.fillWidth: true
                    visible: Weather.enabled && (Weather.ready || (Weather.data.error ?? "") !== "")
                    spacing: 8
                    RowLayout {
                        Layout.fillWidth: true
                        visible: Weather.ready
                        spacing: 12
                        Icon {
                            name: Weather.ready ? Weather.icon(Weather.data.current.code, Weather.data.current.day) : "cloud"
                            Layout.preferredWidth: 36
                            Layout.preferredHeight: 36
                        }
                        Text {
                            text: Weather.ready ? Weather.data.current.temp + "°" : ""
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(30)
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                Layout.fillWidth: true
                                text: Weather.ready ? Weather.condition(Weather.data.current.code) + (Weather.data.place ? " · " + Weather.data.place : "") : ""
                                textFormat: Text.PlainText
                                color: Theme.text
                                elide: Text.ElideRight
                            }
                            Text {
                                Layout.fillWidth: true
                                text: Weather.ready ? I18n.tr("weather.feels", [Weather.data.current.feels]) + " · " + I18n.tr("weather.wind", [Weather.data.current.wind]) : ""
                                color: Theme.muted
                                font.pixelSize: Theme.textSize(12)
                                elide: Text.ElideRight
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        visible: Weather.ready
                        spacing: 4
                        uniformCellSizes: true
                        Repeater {
                            model: Weather.data.hours ?? []
                            ColumnLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredWidth: 0
                                spacing: 2
                                // Filling the cell lets the column stretch: a layout is no wider than its widest child
                                // unless one of them fills, and the six entries then stay packed at the left.
                                Text {
                                    Layout.fillWidth: true
                                    horizontalAlignment: Text.AlignHCenter
                                    text: modelData.time
                                    color: Theme.muted
                                    font.pixelSize: Theme.textSize(11)
                                }
                                Icon {
                                    Layout.alignment: Qt.AlignHCenter
                                    name: Weather.icon(modelData.code, modelData.day)
                                    Layout.preferredWidth: 18
                                    Layout.preferredHeight: 18
                                }
                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: modelData.temp + "°" + (modelData.rain >= 30 ? " " + I18n.tr("weather.rain", [modelData.rain]) : "")
                                    color: Theme.text
                                    font.pixelSize: Theme.textSize(12)
                                }
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: (Weather.data.error ?? "") !== ""
                        text: Weather.data.stale && Weather.ready ? I18n.tr("weather.stale", [I18n.locale.toString(new Date(Weather.data.updated * 1000), I18n.timeFormat)]) : (Weather.data.error ?? "")
                        textFormat: Text.PlainText
                        color: Theme.muted
                        font.pixelSize: Theme.textSize(11)
                        wrapMode: Text.WordWrap
                    }
                }
                RowLayout {
                    PanelIconButton {
                        iconName: "chevron-left"
                        tooltip: I18n.tr("calendar.previousMonth")
                        onClicked: root.shiftMonth(-1)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.locale.toString(new Date(root.year, root.month, 1), I18n.tr("calendar.monthFormat"))
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: Theme.textSize(18)
                        font.family: Theme.font
                        color: Theme.text
                    }
                    PanelIconButton {
                        iconName: "chevron-right"
                        tooltip: I18n.tr("calendar.nextMonth")
                        onClicked: root.shiftMonth(1)
                    }
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 7
                    columnSpacing: 3
                    rowSpacing: 3
                    Repeater {
                        model: Array.from({
                            length: 7
                        }, (_, i) => root.locale.dayName((root.locale.firstDayOfWeek + i) % 7, Locale.NarrowFormat))
                        Text {
                            required property string modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 26
                            text: modelData
                            horizontalAlignment: Text.AlignHCenter
                            color: Theme.muted
                            font.pixelSize: Theme.textSize(12)
                        }
                    }
                    Repeater {
                        model: root.days
                        ActionButton {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: Theme.hit(40)
                            implicitWidth: 0
                            implicitHeight: Theme.hit(40)
                            text: modelData.getDate()
                            highlighted: root.sameDay(modelData, root.selected)
                            tone: "cursor"
                            opacity: modelData.getMonth() === root.month ? 1 : 0.4
                            // The date is printed under the grid; the tooltip only says which cell is today.
                            tooltip: root.sameDay(modelData, clock.date) ? I18n.tr("calendar.today") : ""
                            onClicked: {
                                root.selected = modelData;
                                keyboard.forceActiveFocus();
                            }
                            Rectangle {
                                anchors.horizontalCenter: parent.horizontalCenter
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 3
                                width: 4
                                height: 4
                                radius: 2
                                color: Theme.accent
                                visible: root.sameDay(parent.modelData, clock.date) || Calendar.hasEvents(parent.modelData)
                            }
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: root.locale.toString(root.selected, I18n.tr("calendar.longDateFormat"))
                    color: Theme.text
                    horizontalAlignment: Text.AlignHCenter
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: Math.min(210, agenda.implicitHeight)
                    Layout.minimumHeight: 50
                    contentWidth: availableWidth
                    clip: true
                    ColumnLayout {
                        id: agenda
                        width: parent.width
                        spacing: 8
                        Repeater {
                            model: root.selectedEvents
                            Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: eventText.implicitHeight + 20
                                radius: Theme.corner(8)
                                color: Theme.raised
                                Rectangle {
                                    anchors {
                                        left: parent.left
                                        top: parent.top
                                        bottom: parent.bottom
                                        margins: 8
                                    }
                                    width: 3
                                    radius: 1.5
                                    color: Calendar.source(parent.modelData.source)?.color || Theme.accent
                                }
                                ColumnLayout {
                                    id: eventText
                                    anchors {
                                        left: parent.left
                                        right: parent.right
                                        top: parent.top
                                        leftMargin: 18
                                        rightMargin: 10
                                        topMargin: 10
                                    }
                                    spacing: 3
                                    Text {
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                        text: modelData.title
                                        color: Theme.text
                                        font.bold: true
                                        textFormat: Text.PlainText
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                        text: root.eventTime(modelData) + " · " + (Calendar.source(modelData.source)?.name || "")
                                        color: Theme.muted
                                        font.pixelSize: Theme.textSize(11)
                                        textFormat: Text.PlainText
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                        visible: text !== ""
                                        text: modelData.location
                                        color: Theme.muted
                                        font.pixelSize: Theme.textSize(11)
                                        textFormat: Text.PlainText
                                    }
                                }
                            }
                        }
                        Text {
                            visible: root.selectedEvents.length === 0
                            text: Calendar.busy && Calendar.sources.length === 0 ? I18n.tr("calendar.loading") : Calendar.sources.length ? I18n.tr("calendar.noEvents") : I18n.tr("calendar.noCalendars")
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            color: Theme.muted
                        }
                        Text {
                            visible: Calendar.error !== ""
                            text: Calendar.error
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            color: Theme.danger
                            font.pixelSize: Theme.textSize(11)
                            textFormat: Text.PlainText
                        }
                    }
                }
                RowLayout {
                    ActionButton {
                        outlined: true
                        text: I18n.tr("calendar.today")
                        onClicked: {
                            root.today();
                            keyboard.forceActiveFocus();
                        }
                    }
                    ActionButton {
                        outlined: true
                        text: Calendar.busy ? I18n.tr("common.loading") : I18n.tr("common.refresh")
                        enabled: !Calendar.busy
                        onClicked: root.loadEvents()
                    }
                }
                KeyHints {
                    hints: root.pickingZone ? I18n.tr("timezone.pickerHint") : I18n.tr("calendar.navigationHint")
                }
            }
        }
    }
}
