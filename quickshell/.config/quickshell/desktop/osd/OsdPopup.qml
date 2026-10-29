import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import ".."
import "../components"
import "../services"

PanelWindow {
    id: root
    screen: Osd.targetScreen || Quickshell.screens[0]
    anchors.bottom: true
    // 8 px of room below the card for its rise; the card itself stays where the margin puts it.
    margins.bottom: Math.max(0, Config.osdBottomMargin - 8)
    implicitWidth: Math.min(Math.max(240, Config.osdWidth), (screen?.width ?? 800) - 24)
    implicitHeight: 104
    color: "transparent"
    visible: Osd.visible || card.opacity > 0
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "desktop-osd"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
    // An empty input region lets pointer events reach the application underneath.
    mask: Region {}

    Rectangle {
        id: card
        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
        }
        height: 96
        radius: Theme.radius
        color: Theme.surface
        border.width: Theme.frameWidth
        border.color: Theme.frameInactive
        opacity: Osd.visible ? 1 : 0
        transform: Translate {
            y: 8 * (1 - card.opacity)
        }
        Behavior on opacity {
            NumberAnimation {
                duration: Osd.visible ? Theme.motionFast : Theme.motionNormal
                easing.type: Easing.BezierSpline
                easing.bezierCurve: Osd.visible ? Theme.easeOut : Theme.easeIn
            }
        }
        RowLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 14
            Icon {
                name: Osd.iconName
                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                color: Osd.muted ? Theme.muted : Theme.text
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 7
                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: Osd.title
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: 13
                        font.weight: Font.DemiBold
                        Layout.fillWidth: true
                    }
                    Text {
                        visible: Osd.kind !== "state"
                        text: Osd.muted ? I18n.tr("audio.muted") : Osd.percent + "%"
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: 12
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    visible: Osd.kind !== "state"
                    implicitHeight: 6
                    radius: 3
                    color: Theme.raised
                    Rectangle {
                        width: parent.width * (Osd.muted ? 0 : Math.min(100, Osd.percent) / 100)
                        height: parent.height
                        radius: parent.radius
                        color: Theme.accent
                        Behavior on width {
                            NumberAnimation {
                                duration: Config.reduceMotion ? 0 : 80
                            }
                        }
                    }
                }
                Text {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                    text: Osd.detail
                    textFormat: Text.PlainText
                    elide: Text.ElideRight
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: 10
                }
            }
        }
    }
}
