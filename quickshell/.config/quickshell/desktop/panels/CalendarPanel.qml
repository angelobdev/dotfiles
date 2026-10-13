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
    property date selected: new Date()
    property int month: selected.getMonth()
    property int year: selected.getFullYear()
    readonly property var locale: I18n.locale
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
    onDaysChanged: loadEvents()
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
        today();
        loadEvents();
        keyboard.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(480, parent.width - 48)
        height: Math.min(layout.implicitHeight + 44, parent.height - 76)
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
                    margins: 22
                    bottom: parent.bottom
                }
                spacing: 14
                Heading {
                    text: I18n.tr("calendar.title")
                }
                RowLayout {
                    PanelIconButton {
                        iconName: "chevron-left"
                        tooltip: I18n.tr("calendar.previousMonth")
                        onClicked: root.shiftMonth(-1)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: root.locale.toString(new Date(root.year, root.month, 1), "MMMM yyyy")
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: 18
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
                        model: Array.from({length: 7}, (_, i) => root.locale.dayName((root.locale.firstDayOfWeek + i) % 7, Locale.NarrowFormat))
                        Text {
                            required property string modelData
                            Layout.fillWidth: true
                            Layout.preferredHeight: 26
                            text: modelData
                            horizontalAlignment: Text.AlignHCenter
                            color: Theme.muted
                            font.pixelSize: 12
                        }
                    }
                    Repeater {
                        model: root.days
                        ActionButton {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: 40
                            implicitWidth: 0
                            implicitHeight: 40
                            text: modelData.getDate()
                            highlighted: root.sameDay(modelData, root.selected)
                            opacity: modelData.getMonth() === root.month ? 1 : 0.4
                            tooltip: root.locale.toString(modelData, I18n.tr("calendar.longDateFormat")) + (root.sameDay(modelData, clock.date) ? I18n.tr("calendar.todaySuffix") : "")
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
                                color: parent.highlighted ? Theme.accentText : Theme.accent
                                visible: root.sameDay(parent.modelData, clock.date) || Calendar.forDay(parent.modelData).length > 0
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
                            model: Calendar.forDay(root.selected)
                            Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                implicitHeight: eventText.implicitHeight + 20
                                radius: 8
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
                                        font.pixelSize: 11
                                        textFormat: Text.PlainText
                                    }
                                    Text {
                                        Layout.fillWidth: true
                                        wrapMode: Text.Wrap
                                        visible: text !== ""
                                        text: modelData.location
                                        color: Theme.muted
                                        font.pixelSize: 11
                                        textFormat: Text.PlainText
                                    }
                                }
                            }
                        }
                        Text {
                            visible: Calendar.forDay(root.selected).length === 0
                            text: Calendar.busy ? I18n.tr("calendar.loading") : Calendar.sources.length ? I18n.tr("calendar.noEvents") : I18n.tr("calendar.noCalendars")
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
                            font.pixelSize: 11
                            textFormat: Text.PlainText
                        }
                    }
                }
                RowLayout {
                    ActionButton {
                        text: I18n.tr("calendar.today")
                        onClicked: {
                            root.today();
                            keyboard.forceActiveFocus();
                        }
                    }
                    ActionButton {
                        text: I18n.tr("common.refresh")
                        enabled: !Calendar.busy
                        onClicked: root.loadEvents()
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    ActionButton {
                        text: I18n.tr("common.close")
                        onClicked: ShellState.close()
                    }
                }
                Text {
                    text: I18n.tr("calendar.navigationHint")
                    color: Theme.muted
                    font.pixelSize: 11
                }
            }
        }
    }
}
