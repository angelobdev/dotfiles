import QtQuick
import "../.."
import "../../services"
import ".."

// What plays: a click plays or pauses, the wheel skips, a right click opens the Control Center.
BarButton {
    id: root
    property var bar
    readonly property var player: Media.player
    readonly property bool shown: Config.barMedia && !!player && (player.trackTitle ?? "") !== ""
    iconName: player?.isPlaying ? "pause" : "play"
    text: player?.trackTitle ?? ""
    textElide: Text.ElideRight
    // The label fills the button and is cut with an ellipsis: centred, it kept its full width and ran
    // over the battery.
    alignLeft: true
    clip: true
    implicitWidth: Math.min(Theme.hit(220), implicitContentWidth + leftPadding + rightPadding)
    tooltip: I18n.tr("media.barTooltip", [player?.trackTitle ?? "", player?.trackArtist || player?.identity || ""])
    onClicked: Media.control("play-pause")
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: ShellState.toggle("controls", root.bar.screen)
    }
    WheelHandler {
        onWheel: event => Media.control(event.angleDelta.y < 0 ? "next" : "previous")
    }
}
