import QtQuick
import "../components"
import QtQuick.Layouts
import Quickshell
import ".."
import "../services"
import "NotificationText.js" as NotificationText

Rectangle {
    id: root
    required property var notification
    signal hidePopup
    signal deckRequested
    signal stackToggled
    property bool popup: false
    // In a deck: the lines a popup shows, and whether its text is hidden behind the front card.
    property int bodyLines: 6
    property bool contentHidden: false
    // A closed deck of popups in tablet mode opens with a tap, as there is no hover to open it.
    property bool opensDeck: false
    // In the center: how many entries a closed stack stands for, and whether this one heads an open stack.
    property int stackCount: 1
    property bool stackOpen: false
    // Restored from before a shell restart: readable and removable, with no actions left.
    // The notification goes null for a moment when it closes, before this delegate does.
    readonly property bool archived: notification?.archived === true
    readonly property var defaultAction: notification?.actions.find(a => a.identifier === "default") ?? null
    readonly property var buttons: notification?.actions.filter(a => !popup || a.identifier !== "default") ?? []
    readonly property string appIcon: {
        const icon = notification?.appIcon || notification?.desktopEntry || "";
        if (icon.startsWith("/") || icon.startsWith("file:") || icon.startsWith("image:"))
            return icon;
        return icon && !icon.includes(":") ? Quickshell.iconPath(icon, true) : "";
    }
    color: Theme.raised
    radius: Theme.corner(10)
    // Popups are surfaces of their own and take the window border; entries in the center sit in its card.
    border.width: popup ? Theme.borderSize : 0
    border.color: Theme.frameInactive
    implicitHeight: column.implicitHeight + 24
    // Swiped sideways past a third of its width, a popup goes away like a right click (it stays in the
    // center) and an entry of the center is deleted; a shorter swipe springs back.
    property real swipe: 0
    function dismiss() {
        if (popup)
            hidePopup();
        else if (archived)
            Notices.forget(notification.id);
        else
            notification.dismiss();
    }
    transform: Translate {
        x: root.swipe
    }
    opacity: 1 - Math.min(0.7, Math.abs(swipe) / Math.max(1, width))
    NumberAnimation {
        id: swipeAnimation
        target: root
        property: "swipe"
        duration: Theme.motionFast
        easing.type: Easing.OutCubic
        onFinished: {
            if (Math.abs(root.swipe) >= root.width)
                root.dismiss();
        }
    }
    // Clicks act only on popups, but the area always holds the swipe handler: a handler of the item sees the
    // press before the item, so it can take a drag over from it (a handler on the parent would never see it).
    MouseArea {
        anchors.fill: parent
        acceptedButtons: root.popup ? Qt.LeftButton | Qt.RightButton : Qt.NoButton
        cursorShape: root.popup && root.defaultAction ? Qt.PointingHandCursor : Qt.ArrowCursor
        DragHandler {
            target: null
            yAxis.enabled: false
            onTranslationChanged: if (active)
                root.swipe = translation.x
            onActiveChanged: {
                if (active) {
                    swipeAnimation.stop();
                    return;
                }
                const away = Math.abs(root.swipe) > root.width / 3;
                swipeAnimation.to = away ? (root.swipe < 0 ? -root.width : root.width) : 0;
                swipeAnimation.start();
            }
        }
        // A long press (touch) hides the popup like a right click.
        property bool held: false
        pressAndHoldInterval: 500
        onPressed: held = false
        onPressAndHold: {
            held = true;
            root.hidePopup();
        }
        onClicked: mouse => {
            if (held)
                return;
            if (mouse.button === Qt.RightButton)
                root.hidePopup();
            else if (root.opensDeck)
                root.deckRequested();
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
        opacity: root.contentHidden ? 0 : 1
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.motionFast
                easing.type: Easing.OutCubic
            }
        }
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
                text: root.notification?.appName || I18n.tr("notifications.fallbackTitle")
                color: Theme.muted
                font.pixelSize: 11
                textFormat: Text.PlainText
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Text {
                visible: root.archived
                text: I18n.tr("notifications.archived")
                color: Theme.muted
                font.pixelSize: 11
                font.italic: true
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Text {
                id: summary
                text: root.notification?.summary ?? ""
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
                implicitHeight: Math.max(Theme.hit(24), summary.font.pixelSize + 8)
                topPadding: 0
                bottomPadding: 0
                compact: true
                destructive: true
                text: I18n.tr("common.delete")
                font.pixelSize: summary.font.pixelSize
                font.bold: summary.font.bold
                onClicked: root.dismiss()
            }
        }
        Text {
            text: NotificationText.styled(root.notification?.body ?? "")
            color: Theme.text
            visible: text !== ""
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            maximumLineCount: root.popup ? root.bodyLines : 2147483647
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
        ActionButton {
            visible: root.stackCount > 1 || root.stackOpen
            Layout.alignment: Qt.AlignRight
            compact: true
            text: root.stackOpen ? I18n.tr("notifications.less") : I18n.plural("notifications.more.one", "notifications.more.other", root.stackCount - 1)
            onClicked: root.stackToggled()
        }
    }
}
