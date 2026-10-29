import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

Overlay {
    id: root
    panelName: "clipboard"
    dialog: true
    property bool confirmClear: false
    onOpened: {
        confirmClear = false;
        search.clear();
        Clipboard.refresh();
        // In tablet mode the search field waits for a tap: focused, it would open the keyboard just to browse.
        if (!Tablet.active)
            search.forceActiveFocus();
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(620, parent.width - 32)
        height: Math.min(560, parent.height - 76)
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Theme.dialogPadding
            spacing: 12
            PanelHeader {
                title: I18n.tr("clipboard.title")
                Layout.fillWidth: true
                PanelIconButton {
                    iconName: Clipboard.paused ? "play" : "pause"
                    tooltip: Clipboard.paused ? I18n.tr("clipboard.resume") : I18n.tr("clipboard.pause")
                    enabled: Config.clipboardEnabled
                    onClicked: Clipboard.paused = !Clipboard.paused
                }
                PanelIconButton {
                    iconName: "trash"
                    tooltip: I18n.tr("clipboard.clearHistory")
                    enabled: !Clipboard.busy && Clipboard.entries.length > 0
                    onClicked: root.confirmClear = !root.confirmClear
                }
            }
            RowLayout {
                visible: root.confirmClear
                Layout.fillWidth: true
                Text {
                    text: I18n.tr("clipboard.confirmClear")
                    color: Theme.text
                    Layout.fillWidth: true
                }
                ActionButton {
                    text: I18n.tr("common.delete")
                    destructive: true
                    onClicked: {
                        Clipboard.act("clear");
                        root.confirmClear = false;
                    }
                }
                ActionButton {
                    text: I18n.tr("common.cancel")
                    onClicked: root.confirmClear = false
                }
            }
            InputField {
                id: search
                Layout.fillWidth: true
                placeholderText: I18n.tr("clipboard.searchPlaceholder")
                onTextChanged: clips.currentIndex = 0
                Keys.onDownPressed: clips.currentIndex = Math.min(clips.count - 1, clips.currentIndex + 1)
                Keys.onUpPressed: clips.currentIndex = Math.max(0, clips.currentIndex - 1)
                onAccepted: if (clips.model[clips.currentIndex])
                    Clipboard.act("copy", clips.model[clips.currentIndex].id)
            }
            ListView {
                id: clips
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                spacing: 4
                model: Clipboard.entries.filter(e => e.preview.toLowerCase().includes(search.text.toLowerCase()))
                delegate: RowLayout {
                    required property var modelData
                    required property int index
                    width: clips.width
                    ActionButton {
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        implicitHeight: 46
                        text: modelData.preview
                        iconName: modelData.image ? "image" : "clipboard"
                        alignLeft: true
                        highlighted: clips.currentIndex === index
                        enabled: !Clipboard.busy
                        onClicked: Clipboard.act("copy", modelData.id)
                    }
                    PanelIconButton {
                        iconName: "trash"
                        tooltip: I18n.tr("clipboard.deleteItem")
                        enabled: !Clipboard.busy
                        onClicked: Clipboard.act("delete", modelData.id)
                    }
                }
                ScrollBar.vertical: ScrollBar {}
                Text {
                    anchors.centerIn: parent
                    visible: clips.count === 0
                    text: I18n.tr("clipboard.empty")
                    color: Theme.muted
                }
            }
            Text {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: Clipboard.error || (!Config.clipboardEnabled ? I18n.tr("clipboard.disabled") : Clipboard.paused ? I18n.tr("clipboard.paused") : I18n.tr("clipboard.navigationHint"))
                color: Clipboard.error ? Theme.danger : Theme.muted
                font.pixelSize: 12
                textFormat: Text.PlainText
            }
        }
    }
}
