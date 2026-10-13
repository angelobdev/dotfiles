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
    margins.bottom: Math.max(0, Config.osdBottomMargin)
    implicitWidth: Math.min(Math.max(240, Config.osdWidth), (screen?.width ?? 800) - 24)
    implicitHeight: 96
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
        anchors.fill: parent
        radius: Theme.radius
        color: Theme.surface
        border.width: 1
        border.color: Theme.stroke
        opacity: Osd.visible ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: 140
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
                        text: Osd.muted ? I18n.tr("audio.muted") : Osd.percent + "%"
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: 12
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
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
                                duration: 80
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
