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
    onOpened: {
        Weather.refresh();
        today();
        Qt.callLater(loadEvents);
        keyboard.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(480, parent.width - 48)
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
                        spacing: 0
                        Repeater {
                            model: Weather.data.hours ?? []
                            ColumnLayout {
                                required property var modelData
                                Layout.fillWidth: true
                                spacing: 2
                                Text {
                                    Layout.alignment: Qt.AlignHCenter
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
                Text {
                    // Wraps instead of widening the layout past the panel (wide theme fonts, long translations).
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: I18n.tr("calendar.navigationHint")
                    color: Theme.muted
                    font.pixelSize: Theme.textSize(11)
                }
            }
        }
    }
}
