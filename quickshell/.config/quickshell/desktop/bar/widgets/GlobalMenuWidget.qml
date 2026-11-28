import QtQuick
import QtQuick.Layouts
import Quickshell
import "../.."
import "../../services"
import ".."

// The global menu, after Oma Top Menu: the menu of the window of this monitor (services/GlobalMenu.qml). An app with
// a menu of its own shows its icon and its menus (File, Edit, View…, read from the app); one without gets its name
// and a generic menu (File, Edit, View, Window, Help) or nothing (Config.globalMenuFallback). Each opens below it
// (bar/GlobalMenuWindow.qml); a right click opens the options and the apps to start under X11
// (panels/GlobalMenuPanel.qml). Hidden on a monitor without a window.
RowLayout {
    id: root
    property var bar
    readonly property var window: GlobalMenu.target(bar.screen.name)
    readonly property var appMenu: GlobalMenu.menuOf(window)?.menu ?? []
    readonly property bool own: appMenu.length > 0
    readonly property bool generic: !own && Config.globalMenuFallback === "generic"
    // The menus in order: {kind, label, id}: "app-menu" for one of the app (its id), else the generic ones.
    readonly property var menus: own ? appMenu.map(menu => ({
                kind: "app-menu",
                id: menu.id,
                label: menu.label
            })) : generic ? [
        {
            kind: "app",
            label: GlobalMenu.nameOf(window)
        },
        {
            kind: "file",
            label: I18n.tr("globalMenu.generic.file")
        },
        {
            kind: "edit",
            label: I18n.tr("globalMenu.generic.edit")
        },
        {
            kind: "view",
            label: I18n.tr("globalMenu.generic.view")
        },
        {
            kind: "window",
            label: I18n.tr("globalMenu.window")
        },
        {
            kind: "help",
            label: I18n.tr("globalMenu.generic.help")
        }
    ] : []
    readonly property bool shown: GlobalMenu.placed && window !== null && menus.length > 0
    spacing: 0
    function anchorFor(index) {
        return buttons.itemAt(index) ?? root;
    }
    Image {
        visible: Config.globalMenuIcon && source.toString() !== ""
        Layout.leftMargin: 6
        Layout.rightMargin: 2
        Layout.preferredWidth: Theme.hit(18)
        Layout.preferredHeight: Theme.hit(18)
        source: {
            const icon = GlobalMenu.entryOf(root.window)?.icon ?? "";
            return icon !== "" ? Quickshell.iconPath(icon, true) : "";
        }
        sourceSize: Qt.size(36, 36)
        fillMode: Image.PreserveAspectFit
    }
    Repeater {
        id: buttons
        model: root.menus
        BarButton {
            required property var modelData
            required property int index
            text: modelData.label
            font.weight: modelData.kind === "app" ? Font.DemiBold : Font.Normal
            onClicked: root.bar.globalMenu.popup(root, index)
        }
    }
    // A right click on the strip: its options.
    TapHandler {
        acceptedButtons: Qt.RightButton
        onTapped: ShellState.open("globalmenu")
    }
}
