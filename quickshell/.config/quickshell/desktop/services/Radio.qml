pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// Radio & music (radio.py): the stations and categories, the saved items, YouTube search, and the own mpv of the radio,
// which plays sound only. The state file follows play and stop; while the panel is open, status reads the title and
// pause from mpv itself. mpv-mpris puts that mpv on MPRIS for the bar, the lock screen and the media keys.
// The picture plays in the Radio panel (RadioVideo.qml): openVideo() pauses mpv and gets one stream with sound and
// picture from where it was (radio.py handoff); closeVideo(seconds) gives the sound back to mpv from there.
Singleton {
    id: root
    property var categories: []
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
    property string error: ""
    property string lastQuery: ""
    property string searchType: "all"
    readonly property bool searching: searchProc.running
    readonly property bool busy: actionProc.running
    // The picture in the panel: open, the stream it plays and where it starts. While it is open, mpv is paused.
    property bool videoOpen: false
    property string videoStream: ""
    property real videoStart: 0
    readonly property bool videoLoading: handoffProc.running
    readonly property bool hasVideo: active && ["youtube", "playlist", "file"].includes(kind)
    // A skip while the picture is open: the picture of the next item, once mpv has moved to it.
    property bool reopenVideo: false
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

    function play(itemOrId) {
        error = "";
        dropVideo();
        const payload = typeof itemOrId === "object" ? JSON.stringify(itemOrId) : String(itemOrId);
        runAction(["python3", helper, "play", payload]);
    }

    function stop() {
        dropVideo();
        runAction(["python3", helper, "stop"]);
    }

    function togglePlaying() {
        runAction(["python3", helper, "toggle"]);
    }

    function next() {
        skip("next");
    }

    function previous() {
        skip("previous");
    }

    function skip(direction) {
        // mpv is paused under the picture: it moves on, and the picture follows.
        reopenVideo = videoOpen;
        dropVideo();
        runAction(["python3", helper, direction]);
    }

    function openVideo() {
        if (!hasVideo || handoffProc.running)
            return;
        error = "";
        videoOpen = true;
        videoStream = "";
        handoffProc.running = true;
    }

    // seconds: where the picture of the panel was; mpv goes on with the sound from there.
    function closeVideo(seconds) {
        if (!videoOpen)
            return;
        dropVideo();
        runAction(["python3", helper, "resume", String(Math.max(0, Math.floor(seconds || 0)))]);
    }

    // The picture goes away without giving the sound back (a new item, stop, a skip).
    function dropVideo() {
        videoOpen = false;
        videoStream = "";
        videoStart = 0;
        if (handoffProc.running)
            handoffProc.running = false;
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
                if (Array.isArray(parsed.categories))
                    root.categories = parsed.categories.filter(name => typeof name === "string");
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
            if (root.reopenVideo) {
                root.reopenVideo = false;
                root.openVideo();
            }
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

    Process {
        id: handoffProc
        command: ["python3", root.helper, "handoff"]
        stdout: StdioCollector {
            id: handoffOut
        }
        stderr: StdioCollector {
            id: handoffErr
        }
        onExited: code => {
            if (!root.videoOpen)
                return;
            try {
                const value = JSON.parse(handoffOut.text);
                if (code === 0 && typeof value.stream === "string" && value.stream !== "") {
                    root.videoStart = Number(value.position) || 0;
                    root.videoStream = value.stream;
                    return;
                }
            } catch (e) {}
            root.error = handoffErr.text.trim();
            root.videoOpen = false;
        }
    }
    // The title of a stream changes with each track: read it from mpv while it plays.
    Process {
        id: statusProc
        command: ["python3", root.helper, "status"]
        stdout: StdioCollector {
            onStreamFinished: root.applyStateText(text)
        }
    }
    Timer {
        interval: 3000
        running: root.active && ShellState.panel === "radio"
        repeat: true
        onTriggered: if (!statusProc.running)
            statusProc.running = true
    }
}
