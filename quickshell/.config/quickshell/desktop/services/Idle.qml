pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Singleton {
    id: root
    // The choice is saved, so it survives shell restarts and logins until changed.
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
    // A logind idle inhibitor, which hypridle honours (ignore_systemd_inhibit is off). The Wayland IdleInhibitor
    // of Quickshell crashed the shell whenever it closed with one active (the inhibitor is destroyed after its
    // window). cat reads a pipe from the shell, so the inhibitor goes with the shell even if it is killed.
    Process {
        running: root.keepAwake
        stdinEnabled: true
        command: ["systemd-inhibit", "--what=idle", "--who=Desktop", "--why=" + I18n.tr("idle.keepAwake"), "--mode=block", "cat"]
    }
}
