pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// The release of the desktop and its changelog (channel.py). A shell start, and every update check after it (an
// update of this repository checks again), asks for the notes of the versions installed since the last one seen:
// What's new opens with them once, and closing it records the installed version as seen. About opens it on the
// notes of the installed version.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/channel.py"
    // The installed release, "" before the first one.
    property string version: ""
    // [{version, date, notes}] on screen, newest first.
    property var sections: []
    // What is on screen has not been seen yet: closing records it.
    property bool unseen: false
    function parse(text) {
        try {
            const value = JSON.parse(text);
            return value && typeof value === "object" ? value : {};
        } catch (failure) {
            return {};
        }
    }
    function check() {
        if (!reader.running)
            reader.running = true;
    }
    function showCurrent() {
        if (!currentReader.running)
            currentReader.running = true;
    }
    function show(value, fresh) {
        const list = Array.isArray(value.sections) ? value.sections.filter(section => section && typeof section.version === "string" && typeof section.notes === "string") : [];
        root.version = typeof value.version === "string" ? value.version : "";
        if (list.length === 0)
            return;
        root.sections = list;
        root.unseen = fresh;
        ShellState.open("whatsnew");
    }
    Process {
        id: reader
        command: ["python3", root.helper, "whats-new"]
        stdout: StdioCollector {
            onStreamFinished: root.show(root.parse(text), true)
        }
    }
    Process {
        id: currentReader
        command: ["python3", root.helper, "whats-new", "--current"]
        stdout: StdioCollector {
            onStreamFinished: root.show(root.parse(text), false)
        }
    }
    Process {
        id: recorder
        command: ["python3", root.helper, "seen"]
    }
    Connections {
        target: ShellState
        function onPanelChanged() {
            if (ShellState.panel !== "whatsnew" && root.unseen) {
                root.unseen = false;
                recorder.running = true;
            }
        }
    }
    // An update of this repository ends with a check, which rewrites updates.json.
    Connections {
        target: Updates
        function onDataChanged() {
            Qt.callLater(root.check);
        }
    }
    // Once the session has settled after a start.
    Timer {
        interval: 4000
        running: true
        onTriggered: root.check()
    }
}
