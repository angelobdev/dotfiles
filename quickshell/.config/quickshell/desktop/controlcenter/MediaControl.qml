import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import ".."
import "../components"
import "../services"

ControlTile {
    id: root
    readonly property var player: Media.player
    property bool expanded: false
    property real position: 0
    implicitHeight: content.implicitHeight + 24
    function updatePosition() {
        if (!seek.pressed)
            position = player?.positionSupported ? Math.max(0, player.position) : 0;
    }
    function time(seconds) {
        const s = Math.max(0, Math.floor(seconds || 0));
        return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
    }
    onPlayerChanged: updatePosition()
    Connections {
        target: root.player
        function onPositionChanged() {
            root.updatePosition();
        }
        function onTrackChanged() {
            root.updatePosition();
        }
    }
    Timer {
        interval: 500
        repeat: true
        running: ShellState.panel === "controls" && !!root.player?.isPlaying
        onTriggered: root.updatePosition()
    }
    ColumnLayout {
        id: content
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            margins: 12
        }
        spacing: 6
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: root.player?.trackTitle || root.player?.identity || I18n.tr("media.title")
                    color: Theme.text
                    font.weight: Font.DemiBold
                    textFormat: Text.PlainText
                }
                Text {
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    text: root.player ? [root.player.trackArtist, root.player.identity].filter(Boolean).join(" · ") : I18n.tr("media.unavailable")
                    color: Theme.muted
                    font.pixelSize: 11
                    textFormat: Text.PlainText
                }
            }
            CompactIconButton {
                visible: Media.players.length > 1
                iconName: root.expanded ? "chevron-up" : "chevron-down"
                tooltip: I18n.tr("media.choosePlayer")
                onClicked: root.expanded = !root.expanded
            }
        }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            PanelIconButton {
                iconName: "previous"
                tooltip: I18n.tr("media.previous")
                enabled: root.player?.canGoPrevious ?? false
                onClicked: root.player.previous()
            }
            ActionButton {
                iconName: root.player?.isPlaying ? "pause" : "play"
                tooltip: root.player?.isPlaying ? I18n.tr("media.pause") : I18n.tr("media.play")
                enabled: root.player?.canTogglePlaying ?? false
                onClicked: root.player.togglePlaying()
            }
            PanelIconButton {
                iconName: "next"
                tooltip: I18n.tr("media.next")
                enabled: root.player?.canGoNext ?? false
                onClicked: root.player.next()
            }
        }
        ControlSlider {
            id: seek
            Layout.fillWidth: true
            visible: !!root.player?.lengthSupported && root.player.length > 0
            enabled: !!root.player?.canSeek && !!root.player?.positionSupported
            to: Math.max(1, root.player?.length ?? 1)
            value: root.position
            Accessible.name: I18n.tr("media.position")
            onMoved: root.position = value
            onPressedChanged: if (!pressed && enabled && root.player)
                root.player.position = value
            Keys.onReleased: event => {
                if (enabled && root.player && [Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End].includes(event.key))
                    root.player.position = value;
            }
        }
        Text {
            visible: seek.visible
            text: root.time(root.position) + " / " + root.time(root.player?.length)
            color: Theme.muted
            font.pixelSize: 10
        }
        ColumnLayout {
            visible: root.expanded && Media.players.length > 1
            Layout.fillWidth: true
            Repeater {
                model: Media.players
                ActionButton {
                    required property var modelData
                    Layout.fillWidth: true
                    alignLeft: true
                    text: modelData.identity
                    highlighted: root.player === modelData
                    onClicked: Media.select(modelData.dbusName)
                }
            }
        }
    }
}
