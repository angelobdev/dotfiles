pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// Reminders (Super + Ctrl + M, the bar indicator, desktop-shell toggle reminders): when ("20", "1h30", "14:30")
// and what, then Enter; the pending ones below, the next first, each with its time and how long is left.
Overlay {
    id: root
    panelName: "reminders"
    dialog: true
    property bool invalid: false
    function add() {
        if (Reminders.add(when.text, what.text)) {
            when.text = "";
            what.text = "";
            invalid = false;
            when.forceActiveFocus();
        } else {
            invalid = true;
        }
    }
    function left(entry) {
        const minutes = Reminders.minutesLeft(entry);
        return minutes >= 60 ? I18n.tr("battery.durationHours", [Math.floor(minutes / 60), minutes % 60]) : I18n.tr("battery.durationMinutes", [minutes]);
    }
    onOpened: {
        invalid = false;
        Reminders.now = Date.now();
        when.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(Theme.dialogNarrow, parent.width - 48)
        height: Math.min(layout.implicitHeight + 2 * Theme.dialogPadding, parent.height - Theme.panelClearance)
        ColumnLayout {
            id: layout
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 14
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("reminders.title")
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                InputField {
                    id: when
                    Layout.preferredWidth: 110
                    placeholderText: I18n.tr("reminders.when")
                    onTextChanged: root.invalid = false
                    Keys.onReturnPressed: what.text === "" ? what.forceActiveFocus() : root.add()
                    Keys.onEnterPressed: what.text === "" ? what.forceActiveFocus() : root.add()
                    KeyNavigation.tab: what
                }
                InputField {
                    id: what
                    Layout.fillWidth: true
                    placeholderText: I18n.tr("reminders.what")
                    Keys.onReturnPressed: root.add()
                    Keys.onEnterPressed: root.add()
                }
                ActionButton {
                    highlighted: true
                    text: I18n.tr("reminders.add")
                    enabled: when.text.trim() !== ""
                    onClicked: root.add()
                }
            }
            Text {
                Layout.fillWidth: true
                text: root.invalid ? I18n.tr("reminders.invalid") : I18n.tr("reminders.hint")
                color: root.invalid ? Theme.danger : Theme.muted
                wrapMode: Text.WordWrap
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
            Heading {
                visible: Reminders.list.length > 0
                section: true
                text: I18n.tr("reminders.pending")
            }
            Repeater {
                model: Reminders.list
                RowLayout {
                    id: row
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 10
                    Text {
                        text: I18n.locale.toString(new Date(row.modelData.at), I18n.timeFormat)
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                        font.weight: Font.DemiBold
                    }
                    Text {
                        Layout.fillWidth: true
                        text: row.modelData.text || I18n.tr("reminders.untitled")
                        elide: Text.ElideRight
                        textFormat: Text.PlainText
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                    }
                    Text {
                        text: root.left(row.modelData)
                        color: Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(11)
                    }
                    CompactIconButton {
                        iconName: "close"
                        iconSize: 14
                        tooltip: I18n.tr("reminders.remove")
                        onClicked: Reminders.remove(row.modelData.id)
                    }
                }
            }
            ActionButton {
                visible: Reminders.list.length > 1
                Layout.alignment: Qt.AlignRight
                outlined: true
                text: I18n.tr("reminders.clear")
                onClicked: Reminders.clear()
            }
            KeyHints {
                hints: I18n.tr("reminders.keys")
            }
        }
    }
}
