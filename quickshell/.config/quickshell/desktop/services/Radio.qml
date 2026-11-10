pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// Radio & music (radio.py): the stations and categories, the saved items, YouTube search, and the own mpv of the radio,
// which plays sound only. The state file follows play and stop; while the panel is open, status reads the title and
// pause from mpv itself. mpv-mpris puts that mpv on MPRIS for the bar, the lock screen and the media keys.
// The picture plays in the Radio panel (RadioVideo.qml), muted: openVideo() gets the video-only stream of what mpv
// plays (radio.py video), and while it is open, status is read every second so the picture follows the position,
// the pause and the item of mpv, which keeps the sound.
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
    // Where mpv is, and the item it plays (of a playlist too), from status.
    property real position: 0
    property string item: ""
    // The picture in the panel: open, the stream it plays, where it starts and the item it shows.
    property bool videoOpen: false
    property string videoStream: ""
    property real videoStart: 0
    property string videoItem: ""
    readonly property bool videoLoading: videoProc.running
    readonly property bool hasVideo: active && ["youtube", "playlist", "file"].includes(kind)
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
        position = Number(s.position) || 0;
        item = s.item || s.url || "";
        // mpv moved to another item (a playlist, a skip): the picture follows.
        if (videoOpen && videoItem !== "" && item !== "" && item !== videoItem && !videoProc.running)
            openVideo();
        if (videoOpen && !active)
            dropVideo();
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
        position = 0;
        item = "";
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
        runAction(["python3", helper, "next"]);
    }

    function previous() {
        runAction(["python3", helper, "previous"]);
    }

    function openVideo() {
        if (!hasVideo || videoProc.running)
            return;
        error = "";
        videoOpen = true;
        videoStream = "";
        videoProc.running = true;
    }

    // The picture as soon as there is one: desktop-radio video may come before this has read the state.
    property bool videoWanted: false
    function requestVideo() {
        if (hasVideo) {
            openVideo();
            return;
        }
        videoWanted = true;
        wantedTimer.restart();
        refresh();
    }
    onHasVideoChanged: if (hasVideo && videoWanted) {
        videoWanted = false;
        openVideo();
    }
    Timer {
        id: wantedTimer
        interval: 5000
        onTriggered: root.videoWanted = false
    }

    // The picture goes away; mpv never stopped playing the sound.
    function dropVideo() {
        videoOpen = false;
        videoStream = "";
        videoStart = 0;
        videoItem = "";
        if (videoProc.running)
            videoProc.running = false;
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
        id: videoProc
        command: ["python3", root.helper, "video"]
        stdout: StdioCollector {
            id: videoOut
        }
        stderr: StdioCollector {
            id: videoErr
        }
        onExited: code => {
            if (!root.videoOpen)
                return;
            try {
                const value = JSON.parse(videoOut.text);
                if (code === 0 && typeof value.stream === "string" && value.stream !== "") {
                    root.videoStart = Number(value.position) || 0;
                    root.videoItem = value.item || "";
                    root.videoStream = value.stream;
                    return;
                }
            } catch (e) {}
            root.error = videoErr.text.trim();
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
    // Every second with the picture open, which follows the position of mpv; every three with the panel open.
    Timer {
        interval: root.videoOpen ? 1000 : 3000
        running: root.active && ShellState.panel === "radio"
        repeat: true
        onTriggered: if (!statusProc.running)
            statusProc.running = true
    }
}
