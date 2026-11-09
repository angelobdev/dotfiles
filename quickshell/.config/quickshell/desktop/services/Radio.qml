pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Singleton {
    id: root
    property var stations: []
    property var saved: []
    property var results: []
    property bool active: false
    property bool playing: false
    property bool paused: false
    property string stationId: ""
    property string title: ""
    property string stationTitle: ""
    property string subtitle: ""
    property string url: ""
    property string kind: ""
    property bool video: false
    property string error: ""
    property string lastQuery: ""
    property string searchType: "all"
    readonly property bool searching: searchProc.running
    readonly property bool busy: actionProc.running
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/radio.py"
    readonly property string statePath: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/desktop-shell/radio.json"

    Component.onCompleted: refresh()

    function applyStateObj(s) {
        if (!s || typeof s !== "object") {
            resetState();
            return;
        }
        active = Boolean(s.active);
        playing = Boolean(s.playing);
        paused = Boolean(s.paused);
        stationId = s.stationId || "";
        title = s.title || "";
        stationTitle = s.stationTitle || "";
        subtitle = s.subtitle || "";
        url = s.url || "";
        kind = s.kind || "";
        video = Boolean(s.video);
    }

    function applyStateText(raw) {
        if (!raw || raw.trim() === "") {
            resetState();
            return;
        }
        try {
            applyStateObj(JSON.parse(raw));
        } catch (e) {
            resetState();
        }
    }

    function resetState() {
        active = false;
        playing = false;
        paused = false;
        stationId = "";
        title = "";
        stationTitle = "";
        subtitle = "";
        url = "";
        kind = "";
        video = false;
    }

    function refresh() {
        if (!listProc.running)
            listProc.running = true;
    }

    function isSaved(targetUrl) {
        if (!targetUrl)
            return false;
        const norm = targetUrl.replace(/\/+$/, "");
        for (const item of saved) {
            if (item.url === targetUrl || item.id === targetUrl || (item.url && item.url.replace(/\/+$/, "") === norm))
                return true;
        }
        return false;
    }

    function play(itemOrId, withVideo) {
        error = "";
        const payload = typeof itemOrId === "object" ? JSON.stringify(itemOrId) : String(itemOrId);
        const useVideo = withVideo !== undefined ? Boolean(withVideo) : video;
        const args = ["python3", helper, "play", payload];
        if (useVideo)
            args.push("--video");
        runAction(args);
    }

    function stop() {
        runAction(["python3", helper, "stop"]);
    }

    function togglePlaying() {
        runAction(["python3", helper, "toggle"]);
    }

    function next() {
        runAction(["python3", helper, "next"]);
    }

    function previous() {
        runAction(["python3", helper, "previous"]);
    }

    function toggleVideo() {
        runAction(["python3", helper, "video", "toggle"]);
    }

    function saveItem(item) {
        if (!item)
            return;
        runAction(["python3", helper, "save", JSON.stringify(item)]);
    }

    function removeItem(idOrUrl) {
        if (!idOrUrl)
            return;
        runAction(["python3", helper, "remove", String(idOrUrl)]);
    }

    function search(query, mode) {
        const trimmed = (query || "").trim();
        if (!trimmed)
            return;
        error = "";
        lastQuery = trimmed;
        if (mode)
            searchType = mode;
        if (searchProc.running)
            searchProc.running = false;
        searchProc.command = ["python3", helper, "search", trimmed, searchType];
        searchProc.running = true;
    }

    function runAction(cmd) {
        if (actionProc.running)
            actionProc.running = false;
        actionProc.command = cmd;
        actionProc.running = true;
    }

    FileView {
        id: stateFile
        path: root.statePath
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.applyStateText(text())
        onLoadFailed: root.resetState()
    }

    Process {
        id: listProc
        command: ["python3", root.helper, "list"]
        stdout: StdioCollector {
            id: listOut
        }
        onExited: code => {
            if (code !== 0)
                return;
            try {
                const parsed = JSON.parse(listOut.text);
                if (Array.isArray(parsed.stations))
                    root.stations = parsed.stations;
                if (Array.isArray(parsed.saved))
                    root.saved = parsed.saved;
                if (parsed.state)
                    root.applyStateObj(parsed.state);
            } catch (e) {}
        }
    }

    Process {
        id: actionProc
        stdout: StdioCollector {
            id: actionOut
        }
        stderr: StdioCollector {
            id: actionErr
        }
        onExited: code => {
            if (code !== 0) {
                root.error = actionErr.text.trim();
                return;
            }
            root.error = "";
            const out = actionOut.text.trim();
            if (out) {
                try {
                    const parsed = JSON.parse(out);
                    if (Array.isArray(parsed.saved))
                        root.saved = parsed.saved;
                    else if ("active" in parsed)
                        root.applyStateObj(parsed);
                } catch (e) {}
            }
            stateFile.reload();
        }
    }

    Process {
        id: searchProc
        stdout: StdioCollector {
            id: searchOut
        }
        stderr: StdioCollector {
            id: searchErr
        }
        onExited: code => {
            if (code !== 0) {
                root.error = searchErr.text.trim();
                return;
            }
            root.error = "";
            try {
                const parsed = JSON.parse(searchOut.text);
                root.results = Array.isArray(parsed.results) ? parsed.results : [];
            } catch (e) {
                root.results = [];
            }
        }
    }

    Timer {
        interval: 2000
        running: ShellState.panel === "radio" || root.active
        repeat: true
        onTriggered: stateFile.reload()
    }
}
