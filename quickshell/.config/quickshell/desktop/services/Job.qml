import QtQuick
import Quickshell
import Quickshell.Io
import "JobRecord.js" as JobRecord

// One background operation of jobs.py, by name: start() runs it detached (a shell restart or a closed panel does not
// stop it), and its record and log follow it from ~/.local/state/desktop-shell/jobs/NAME.json. finished() fires when a
// run this shell watched ends.
Scope {
    id: root
    required property string name
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/jobs.py"
    readonly property string stateFile: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell/jobs/" + name + ".json"
    property var record: ({})
    property var log: []
    // When start() asked, in seconds: until jobs.py records that run, the file still holds the one before.
    property real requested: 0
    readonly property bool running: record.running === true
    readonly property bool failed: !running && record.finished !== undefined && record.status !== 0 || record.status === -1
    signal finished(int status)
    // command: argv; asRoot: behind one pkexec prompt; title: the notification at the end.
    function start(command, asRoot, title) {
        if (running)
            return;
        requested = Date.now() / 1000;
        record = {
            running: true
        };
        log = [];
        Quickshell.execDetached(["python3", helper, "run", name].concat(asRoot ? ["--root"] : [], title ? ["--title", title] : [], ["--"], command));
    }
    function read() {
        if (!reader.running)
            reader.running = true;
    }
    Process {
        id: reader
        command: ["python3", root.helper, "status", root.name]
        stdout: StdioCollector {
            onStreamFinished: {
                let value = {};
                try {
                    value = JSON.parse(text);
                } catch (failure) {
                    return;
                }
                if (!value || typeof value !== "object")
                    return;
                // Not the record of an earlier run over the one just started (unless it never started).
                if (JobRecord.stale(value, root.requested, Date.now() / 1000))
                    return;
                root.requested = 0;
                root.log = Array.isArray(value.log) ? value.log.filter(line => typeof line === "string") : [];
                const wasRunning = root.running;
                delete value.log;
                root.record = value;
                if (wasRunning && !root.running)
                    root.finished(value.status ?? -1);
            }
        }
    }
    // The log grows while it runs.
    Timer {
        interval: 2000
        repeat: true
        running: root.running
        onTriggered: root.read()
    }
    FileView {
        path: root.stateFile
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.read()
    }
    Component.onCompleted: read()
}
