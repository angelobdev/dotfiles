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
    // In the center: the time the age of the entry is counted to; popups leave it at 0 and show no age.
    property real now: 0
    // Restored from before a shell restart: readable and removable, with no actions left.
    // The notification goes null for a moment when it closes, before this delegate does.
    readonly property bool archived: notification?.archived === true
    readonly property var defaultAction: notification?.actions.find(a => a.identifier === "default") ?? null
    readonly property var buttons: notification?.actions.filter(a => !popup || a.identifier !== "default") ?? []
    readonly property string appLabel: notification?.appName || I18n.tr("notifications.fallbackTitle")
    readonly property bool titleLeads: NotificationText.repeatsTitle(appLabel, notification?.summary)
    // How long ago it arrived, against now.
    readonly property string age: {
        const elapsed = now > 0 ? NotificationText.age(Notices.arrivalOf(notification), now) : null;
        switch (elapsed?.unit) {
        case "now":
            return I18n.tr("notifications.age.now");
        case "minutes":
            return I18n.plural("notifications.age.minutes.one", "notifications.age.minutes.other", elapsed.count);
        case "hours":
            return I18n.plural("notifications.age.hours.one", "notifications.age.hours.other", elapsed.count);
        case "yesterday":
            return I18n.tr("notifications.age.yesterday");
        case "date":
            return I18n.locale.toString(new Date(Notices.arrivalOf(notification)), I18n.tr("notifications.age.dateFormat"));
        default:
            return "";
        }
    }
    readonly property string appIcon: {
        const icon = notification?.appIcon || notification?.desktopEntry || "";
        if (icon.startsWith("/") || icon.startsWith("file:") || icon.startsWith("image:"))
            return icon;
        return icon && !icon.includes(":") ? Quickshell.iconPath(icon, true) : "";
    }
    color: popup ? Theme.notice : Theme.raised
    // A popup is a surface of its own, with the window radius; entries of the center sit inside its card.
    radius: popup ? Theme.radius : Theme.corner(10)
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
    HoverHandler {
        id: hover
        enabled: !root.popup
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
            // The app name, or the title in its place when the two are the same.
            Text {
                text: root.titleLeads ? root.notification?.summary ?? "" : root.appLabel
                color: root.titleLeads ? Theme.text : Theme.muted
                font.bold: root.titleLeads
                font.pixelSize: Theme.textSize(root.titleLeads ? 13 : 11)
                textFormat: Text.PlainText
                wrapMode: root.titleLeads ? Text.Wrap : Text.NoWrap
                maximumLineCount: root.titleLeads && root.popup ? 3 : 2147483647
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
            Text {
                visible: root.archived
                text: I18n.tr("notifications.archived")
                color: Theme.muted
                font.pixelSize: Theme.textSize(11)
                font.italic: true
            }
            Text {
                visible: text !== ""
                text: root.age
                color: Theme.muted
                font.pixelSize: Theme.textSize(11)
            }
            // Quiet, and shown on the hovered or focused card only (it keeps its place, so nothing moves);
            // tablet mode has no hover, so there it stays.
            CompactIconButton {
                visible: !root.popup
                implicitWidth: Theme.hit(24)
                implicitHeight: Theme.hit(24)
                iconName: "close"
                iconSize: 14
                normalColor: Theme.muted
                tooltip: I18n.tr("common.delete")
                opacity: hover.hovered || activeFocus || Tablet.active ? 1 : 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: Theme.motionFast
                    }
                }
                onClicked: root.dismiss()
            }
        }
        Text {
            visible: !root.titleLeads
            text: root.notification?.summary ?? ""
            color: Theme.text
            font.bold: true
            font.pixelSize: Theme.textSize(13)
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            maximumLineCount: root.popup ? 3 : 2147483647
            elide: Text.ElideRight
            textFormat: Text.PlainText
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
                    outlined: true
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
