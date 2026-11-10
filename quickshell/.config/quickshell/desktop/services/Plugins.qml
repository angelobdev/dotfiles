pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "JobRecord.js" as JobRecord
import ".."

// The Hyprland plugins (plugins.py). At Hyprland startup `desktop-plugins reload` writes plugin-rebuild.json with
// "wanted" when they need a rebuild; the shell starts it here once its polkit agent is registered (the rebuild asks
// for root once, through pkexec), detached so a shell restart does not stop it. The Plugins tab in Settings → System
// reads status, starts a rebuild and cleans the build cache.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/plugins.py"
    // bundle.STAMP's directory (scripts/hyprpm/bundle.py), not XDG_STATE_HOME.
    readonly property string rebuildFile: Quickshell.env("HOME") + "/.local/state/dotfiles/plugin-rebuild.json"
    // Set by shell.qml from the polkit agent: no prompt can show before it is registered.
    property bool agentReady: false
    property var rebuild: ({})
    // When startRebuild() asked, in seconds: until plugins.py records that run, the file holds the one before.
    property real requested: 0
    property var status: ({})
    readonly property bool running: rebuild.running === true
    readonly property bool wanted: typeof rebuild.wanted === "string" && !running
    readonly property bool reading: reader.running
    property bool cleaning: cleaner.running
    property string error: ""
    function parse(text) {
        try {
            const value = JSON.parse(text);
            return value && typeof value === "object" && !Array.isArray(value) ? value : {};
        } catch (failure) {
            return {};
        }
    }
    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function startRebuild() {
        if (running)
            return;
        // Shown at once; plugins.py writes the same as soon as it holds the lock.
        requested = Date.now() / 1000;
        rebuild = Object.assign({}, rebuild, {
            running: true
        });
        Quickshell.execDetached(["python3", helper, "rebuild"]);
    }
    function clearCache(kind) {
        if (cleaner.running || running)
            return;
        cleaner.command = ["python3", helper, "clear-cache", kind];
        cleaner.running = true;
    }
    // At login: the rebuild plugins.py asked for, once the prompt can show.
    onWantedChanged: Qt.callLater(startWanted)
    // The file may appear after the shell read it (both start with Hyprland): status reads it again then.
    onAgentReadyChanged: if (agentReady)
        refresh()
    function startWanted() {
        if (wanted && agentReady)
            startRebuild();
    }
    FileView {
        id: file
        path: root.rebuildFile
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            const value = root.parse(text());
            if (!JobRecord.stale(value, root.requested, Date.now() / 1000))
                root.rebuild = value;
            root.refresh();
        }
        onLoadFailed: root.rebuild = ({})
    }
    Process {
        id: reader
        command: ["python3", root.helper, "status"]
        stdout: StdioCollector {
            onStreamFinished: {
                const value = root.parse(text);
                root.status = value;
                // The same record as plugin-rebuild.json, with the log: the newest of the two wins.
                // Not the record of an earlier rebuild over the one just started (unless it never started), as Job.qml.
                if (value.rebuild && typeof value.rebuild === "object" && !JobRecord.stale(value.rebuild, root.requested, Date.now() / 1000)) {
                    root.requested = 0;
                    const record = Object.assign({}, value.rebuild);
                    delete record.log;
                    root.rebuild = record;
                }
                root.startWanted();
                root.error = Object.keys(value).length ? "" : text.trim();
            }
        }
        stderr: StdioCollector {
            onStreamFinished: if (text.trim() !== "")
                root.error = text.trim()
        }
    }
    Process {
        id: cleaner
        stderr: StdioCollector {
            onStreamFinished: root.error = text.trim()
        }
        onRunningChanged: if (!running)
            root.refresh()
    }
}
