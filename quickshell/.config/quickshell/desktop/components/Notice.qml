import QtQuick
import QtQuick.Layouts
import ".."
Rectangle {
    id: root
    required property var notification
    signal hidePopup()
    property bool popup: false
    color: Theme.raised
    radius: 10
    implicitHeight: column.implicitHeight + 24
    ColumnLayout {
        id: column
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 6
        Text { text: root.notification.appName; color: Theme.muted; font.pixelSize: 11; textFormat: Text.PlainText }
        Text { text: root.notification.summary; color: Theme.text; font.bold: true; Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText }
        Text { text: root.notification.body; color: Theme.text; visible: text !== ""; Layout.fillWidth: true; wrapMode: Text.Wrap; textFormat: Text.PlainText }
        Flow {
            Layout.fillWidth: true
            spacing: 4
            Repeater {
                model: root.notification.actions
                ActionButton { required property var modelData; text: modelData.text; onClicked: modelData.invoke() }
            }
            ActionButton { iconName: "trash"; text: "Elimina"; onClicked: root.notification.dismiss() }
            ActionButton { visible: root.popup; iconName: "close"; text: "Nascondi"; onClicked: root.hidePopup() }
        }
    }
}
