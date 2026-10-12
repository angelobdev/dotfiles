pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."
Singleton {
    id: root
    property var monitors: []
    property var otherNames: []
    property string error: ""
    property var pending: ({})
    property var requested: ({})
    property var inFlight: null
    readonly property bool active: ShellState.panel === "controls" && Config.controlCenterModules.includes("brightness")
    readonly property var primary: monitors.find(m => m.name === Config.primaryMonitor) || monitors[0] || null
    readonly property var others: monitors.filter(m => m !== primary)
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/brightness.py"
    // Keep the UI at the user's latest value until the queue is confirmed by a read.
    function displayPercent(monitor) { return monitor ? (requested[monitor.name] ?? monitor.percent ?? 1) : 1; }
    function refresh() {
        if (!reader.running && !writer.running && Object.keys(pending).length === 0) {
            reader.command = ["python3", helper, "read", JSON.stringify(Quickshell.screens.map(s => s.name)), JSON.stringify(Config.brightnessDevices)];
            reader.running = true;
        }
    }
    function setBrightness(monitor, value) {
        if (!monitor?.available) return;
        const percent = Math.max(1, Math.min(100, Math.round(value)));
        requested = Object.assign({}, requested, {[monitor.name]: percent});
        pending = Object.assign({}, pending, {[monitor.name]: {name: monitor.name, backend: monitor.backend, percent: percent}});
        settle.stop();
        // Leading-edge throttle: continuous dragging must never postpone every write.
        if (!throttle.running) { flush(); throttle.start(); }
    }
    function flush() {
        if (reader.running || writer.running) return;
        const names = Object.keys(pending);
        if (names.length === 0) return;
        const next = Object.assign({}, pending);
        inFlight = next[names[0]];
        delete next[names[0]]; pending = next;
        error = ""; writer.failure = "";
        writer.command = ["python3", helper, "set", JSON.stringify(inFlight.backend), String(inFlight.percent)];
        writer.running = true;
    }
    onActiveChanged: if (active) refresh()
    Connections { target: Quickshell; function onScreensChanged() { if (root.active) root.refresh(); } }
    Timer { interval: 3000; repeat: true; running: root.active; onTriggered: root.refresh() }
    Timer { id: throttle; interval: 70; onTriggered: root.flush() }
    Timer { id: settle; interval: 120; onTriggered: root.refresh() }
    Process {
        id: reader
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (Array.isArray(data)) {
                        root.monitors = data;
                        const names = data.filter(m => m.name !== root.primary?.name).map(m => m.name);
                        if (JSON.stringify(names) !== JSON.stringify(root.otherNames)) root.otherNames = names;
                        // An older read must not roll back a newer user request.
                        if (!writer.running && Object.keys(root.pending).length === 0) root.requested = ({});
                    } else root.error = data.error || "Lettura luminosità fallita.";
                } catch (e) { root.error = "Impossibile leggere la luminosità."; }
            }
        }
        onExited: (code, status) => {
            if (code !== 0 && root.error === "") root.error = "Lettura luminosità fallita.";
            if (Object.keys(root.pending).length > 0 && !throttle.running) Qt.callLater(root.flush);
        }
    }
    Process {
        id: writer
        property string failure: ""
        stdout: StdioCollector {
            onStreamFinished: {
                try { const data = JSON.parse(text); if (data.error) writer.failure = data.error; }
                catch (e) { writer.failure = "Impossibile impostare la luminosità."; }
            }
        }
        onExited: (code, status) => {
            if (code !== 0 || failure !== "") {
                root.error = failure || "Modifica luminosità fallita.";
                if (root.inFlight && !root.pending[root.inFlight.name]) {
                    const next = Object.assign({}, root.requested);
                    delete next[root.inFlight.name]; root.requested = next;
                }
            }
            root.inFlight = null;
            if (Object.keys(root.pending).length > 0) {
                if (!throttle.running) Qt.callLater(root.flush);
            } else settle.restart();
        }
    }
}
