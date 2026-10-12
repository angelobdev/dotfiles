import QtQuick
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"

Overlay {
    id: root
    panelName: "calendar"
    property date selected: new Date()
    property int month: selected.getMonth()
    property int year: selected.getFullYear()
    readonly property var locale: Qt.locale("it_IT")
    readonly property var days: {
        const first = new Date(year, month, 1, 12);
        const offset = (first.getDay() + 6) % 7;
        return Array.from({
            length: 42
        }, (_, i) => new Date(year, month, i - offset + 1, 12));
    }
    SystemClock {
        id: clock
        precision: SystemClock.Minutes
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
        keyboard.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(480, parent.width - 48)
        height: layout.implicitHeight + 44
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
                }
                spacing: 14
                Heading {
                    text: "Calendario"
                }
                RowLayout {
                    PanelIconButton {
                        iconName: "chevron-left"
                        tooltip: "Mese precedente"
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
                        tooltip: "Mese successivo"
                        onClicked: root.shiftMonth(1)
                    }
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: 7
                    columnSpacing: 3
                    rowSpacing: 3
                    Repeater {
                        model: ["L", "M", "M", "G", "V", "S", "D"]
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
                            tooltip: root.locale.toString(modelData, "dddd d MMMM yyyy") + (root.sameDay(modelData, clock.date) ? " · Oggi" : "")
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
                                color: parent.highlighted ? Theme.background : Theme.accent
                                visible: root.sameDay(parent.modelData, clock.date)
                            }
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: root.locale.toString(root.selected, "dddd d MMMM yyyy")
                    color: Theme.text
                    horizontalAlignment: Text.AlignHCenter
                }
                RowLayout {
                    ActionButton {
                        text: "Oggi"
                        onClicked: {
                            root.today();
                            keyboard.forceActiveFocus();
                        }
                    }
                    Item {
                        Layout.fillWidth: true
                    }
                    ActionButton {
                        text: "Chiudi"
                        onClicked: ShellState.close()
                    }
                }
                Text {
                    text: "Frecce: giorno · PgUp/PgDn: mese · Home: oggi"
                    color: Theme.muted
                    font.pixelSize: 11
                }
            }
        }
    }
}
