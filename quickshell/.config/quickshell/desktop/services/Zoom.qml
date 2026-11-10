pragma Singleton
import QtQuick
import Quickshell
import ".."

// Screen zoom around the pointer (Hyprland cursor:zoom_factor), in steps of a quarter, from 100% to 800%.
// A config reload sets it back to 100%, and so does reset.
Singleton {
    id: root
    property real factor: 1
    function set(value) {
        factor = Math.round(Math.max(1, Math.min(8, value)) * 100) / 100;
        // Through eval: Hyprland.dispatch wraps its text in hl.dispatch(), which refuses hl.config (not a dispatcher).
        Quickshell.execDetached(["hyprctl", "eval", "hl.config({ cursor = { zoom_factor = " + factor + " } })"]);
        Osd.showState("zoom", I18n.tr("zoom.title"), Math.round(factor * 100) + "%");
    }
    // IPC, the shortcuts and the assist button: in, out, reset, toggle (100% and 200%).
    function request(action) {
        if (action === "in")
            set(factor * 1.25);
        else if (action === "out")
            set(factor / 1.25);
        else if (action === "reset")
            set(1);
        else if (action === "toggle")
            set(factor > 1 ? 1 : 2);
        else
            return false;
        return true;
    }
}
