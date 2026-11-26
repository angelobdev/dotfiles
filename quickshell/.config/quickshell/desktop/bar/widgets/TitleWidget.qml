import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import "../.."
import "../../services"
import ".."

// The active window: its title, or on a narrow bar and in tablet mode the icon of its app. Both open the
// window menu.
RowLayout {
    id: root
    property var bar
    property bool shown: true
    // The title takes the room its section has left, and is cut with an ellipsis.
    readonly property bool fills: true
    // Where the window menu opens when the shell is asked for it (desktop-shell window-menu).
    readonly property Item anchorItem: windowButton.visible ? windowButton : windowTitle
    spacing: 5
    Component.onCompleted: root.bar.titleWidget = root
    Component.onDestruction: {
        if (root.bar && root.bar.titleWidget === root)
            root.bar.titleWidget = null;
    }
    // In tablet mode, and on a narrow bar where the title does not fit, the icon of the active app sits
    // before the title and opens the same menu with a tap.
    BarButton {
        id: windowButton
        visible: (root.bar.width <= 1100 || Tablet.active) && Hyprland.activeToplevel !== null
        iconSource: Quickshell.iconPath(DesktopEntries.heuristicLookup(Hyprland.activeToplevel?.wayland?.appId ?? "")?.icon ?? "", "application-x-executable")
        tooltip: Hyprland.activeToplevel?.title ?? ""
        onClicked: root.bar.windowMenu.popup(this, 0, root.bar.stripHeight)
        Accessible.name: I18n.tr("windowMenu.title")
    }
    Text {
        id: windowTitle
        Layout.fillWidth: true
        Layout.minimumWidth: 0
        Layout.leftMargin: 12
        text: Hyprland.activeToplevel?.title ?? I18n.tr("bar.desktop")
        elide: Text.ElideRight
        textFormat: Text.PlainText
        color: BarStyle.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        visible: root.bar.width > 1100
        // The window menu: right click, or a long press for touch. Only the title itself, so a double
        // click on the empty bar beside it still switches the bar style.
        MouseArea {
            width: Math.min(parent.width, parent.paintedWidth)
            height: parent.height
            enabled: Hyprland.activeToplevel !== null
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            pressAndHoldInterval: 500
            onPressAndHold: root.bar.windowMenu.popup(windowTitle, 0, root.bar.stripHeight)
            onClicked: mouse => {
                if (mouse.button === Qt.RightButton)
                    root.bar.windowMenu.popup(windowTitle, mouse.x, root.bar.stripHeight);
            }
        }
    }
}
