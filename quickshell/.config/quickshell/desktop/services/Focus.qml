pragma Singleton
import QtQuick
import Quickshell
import ".."

// A focus session: Do Not Disturb for a set time, then back to how it was, with a notification. Saved in the
// session state, so a shell restart or a new login inside the session keeps it; turning Do Not Disturb off
// ends it early.
Singleton {
    id: root
    readonly property real until: SessionState.focusUntil
    property real now: Date.now()
    readonly property bool active: until > now
    readonly property int minutesLeft: active ? Math.ceil((until - now) / 60000) : 0

    function start(minutes) {
        const length = Math.max(1, Math.min(240, Math.round(minutes || Config.focusMinutes)));
        const values = {
            focusMinutes: length,
            focusUntil: Date.now() + length * 60000
        };
        if (!active)
            values.focusQuietBefore = Notices.quiet;
        values.quiet = true;
        SessionState.setMany(values);
        now = Date.now();
    }
    function stop(finished) {
        if (until === 0)
            return;
        const length = SessionState.focusMinutes;
        SessionState.setMany({
            focusUntil: 0,
            quiet: SessionState.focusQuietBefore
        });
        if (finished)
            Quickshell.execDetached(["notify-send", "--app-name=" + I18n.tr("focus.title"), "--app-icon=alarm-symbolic", I18n.tr("focus.finished"), I18n.tr("focus.finishedBody", [length])]);
    }
    // IPC and the shortcut: toggle (Config.focusMinutes), start [minutes], stop.
    function request(action, minutes) {
        if (action === "toggle")
            active ? stop(false) : start(minutes);
        else if (action === "start")
            start(minutes);
        else if (action === "stop")
            stop(false);
        else
            return false;
        Osd.showState(active ? "bell-off" : "bell", I18n.tr("focus.title"), active ? I18n.tr("focus.minutesLeft", [minutesLeft]) : I18n.tr("common.off"));
        return true;
    }
    Timer {
        // Every second while a session runs; one that ended while the shell was off ends at start.
        running: root.until > 0
        interval: 1000
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            root.now = Date.now();
            if (root.until > 0 && root.until <= root.now)
                root.stop(true);
        }
    }
    Connections {
        target: Notices
        function onQuietChanged() {
            if (!Notices.quiet && root.active)
                root.stop(false);
        }
    }
}
