pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"
import ".."

// Privacy: microphone, camera and screen sharing in use, in the accent colour; the tooltip names the apps.
BarButton {
    id: root
    property var bar
    readonly property bool shown: Privacy.active
    implicitWidth: privacyIcons.implicitWidth + leftPadding + rightPadding
    tooltip: [Privacy.microphone ? I18n.tr("privacy.microphone", [Privacy.microphoneApps.join(", ") || I18n.tr("privacy.unknownApp")]) : "", Privacy.camera ? I18n.tr("privacy.camera", [Privacy.cameraApps.join(", ") || I18n.tr("privacy.unknownApp")]) : "", Privacy.sharing ? I18n.tr("privacy.sharing") : ""].filter(line => line !== "").join("\n")
    Accessible.name: I18n.tr("privacy.title")
    contentItem: RowLayout {
        id: privacyIcons
        spacing: 4
        Repeater {
            // While the bar is edited and nothing is in use, the microphone stands in for the widget.
            model: Privacy.active ? [Privacy.microphone ? "microphone" : "", Privacy.camera ? "camera" : "", Privacy.sharing ? "monitor" : ""].filter(name => name !== "") : ["microphone"]
            Icon {
                required property string modelData
                name: modelData
                color: Theme.accent
                Layout.preferredWidth: Theme.hit(16)
                Layout.preferredHeight: Theme.hit(16)
            }
        }
    }
}
