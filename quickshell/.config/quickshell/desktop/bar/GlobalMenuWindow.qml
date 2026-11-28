import QtQuick
import Quickshell
import Quickshell.Hyprland
import ".."
import "../components"
import "../services"

// A menu of the global menu (bar/widgets/GlobalMenuWidget.qml), below its name on the bar:
// - a menu of the app, read from it when it opens (services/GlobalMenu.qml); a submenu opens in the same menu, under
//   a row that goes back; a menu the app fills only once open (Firefox) shows its entries a moment later;
// - the generic menus of an app without its own: its name (a new window, its desktop actions, close, quit), File,
//   Edit (keys sent to the window: undo, cut, copy, paste, select all), View, Window and Help.
// ← and → move to the menu beside it on the bar, as on a menu bar.
MenuLayer {
    id: root
    property point origin: Qt.point(0, 0)
    property var entries: []
    // The app menus opened, outermost first: [{id, label}] (empty for a generic menu).
    property var stack: []
    // The widget: its window, its menus and where each one opens.
    property var owner: null
    property var window: null
    property int topIndex: -1
    onDismissRequested: dismiss()
    function popup(widget, index) {
        owner = widget;
        window = widget.window;
        topIndex = index;
        const top = widget.menus[index];
        const anchor = widget.anchorFor(index);
        origin = anchor.mapToItem(anchor.QsWindow.window.contentItem, 0, widget.bar.stripHeight);
        visible = true;
        if (top.kind === "app-menu") {
            stack = [top];
            entries = [loadingEntry()];
            GlobalMenu.open(window, top.id);
        } else {
            stack = [];
            entries = genericEntries(top.kind);
        }
        Qt.callLater(() => menu.forceActiveFocus());
    }
    function dismiss() {
        visible = false;
        stack = [];
    }
    function loadingEntry() {
        return {
            kind: "heading",
            text: I18n.tr("globalMenu.loading")
        };
    }
    // The keys of a bind of the Hyprland config, by its description, as "Super+F".
    function keys(bind) {
        return Commands.keysOf({
            bind: bind
        }).join("+");
    }
    function dispatch(command) {
        Hyprland.dispatch(command);
    }
    function target() {
        return "window = \"address:" + window.address + "\"";
    }
    // A key combination for the window itself, as if typed in it.
    function sendKeys(mods, key) {
        dispatch("hl.dsp.send_shortcut({ mods = \"" + mods + "\", key = \"" + key + "\", " + target() + " })");
    }
    function keyEntry(labelKey, mods, key, hint) {
        return {
            text: I18n.tr(labelKey),
            hint: hint,
            action: () => root.sendKeys(mods, key)
        };
    }
    function separator() {
        return {
            kind: "separator"
        };
    }
    function closeEntry() {
        return {
            text: I18n.tr("windowMenu.close"),
            hint: keys("Close window"),
            action: () => root.dispatch("hl.dsp.window.close({ " + root.target() + " })")
        };
    }
    function quitEntry() {
        return {
            text: I18n.tr("globalMenu.generic.quit", [GlobalMenu.nameOf(window)]),
            destructive: true,
            action: () => GlobalMenu.closeAll(root.window)
        };
    }
    function genericEntries(kind) {
        const app = GlobalMenu.entryOf(window);
        const newWindow = app ? [
            {
                text: I18n.tr("globalMenu.newWindow"),
                action: () => app.execute()
            }
        ] : [];
        switch (kind) {
        case "app":
            return newWindow.concat((app?.actions ?? []).map(action => ({
                        text: action.name,
                        action: () => action.execute()
                    }))).concat(app ? [separator()] : []).concat([closeEntry(), quitEntry()]);
        case "file":
            return newWindow.concat(app ? [separator()] : []).concat([closeEntry(), quitEntry()]);
        case "edit":
            return [keyEntry("globalMenu.generic.undo", "CTRL", "z", "Ctrl+Z"), keyEntry("globalMenu.generic.redo", "CTRL SHIFT", "z", "Ctrl+Shift+Z"), separator(), keyEntry("globalMenu.generic.cut", "CTRL", "x", "Ctrl+X"), keyEntry("globalMenu.generic.copy", "CTRL", "c", "Ctrl+C"), keyEntry("globalMenu.generic.paste", "CTRL", "v", "Ctrl+V"), separator(), keyEntry("globalMenu.generic.selectAll", "CTRL", "a", "Ctrl+A")];
        case "view":
            return [
                {
                    text: I18n.tr("windowMenu.floating"),
                    checked: window.floating,
                    hint: keys("Toggle floating window"),
                    action: () => root.dispatch("hl.dsp.window.float({ action = \"toggle\", " + root.target() + " })")
                },
                {
                    text: I18n.tr("windowMenu.fullscreen"),
                    hint: keys("Fullscreen"),
                    action: () => root.dispatch("hl.dsp.window.fullscreen({ " + root.target() + " })")
                },
                {
                    text: I18n.tr("commands.windows.maximize"),
                    hint: keys("Maximize window"),
                    action: () => root.dispatch("hl.dsp.window.fullscreen({ mode = \"maximized\", " + root.target() + " })")
                },
                {
                    text: I18n.tr("commands.windows.popOut"),
                    hint: keys("Pop window out"),
                    action: () => Quickshell.execDetached(["hyprctl", "eval", "desktop_window_trick(\"popOut\")"])
                },
                {
                    text: I18n.tr("commands.windows.transparency"),
                    hint: keys("Window transparency"),
                    action: () => Quickshell.execDetached(["hyprctl", "eval", "desktop_window_trick(\"transparency\")"])
                }
            ];
        case "window":
            return [
                {
                    text: I18n.tr("windowMenu.movePrevious"),
                    action: () => root.dispatch("hl.dsp.window.move({ workspace = \"r-1\", " + root.target() + " })")
                },
                {
                    text: I18n.tr("windowMenu.moveNext"),
                    action: () => root.dispatch("hl.dsp.window.move({ workspace = \"r+1\", " + root.target() + " })")
                },
                separator(),
                ...[["left", "directions.left"], ["right", "directions.right"], ["up", "directions.up"], ["down", "directions.down"]].map(direction => ({
                        text: I18n.tr("bindings.moveDirection", [I18n.tr(direction[1])]),
                        hint: keys("Move " + direction[0]),
                        action: () => root.dispatch("hl.dsp.window.move({ direction = \"" + direction[0] + "\", " + root.target() + " })")
                    })),
                separator(),
                closeEntry()];
        case "help":
            return [
                {
                    text: I18n.tr("commands.tools.shortcuts"),
                    hint: keys("Hints · Keyboard shortcuts"),
                    action: () => ShellState.open("hints")
                },
                {
                    text: I18n.tr("globalMenu.generic.commands"),
                    hint: keys("Applications"),
                    action: () => ShellState.open("launcher")
                }
            ];
        }
        return [];
    }
    function enter(item) {
        stack = stack.concat([item]);
        entries = [loadingEntry()];
        GlobalMenu.open(window, item.id);
    }
    function back() {
        if (stack.length < 2)
            return false;
        stack = stack.slice(0, -1);
        entries = [loadingEntry()];
        GlobalMenu.open(window, stack[stack.length - 1].id);
        return true;
    }
    function run(item) {
        const window = root.window;
        dismiss();
        GlobalMenu.click(window, item.id);
    }
    // The menu beside this one on the bar, wrapping round.
    function step(direction) {
        const count = owner ? owner.menus.length : 0;
        if (count === 0)
            return;
        popup(owner, (topIndex + direction + count) % count);
    }
    Connections {
        target: GlobalMenu
        function onOpened(address, id, items) {
            const current = root.stack[root.stack.length - 1];
            if (!root.visible || !current || !root.window || address !== root.window.address || current.id !== id)
                return;
            // An app that fills the menu only once open answers twice: empty first, then with its entries.
            if (items.length === 0 && root.entries.length === 1 && root.entries[0].kind === "heading")
                return;
            const rows = items.map(item => item.kind === "separator" ? {
                    kind: "separator"
                } : {
                    text: item.label,
                    hint: item.shortcut ?? "",
                    enabled: item.enabled,
                    checked: item.checked,
                    submenu: !!item.submenu,
                    keepOpen: !!item.submenu,
                    action: () => item.submenu ? root.enter(item) : root.run(item)
                });
            // Inside a submenu its first row goes back to the menu it came from.
            root.entries = (root.stack.length > 1 ? [{
                        text: "‹ " + root.stack[root.stack.length - 2].label,
                        keepOpen: true,
                        action: () => root.back()
                    }, {
                        kind: "heading",
                        text: current.label
                    }] : []).concat(rows.length > 0 ? rows : [{
                        kind: "heading",
                        text: I18n.tr("globalMenu.empty")
                    }]);
        }
        function onTargetsChanged() {
            // Another window on this monitor: its menus are not these.
            if (root.visible && root.owner && root.owner.window?.address !== root.window?.address)
                root.dismiss();
        }
    }
    PopupMenu {
        id: menu
        menuWidth: 300
        x: root.clampX(root.origin.x, width)
        y: root.clampY(root.origin.y, height)
        entries: root.visible ? root.entries : []
        onTriggered: entry => {
            if (!entry.keepOpen && root.visible)
                root.dismiss();
        }
        onDismissed: root.dismiss()
        onSideways: direction => {
            if (direction < 0 && root.back())
                return;
            root.step(direction);
        }
    }
}
