import QtQuick
import ".."
Card {
    anchors { top: parent.top; right: parent.right; topMargin: 58; rightMargin: 12 }
    width: Math.min(Config.controlCenterWidth, parent.width - 24)
    height: Math.min(560, parent.height - 76)
}
