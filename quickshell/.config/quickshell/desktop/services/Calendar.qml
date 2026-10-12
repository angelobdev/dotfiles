pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Singleton {
    id: root
    property var events: []
    property var sources: []
    property string error: ""
    property int start: 0
    property int end: 0
    property bool again: false
    readonly property bool busy: process.running
    function load(first, last) {
        start = Math.floor(first.getTime() / 1000);
        end = Math.floor(last.getTime() / 1000);
        if (process.running) { again = true; return; }
        refresh();
    }
    function refresh() {
        if (!start || !end || process.running) return;
        error = "";
        process.command = ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/calendar.py", String(start), String(end), JSON.stringify(Config.calendarSources)];
        process.running = true;
        deadline.restart();
    }
    function forDay(date) {
        const first = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
        const last = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime();
        return events.filter(e => e.start < last && (e.end > first || e.start >= first)).sort((a,b) => Number(b.allDay) - Number(a.allDay) || a.start - b.start);
    }
    function source(uid) { return sources.find(s => s.uid === uid); }
    Process {
        id: process
        stdout: StdioCollector { id: output }
        onExited: (code, status) => {
            deadline.stop();
            if (code === 0) {
                try {
                    const data = JSON.parse(output.text);
                    if (data.error) root.error = data.error;
                    else {
                        // Keep cached entries for unavailable accounts instead of silently losing them.
                        const failed = data.sources.filter(s => s.error).map(s => s.uid);
                        root.events = data.events.concat(root.events.filter(e => failed.includes(e.source)));
                        root.sources = data.sources;
                        root.error = data.sources.filter(s => s.error).map(s => s.name + ": " + s.error).join("\n");
                    }
                } catch(e) { root.error = "Dati calendario non disponibili."; }
            } else if (!root.error) root.error = "Impossibile leggere i calendari degli Account online.";
            if (root.again) { root.again = false; Qt.callLater(root.refresh); }
        }
    }
    Timer {
        id: deadline; interval: 45000
        onTriggered: { root.error = "Il servizio calendari non risponde. Riprova tra poco."; process.running = false; }
    }
    Timer { interval: 60000; repeat: true; running: ShellState.panel === "calendar"; onTriggered: root.refresh() }
}
