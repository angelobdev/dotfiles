pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Singleton {
    id: root
    readonly property bool running: recorder.running
    property bool stopping: false
    readonly property bool selecting: selection.running || selectDelay.running
    property string output: ""
    property string audio: "none"
    property string path: ""
    property string error: ""
    property int seconds: 0
    readonly property string elapsed: Math.floor(seconds / 60) + ":" + String(seconds % 60).padStart(2, "0")
    function start(monitor, area, audioMode) {
        if (running || selecting)
            return;
        output = monitor;
        audio = audioMode;
        error = "";
        path = "";
        seconds = 0;
        ShellState.close();
        if (area)
            selectDelay.start();
        else
            record("");
    }
    function record(geometry) {
        recorder.command = ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/recording.py", "--output", output, "--audio", audio, "--codec", Config.recordingCodec, "--fps", String(Config.recordingFramerate)].concat(geometry ? ["--geometry", geometry] : []);
        recorder.running = true;
    }
    function stop() {
        if (!running || stopping)
            return;
        stopping = true;
        recorder.signal(15);
    }
    Timer {
        id: selectDelay
        interval: 180
        onTriggered: selection.running = true
    }
    Timer {
        interval: 1000
        running: root.running && !root.stopping
        repeat: true
        onTriggered: ++root.seconds
    }
    Process {
        id: selection
        // Restrict selection to a single output; wf-recorder cannot span monitors.
        command: ["slurp", "-f", "%o|%x,%y %wx%h"]
        stdout: StdioCollector {
            id: geometry
        }
        onExited: (code, status) => {
            if (code !== 0)
                return;
            const parts = geometry.text.trim().split("|");
            if (parts.length !== 2 || !Quickshell.screens.some(s => s.name === parts[0])) {
                root.error = I18n.tr("recording.areaHint");
                ShellState.toggle("recording");
                return;
            }
            root.output = parts[0];
            root.record(parts[1]);
        }
    }
    Process {
        id: recorder
        stdout: SplitParser {
            onRead: line => {
                try {
                    const state = JSON.parse(line);
                    if (state.path)
                        root.path = state.path;
                    if (state.error)
                        root.error = state.error;
                } catch (e) {
                    root.error = I18n.tr("recording.errors.invalidResponse");
                }
            }
        }
        onExited: (code, status) => {
            root.stopping = false;
            if (code !== 0 && !root.error)
                root.error = I18n.tr("recording.errors.interrupted");
            if (root.error && ShellState.panel !== "recording")
                ShellState.toggle("recording");
        }
    }
}
