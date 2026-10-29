import QtQuick
import "../components"
import "../services"

ActionButton {
    keyboardFocusOnly: true
    normalColor: BarStyle.foreground
    implicitHeight: 30
    iconSize: 16
    topPadding: 0
    bottomPadding: 0
    leftPadding: 4
    rightPadding: 4
    implicitWidth: Math.max(30, contentItem.implicitWidth + leftPadding + rightPadding)
    font.pixelSize: 12
}
