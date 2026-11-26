import QtQuick
import QtQuick.Layouts
import Quickshell.Widgets
import ".."
import "../services"

// The quick switchers of themes and wallpapers (Super + Ctrl + T, Super + Ctrl + W): a row of large previews with
// the chosen one in the middle and larger, its name under the row and the keys at the foot. Left and Right move,
// Enter (or a click on the middle one) applies; a click on another moves to it. Each switcher fills a card with its
// preview through card, an item with a modelData property.
ColumnLayout {
    id: root
    property var model: []
    // The index applied now, chosen when the switcher opens; -1 when none is.
    property int appliedIndex: -1
    property alias currentIndex: strip.currentIndex
    property string label: ""
    property string hint: ""
    property Component card
    readonly property int cardWidth: 300
    readonly property int cardHeight: Math.round(cardWidth * 10 / 16)
    readonly property Item focusItem: strip
    signal activated(int index)
    function start() {
        strip.currentIndex = Math.max(0, appliedIndex);
        strip.positionViewAtIndex(strip.currentIndex, ListView.Center);
        strip.forceActiveFocus();
    }
    spacing: 16
    ListView {
        id: strip
        Layout.fillWidth: true
        Layout.preferredHeight: root.cardHeight * 1.2 + 24
        orientation: ListView.Horizontal
        clip: true
        spacing: 18
        model: root.model
        keyNavigationEnabled: true
        highlightMoveDuration: Theme.motionNormal
        highlightRangeMode: ListView.StrictlyEnforceRange
        preferredHighlightBegin: (width - root.cardWidth) / 2
        preferredHighlightEnd: (width + root.cardWidth) / 2
        Keys.onReturnPressed: root.activated(currentIndex)
        Keys.onEnterPressed: root.activated(currentIndex)
        delegate: Item {
            id: cell
            required property var modelData
            required property int index
            readonly property bool current: ListView.isCurrentItem
            width: root.cardWidth
            height: strip.height
            ClippingRectangle {
                anchors.centerIn: parent
                width: root.cardWidth
                height: root.cardHeight
                scale: cell.current ? 1.18 : 0.92
                opacity: cell.current ? 1 : 0.6
                radius: Theme.corner(14)
                color: Theme.tile
                border.width: cell.current ? 3 : cell.index === root.appliedIndex ? 2 : 1
                border.color: cell.current ? Theme.accent : cell.index === root.appliedIndex ? Theme.muted : Theme.stroke
                Behavior on scale {
                    NumberAnimation {
                        duration: Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Theme.easeOut
                    }
                }
                Behavior on opacity {
                    NumberAnimation {
                        duration: Theme.motionNormal
                    }
                }
                Loader {
                    anchors.fill: parent
                    sourceComponent: root.card
                    onLoaded: item.modelData = Qt.binding(() => cell.modelData)
                }
            }
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    if (cell.current)
                        root.activated(cell.index);
                    else
                        strip.currentIndex = cell.index;
                }
            }
        }
    }
    Text {
        Layout.alignment: Qt.AlignHCenter
        Layout.maximumWidth: root.width
        text: root.label
        elide: Text.ElideRight
        textFormat: Text.PlainText
        color: Theme.text
        font.family: Theme.font
        font.pixelSize: Theme.textSize(16)
        font.weight: Font.DemiBold
    }
    KeyHints {
        Layout.fillWidth: true
        visible: !Tablet.active
        hints: root.hint
    }
}
