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
    // The inset of a 16 px icon in a 30 px button, so a label or a group of icons sits as far from its neighbours
    // as a lone icon does.
    leftPadding: Theme.hit(7)
    rightPadding: Theme.hit(7)
    implicitWidth: Math.max(Theme.hit(30), contentItem.implicitWidth + leftPadding + rightPadding)
    font.pixelSize: Theme.textSize(12)
}
