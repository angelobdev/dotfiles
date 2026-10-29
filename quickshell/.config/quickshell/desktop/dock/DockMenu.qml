import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import ".."
import "../components"
import "../services"

// The dock context menu lives in a full-screen layer, like tray menus, so it can grab the keyboard
// and close on any outside click.
PanelWindow {
    id: root
    property string key: ""
    // Asking before closing several windows; reset whenever the menu opens.
    property bool confirming: false
    property point origin: Qt.point(0, 0)
    readonly property var item: Dock.items.find(i => i.key === key) ?? null
    readonly property string label: item ? item.entry?.name || item.appId : ""
    function open(dockItem, anchor) {
        key = dockItem.key;
        confirming = false;
        const window = anchor.QsWindow.window;
        const point = anchor.mapToItem(window.contentItem, anchor.width / 2, 0);
        // The dock is anchored to the bottom of the same screen as this full-screen layer, above the docked
        // on-screen keyboard when it is shown.
        origin = Qt.point(point.x, point.y + (screen.height - Keyboard.reservedOn(screen.name) - window.height));
        // Set first: the keyboard grab of the dock steps aside before this menu takes the keyboard.
        Dock.menuScreen = screen.name;
        visible = true;
        menu.forceActiveFocus();
    }
    // Esc goes back to a dock held by the keyboard; anything else also ends its keyboard mode.
    function dismiss(backToDock) {
        if (!backToDock)
            Dock.endKeyboard(screen.name, false);
        visible = false;
        if (Dock.menuScreen === screen.name)
            Dock.menuScreen = "";
    }
    function closeWindows() {
        for (const toplevel of item?.toplevels ?? [])
            toplevel.wayland?.close();
    }
    function entries() {
        if (!item)
            return [];
        const count = item.toplevels.length;
        if (confirming)
            return [
                {
                    kind: "heading",
                    text: I18n.plural("dock.menu.confirmClose.one", "dock.menu.confirmClose.other", count)
                },
                {
                    text: I18n.tr("dock.menu.cancel"),
                    keepOpen: true,
                    action: () => root.confirming = false
                },
                {
                    text: I18n.tr("dock.menu.close"),
                    destructive: true,
                    action: () => root.closeWindows()
                }
            ];
        const groups = [];
        if (count > 0)
            groups.push([
                {
                    kind: "heading",
                    text: I18n.tr("dock.menu.windows")
                }
            ].concat(item.toplevels.map(t => ({
                        text: t.title || root.label,
                        checked: t.activated,
                        action: () => t.wayland?.activate()
                    }))));
        const actions = item.entry?.actions ?? [];
        if (actions.length > 0)
            groups.push(actions.map(a => ({
                        text: a.name,
                        icon: a.icon ? Quickshell.iconPath(a.icon, true) : "",
                        action: () => a.execute()
                    })));
        const general = [];
        if (item.entry) {
            general.push({
                text: I18n.tr("dock.menu.newWindow"),
                action: () => Dock.launchNew(item)
            });
            const pinned = Dock.isPinned(item.entry.id);
            general.push({
                text: I18n.tr(pinned ? "dock.menu.unpin" : "dock.menu.pin"),
                action: () => pinned ? Dock.unpin(item.entry.id) : Dock.pin(item.entry.id)
            });
        }
        if (count === 1)
            general.push({
                text: I18n.tr("dock.menu.close"),
                destructive: true,
                action: () => root.closeWindows()
            });
        else if (count > 1)
            general.push({
                text: I18n.plural("dock.menu.closeAll.one", "dock.menu.closeAll.other", count),
                destructive: true,
                keepOpen: true,
                action: () => root.confirming = true
            });
        if (general.length > 0)
            groups.push(general);
        let result = [
            {
                kind: "heading",
                text: label
            }
        ];
        for (const group of groups)
            result = result.concat([
                {
                    kind: "separator"
                }
            ], group);
        return result;
    }
    visible: false
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    exclusionMode: ExclusionMode.Ignore
    color: "transparent"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.namespace: "desktop-tray-menu"
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
    // The app quit or lost its last window while its menu was open.
    onItemChanged: if (visible && !item)
        dismiss()
    HyprlandFocusGrab {
        active: root.visible
        windows: [root]
        onCleared: root.dismiss()
    }
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
        onPressed: root.dismiss()
    }
    PopupMenu {
        id: menu
        x: Math.max(6, Math.min(root.origin.x - width / 2, root.width - width - 6))
        y: Math.max(6, root.origin.y - height - 8)
        entries: root.visible ? root.entries() : []
        onTriggered: entry => {
            if (!entry.keepOpen)
                root.dismiss();
        }
        onDismissed: root.dismiss(true)
    }
}
