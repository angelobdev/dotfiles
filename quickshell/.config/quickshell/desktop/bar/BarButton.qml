import QtQuick
import ".."
import "../components"
import "../services"

ActionButton {
    keyboardFocusOnly: true
    normalColor: BarStyle.foreground
    implicitHeight: Theme.hit(30)
    iconSize: Theme.hit(16)
    topPadding: 0
    bottomPadding: 0
    leftPadding: 4
    rightPadding: 4
    implicitWidth: Math.max(Theme.hit(30), contentItem.implicitWidth + leftPadding + rightPadding)
    font.pixelSize: 12
}
