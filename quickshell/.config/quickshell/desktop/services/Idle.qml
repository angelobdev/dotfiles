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
    // Started and stopped here, not bound: one that exits while Keep awake is on (logind restarted, the inhibit
    // refused) starts again, later after each quick failure, instead of the switch saying On with nothing behind it.
    Process {
        id: inhibitor
        stdinEnabled: true
        // Ends with the shell, even a killed one (setpriv: the kernel signals it).
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["systemd-inhibit", "--what=idle", "--who=Desktop", "--why=" + I18n.tr("idle.keepAwake"), "--mode=block", "cat"])
        stderr: SplitParser {
            onRead: line => console.warn("systemd-inhibit:", line)
        }
        onStarted: backoff.started()
        onExited: {
            backoff.ended();
            if (root.keepAwake)
                retry.restart();
        }
    }
    onKeepAwakeChanged: {
        retry.stop();
        inhibitor.running = keepAwake;
    }
    Component.onCompleted: inhibitor.running = keepAwake
    Backoff {
        id: backoff
    }
    Timer {
        id: retry
        interval: backoff.interval
        onTriggered: if (root.keepAwake)
            inhibitor.running = true
    }
}
