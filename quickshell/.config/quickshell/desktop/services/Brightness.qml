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
    readonly property bool active: ShellState.panel === "controls" && Config.controlCenterModules.includes("brightness")
    readonly property var primary: monitors.find(m => m.name === Config.primaryMonitor) || monitors[0] || null
    readonly property var others: monitors.filter(m => m !== primary)
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/brightness.py"
    function refresh() {
        if (!reader.running && !writer.running && Object.keys(pending).length === 0) {
            reader.command = ["python3", helper, "read", JSON.stringify(Quickshell.screens.map(s => s.name)), JSON.stringify(Config.brightnessDevices)];
            reader.running = true;
        }
    }
    function setBrightness(monitor, value) {
        if (!monitor?.available) return;
        const next = Object.assign({}, pending);
        next[monitor.name] = {backend: monitor.backend, percent: Math.max(1, Math.min(100, Math.round(value)))};
        pending = next;
        debounce.restart();
    }
    function flush() {
        if (reader.running || writer.running) return;
        const names = Object.keys(pending);
        if (names.length === 0) { if (active) refresh(); return; }
        const next = Object.assign({}, pending);
        const request = next[names[0]];
        delete next[names[0]]; pending = next;
        error = "";
        writer.command = ["python3", helper, "set", JSON.stringify(request.backend), String(request.percent)];
        writer.running = true;
    }
    onActiveChanged: if (active) refresh()
    Connections { target: Quickshell; function onScreensChanged() { if (root.active) root.refresh(); } }
    Timer { interval: 3000; repeat: true; running: root.active; onTriggered: root.refresh() }
    Timer { id: debounce; interval: 180; onTriggered: root.flush() }
    Process {
        id: reader
        stdout: StdioCollector {
            onStreamFinished: {
                try { const data = JSON.parse(text); if (Array.isArray(data)) {
                        root.monitors = data;
                        const names = data.filter(m => m.name !== root.primary?.name).map(m => m.name);
                        if (JSON.stringify(names) !== JSON.stringify(root.otherNames)) root.otherNames = names;
                    } else root.error = data.error || "Lettura luminosità fallita."; }
                catch (e) { root.error = "Impossibile leggere la luminosità."; }
            }
        }
        onExited: (code, status) => { if (code !== 0 && root.error === "") root.error = "Lettura luminosità fallita."; if (Object.keys(root.pending).length > 0) debounce.restart(); }
    }
    Process {
        id: writer
        stdout: StdioCollector { onStreamFinished: { try { const data = JSON.parse(text); if (data.error) root.error = data.error; } catch (e) { root.error = "Impossibile impostare la luminosità."; } } }
        onExited: (code, status) => { if (code !== 0 && root.error === "") root.error = "Modifica luminosità fallita."; if (Object.keys(root.pending).length > 0) debounce.restart(); else if (root.active) root.refresh(); }
    }
}
