import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import Quickshell.Services.Notifications
import ".."
import "../services"
import "NotificationDeck.js" as NotificationDeck

PanelWindow {
    id: root
    screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) || Quickshell.screens[0]
    anchors {
        top: true
        right: true
    }
    // How far a card travels as it arrives or leaves; the window starts that much above the stack, so
    // the top card is not clipped on its way.
    readonly property int travel: 24
    margins {
        top: 54 - root.travel
        right: 12
    }
    readonly property int count: Notices.popups.length
    // Cards fading out: already out of the layout, so the others close the gap under them.
    property var leavingIds: []
    // The pointer, or a tap in tablet mode, holds the stack open: every card stops counting down, and
    // those arriving meanwhile (frozen lists the ones already there) wait, so nothing moves under it.
    property bool expanded: false
    property string openDeck: ""
    property var frozen: null
    property var heights: ({})
    readonly property var decks: NotificationDeck.group(Notices.popups.slice().reverse().filter(n => !leavingIds.includes(n.id) && (frozen === null || frozen.includes(n.id))))
    readonly property var geometry: NotificationDeck.layout(decks, {
        openDeck: openDeck,
        heights: heights,
        fallback: 80,
        gap: 6,
        deckGap: 10
    })
    readonly property real pointerY: pointer.hovered ? pointer.point.position.y : NaN
    implicitWidth: 380
    // Full available height so a deck opens without clipping; the input mask still covers only the stack.
    implicitHeight: (screen?.height ?? 900) - 100
    visible: count > 0 && !Notices.quiet && ShellState.panel === ""
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "desktop-notifications"
    contentItem.clip: true
    mask: Region {
        item: stack
    }
    function hold(deck) {
        if (!expanded)
            frozen = Notices.popups.map(n => n.id);
        expanded = true;
        openDeck = deck;
    }
    function release() {
        expanded = false;
        openDeck = "";
        frozen = null;
    }
    function measure(id, height) {
        if (heights[id] !== height)
            heights = Object.assign({}, heights, {
                [id]: height
            });
    }
    onCountChanged: if (count === 0)
        heights = {}
    onVisibleChanged: if (!visible)
        release()
    // Only the front card opens a deck; moving onto the front card of another one switches.
    onPointerYChanged: {
        if (isNaN(pointerY))
            return;
        const deck = NotificationDeck.deckAt(geometry.rects, pointerY, 6);
        if (deck !== "" || !expanded)
            hold(deck !== "" ? deck : openDeck);
    }
    // Leaving the stack closes it at once; in tablet mode nothing says the finger has left.
    Timer {
        id: collapse
        interval: Tablet.active ? 6000 : 120
        onTriggered: root.release()
    }
    Timer {
        interval: 30000
        running: root.frozen !== null && Notices.popups.some(n => !root.frozen.includes(n.id))
        onTriggered: root.frozen = null
    }
    Item {
        id: stack
        y: root.travel
        width: parent.width
        height: root.geometry.height
        // On the parent of the cards: on a sibling, the cards would take the hover away from it.
        HoverHandler {
            id: pointer
            enabled: !Tablet.active
            onHoveredChanged: {
                if (hovered)
                    collapse.stop();
                else
                    collapse.restart();
            }
        }
        PointHandler {
            enabled: Tablet.active && root.expanded
            onActiveChanged: if (active)
                collapse.restart()
        }
        // Reusing delegates keeps the other toasts (and their countdowns) alive when one leaves.
        Repeater {
            model: ScriptModel {
                values: Notices.popups
                objectProp: "id"
            }
            Item {
                id: card
                required property var modelData
                readonly property int cardId: modelData?.id ?? -1
                readonly property string deckKey: NotificationDeck.groupKey(modelData)
                readonly property var place: root.geometry.places[cardId] ?? null
                // The last place it had: a leaving card fades where it was.
                property var shown: place
                property bool landed: false
                property bool leaving: false
                // Counted by hand: a Timer stopped while a deck is open would start over.
                property real remaining: modelData?.expireTimeout > 0 ? modelData.expireTimeout : 6000
                readonly property bool open: shown?.open ?? false
                function land() {
                    landed = place !== null;
                }
                function leave() {
                    if (leaving)
                        return;
                    leaving = true;
                    root.leavingIds = root.leavingIds.concat(cardId);
                    finish.start();
                }
                onPlaceChanged: if (place) {
                    shown = place;
                    if (!landed)
                        Qt.callLater(land);
                }
                Component.onCompleted: Qt.callLater(land)
                z: leaving ? 0 : shown?.z ?? 0
                y: (shown?.y ?? 0) - (landed && !leaving ? 0 : root.travel)
                width: stack.width
                height: shown?.height ?? 0
                scale: shown?.scale ?? 1
                transformOrigin: Item.Top
                opacity: landed && !leaving ? shown?.opacity ?? 0 : 0
                enabled: (shown?.drawn ?? false) && !leaving
                Behavior on y {
                    NumberAnimation {
                        duration: card.leaving ? Theme.motionFast : Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: card.leaving ? Theme.easeIn : Theme.easeOut
                    }
                }
                Behavior on height {
                    NumberAnimation {
                        duration: Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Theme.easeOut
                    }
                }
                Behavior on scale {
                    NumberAnimation {
                        duration: Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Theme.easeOut
                    }
                }
                Behavior on opacity {
                    NumberAnimation {
                        duration: card.leaving ? Theme.motionFast : Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: card.leaving ? Theme.easeIn : Theme.easeOut
                    }
                }
                Timer {
                    id: finish
                    interval: Math.max(1, Theme.motionFast)
                    // In this order: hiding the popup destroys this delegate.
                    onTriggered: {
                        const leaving = card.cardId;
                        root.leavingIds = root.leavingIds.filter(id => id !== leaving);
                        Notices.hidePopup(leaving);
                    }
                }
                // Retain in the center after the toast timeout; dismiss/close stays explicit.
                Timer {
                    interval: 250
                    repeat: true
                    running: !root.expanded && !card.leaving && card.modelData?.expireTimeout !== 0 && card.modelData?.urgency !== NotificationUrgency.Critical
                    onTriggered: {
                        card.remaining -= interval;
                        if (card.remaining <= 0)
                            card.leave();
                    }
                }
                Notice {
                    width: card.width
                    height: card.height
                    notification: card.modelData
                    popup: true
                    bodyLines: card.open ? 8 : card.shown?.stacked ? 2 : 6
                    contentHidden: !!card.shown && !card.shown.front && !card.shown.open
                    opensDeck: Tablet.active && (card.shown?.stacked ?? false) && !card.open
                    onHidePopup: card.leave()
                    onDeckRequested: {
                        root.hold(card.deckKey);
                        collapse.restart();
                    }
                    onImplicitHeightChanged: root.measure(card.cardId, implicitHeight)
                    Component.onCompleted: root.measure(card.cardId, implicitHeight)
                }
            }
        }
    }
}
