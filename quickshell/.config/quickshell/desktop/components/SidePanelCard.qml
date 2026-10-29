import QtQuick
import ".."

Card {
    anchors {
        top: parent.top
        right: parent.right
        // 20 px below the bar, whose height grows in tablet mode.
        topMargin: Theme.barHeight + 20
        rightMargin: 12
    }
    width: Math.min(Config.controlCenterWidth, parent.width - 24)
    height: Math.min(560, parent.height - 76)
}
