pragma Singleton
import QtQuick
import Quickshell
import ".."
import "ReminderTime.js" as ReminderTime

// Timed reminders ("in 20 minutes: tea"), from the Reminders dialog (Super + Ctrl + M) or desktop-shell remind. Kept
// in session.json, so a restart or the next login keeps them; delivered as a notification that gets through Do Not
// Disturb (Notices, by its x-desktop-reminder hint) and stays until dismissed. One due while logged out comes at the
// next start and says when it was due.
Singleton {
    id: root
    readonly property var list: (Array.isArray(SessionState.reminders) ? SessionState.reminders : []).filter(entry => entry && typeof entry.at === "number" && typeof entry.text === "string").sort((a, b) => a.at - b.at)
    readonly property var next: list.length > 0 ? list[0] : null
    // Now, a minute at a time, for what the bar and the dialog count down.
    property real now: Date.now()
    readonly property real started: Date.now()
    function minutesLeft(entry) {
        return ReminderTime.minutesLeft(entry.at, now);
    }
    // when: minutes, hours and minutes or a time of day (ReminderTime.due). False when it says no time.
    function add(when, text) {
        const at = ReminderTime.due(when, Date.now());
        if (!Number.isFinite(at))
            return false;
        SessionState.set("reminders", list.concat({
            id: Date.now().toString(36) + Math.floor(Math.random() * 1296).toString(36),
            at: at,
            text: String(text ?? "").trim().slice(0, 200)
        }));
        now = Date.now();
        return true;
    }
    function remove(id) {
        SessionState.set("reminders", list.filter(entry => entry.id !== id));
    }
    function clear() {
        SessionState.set("reminders", []);
    }
    function deliver() {
        const time = Date.now();
        const due = list.filter(entry => entry.at <= time);
        if (due.length > 0)
            SessionState.set("reminders", list.filter(entry => entry.at > time));
        for (const entry of due) {
            const missed = entry.at < started - 60000;
            Quickshell.execDetached(["notify-send", "--app-name=" + I18n.tr("reminders.title"), "--app-icon=alarm-symbolic", "--urgency=critical", "--hint=string:x-desktop-reminder:1", entry.text || I18n.tr("reminders.untitled"), missed ? I18n.tr("reminders.missed", [I18n.locale.toString(new Date(entry.at), I18n.timeFormat)]) : I18n.tr("reminders.now")]);
        }
        schedule();
    }
    // The next one, an hour at most ahead: a suspend in between is caught up at the next wake of the timer.
    function schedule() {
        timer.stop();
        if (!next)
            return;
        timer.interval = Math.max(1000, Math.min(next.at - Date.now(), 3600000));
        timer.start();
    }
    // desktop-shell remind: add WHEN TEXT, list (JSON), clear.
    function request(action, when, text) {
        if (action === "add")
            return add(when, text) ? "ok" : "";
        if (action === "clear") {
            clear();
            return "ok";
        }
        if (action === "list")
            return JSON.stringify(list);
        return "";
    }
    onNextChanged: schedule()
    Component.onCompleted: deliver()
    Timer {
        id: timer
        onTriggered: root.deliver()
    }
    Timer {
        interval: 30000
        repeat: true
        running: root.list.length > 0
        onTriggered: {
            root.now = Date.now();
            // After a suspend the one-shot timer may be late: what is due goes now.
            if (root.next && root.next.at <= root.now)
                root.deliver();
        }
    }
}
