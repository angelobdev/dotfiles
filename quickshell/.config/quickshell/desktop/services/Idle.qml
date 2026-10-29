pragma Singleton
import QtQuick
import Quickshell
import ".."

Singleton {
    // Inhibitors live on the mapped bars, so closing a panel does not release them. The choice is saved,
    // so it survives shell restarts and logins until changed.
    readonly property bool keepAwake: SessionState.keepAwake
    function setKeepAwake(value) {
        SessionState.set("keepAwake", value);
    }
    // IPC and the shortcut: "toggle", "on" or "off", with an OSD of the new state.
    function request(action) {
        if (!["toggle", "on", "off"].includes(action))
            return false;
        setKeepAwake(action === "toggle" ? !keepAwake : action === "on");
        Osd.showState("coffee", I18n.tr("idle.keepAwake"), I18n.tr(keepAwake ? "common.on" : "common.off"));
        return true;
    }
}
