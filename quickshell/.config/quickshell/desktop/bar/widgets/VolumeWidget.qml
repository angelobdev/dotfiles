import QtQuick
import "../.."
import "../../services"
import ".."

// The output volume: the wheel changes it, a click opens the Sound panel, a middle click mutes.
BarButton {
    id: root
    property var bar
    property bool shown: true
    iconName: Audio.muted ? "volume-muted" : Audio.volume < 50 ? "volume-low" : "volume-high"
    text: Audio.muted ? "" : Audio.volume + "%"
    tooltip: I18n.tr("bar.widgets.volume.tooltip")
    onClicked: ShellState.toggle("audio", root.bar.screen)
    TapHandler {
        acceptedButtons: Qt.MiddleButton
        onTapped: Audio.toggleMute()
    }
    WheelHandler {
        onWheel: event => Audio.setVolume((Audio.volume + (event.angleDelta.y > 0 ? 5 : -5)) / 100)
    }
}
