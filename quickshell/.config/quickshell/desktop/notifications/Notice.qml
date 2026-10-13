import QtQuick
import "../components"
import QtQuick.Layouts
import Quickshell
import ".."
import "NotificationText.js" as NotificationText

Rectangle {
    id: root
    required property var notification
    signal hidePopup
    property bool popup: false
    readonly property var defaultAction: notification.actions.find(a => a.identifier === "default") ?? null
    readonly property var buttons: notification.actions.filter(a => !popup || a.identifier !== "default")
    readonly property string appIcon: {
        const icon = notification.appIcon || notification.desktopEntry || "";
        if (icon.startsWith("/") || icon.startsWith("file:") || icon.startsWith("image:"))
            return icon;
        return icon && !icon.includes(":") ? Quickshell.iconPath(icon, true) : "";
    }
    color: Theme.raised
    radius: 10
    implicitHeight: column.implicitHeight + 24
    MouseArea {
        anchors.fill: parent
        enabled: root.popup
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: root.defaultAction ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: mouse => {
            if (mouse.button === Qt.RightButton)
                root.hidePopup();
            else if (root.defaultAction)
                root.defaultAction.invoke();
        }
    }
    ColumnLayout {
        id: column
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: 12
        }
        spacing: 6
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Item {
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                Image {
                    id: appImage
                    anchors.fill: parent
                    source: root.appIcon
                    sourceSize: Qt.size(48, 48)
                    fillMode: Image.PreserveAspectFit
                }
                Icon {
                    anchors.fill: parent
                    name: "bell"
                    visible: appImage.status !== Image.Ready
                }
            }
            Text {
                text: root.notification.appName || "Notifica"
                color: Theme.muted
                font.pixelSize: 11
                textFormat: Text.PlainText
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                id: summary
                text: root.notification.summary
                color: Theme.text
                font.bold: true
                font.pixelSize: 13
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                maximumLineCount: root.popup ? 3 : 2147483647
                elide: Text.ElideRight
                textFormat: Text.PlainText
            }
            ActionButton {
                visible: !root.popup
                Layout.alignment: Qt.AlignTop
                implicitHeight: Math.max(24, summary.font.pixelSize + 8)
                topPadding: 0
                bottomPadding: 0
                compact: true
                destructive: true
                text: "Elimina"
                font.pixelSize: summary.font.pixelSize
                font.bold: summary.font.bold
                onClicked: root.notification.dismiss()
            }
        }
        Text {
            text: NotificationText.styled(root.notification.body)
            color: Theme.text
            visible: text !== ""
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            maximumLineCount: root.popup ? 6 : 2147483647
            elide: Text.ElideRight
            textFormat: Text.StyledText
        }
        Flow {
            Layout.fillWidth: true
            visible: root.buttons.length > 0
            spacing: 4
            Repeater {
                model: root.buttons
                ActionButton {
                    required property var modelData
                    text: modelData.text
                    onClicked: modelData.invoke()
                }
            }
        }
    }
}
