import QtQuick
import "../.."
import "../../services"
import ".."

BarButton {
    id: root
    property var bar
    readonly property bool shown: Recording.running
    iconName: "record"
    destructive: true
    text: Recording.elapsed
    tooltip: I18n.tr("recording.barTooltip")
    onClicked: Recording.stop()
}
