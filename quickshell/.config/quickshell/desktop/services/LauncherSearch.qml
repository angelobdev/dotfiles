pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// What the launcher finds besides apps: a calculation or unit conversion (qalc, only when the query has a
// digit) and files in the home folder (fd, from three characters). Both run a moment after typing stops, and
// a late answer for an older query is dropped.
Singleton {
    id: root
    property string query: ""
    property string calc: ""
    property var files: []

    onQueryChanged: {
        const text = query.trim();
        if (!/[0-9]/.test(text) || text.length > 200)
            calc = "";
        if (text.length < 3 || !Config.launcherFiles)
            files = [];
        debounce.restart();
    }
    // What qalc is asked: a decimal comma between digits becomes a dot (qalc reads one or the other, never both,
    // and in Italian it took "3.5" for 35); after "to" or "->" a minus keeps the answer in one unit instead of
    // "3 mi + 188 yd + …"; a leading minus would read as an option.
    function expression(text) {
        const plain = text.replace(/(\d),(\d)/g, "$1.$2").replace(/(\s(?:to|->|→)\s+)(?=[^\s+-])/g, "$1-");
        return plain.startsWith("-") ? "0" + plain : plain;
    }
    function copy(text) {
        Quickshell.execDetached(["wl-copy", "--", text]);
    }
    function open(path) {
        Quickshell.execDetached(["xdg-open", path]);
    }
    Timer {
        id: debounce
        interval: 180
        onTriggered: {
            const text = root.query.trim();
            if (/[0-9]/.test(text) && text.length <= 200) {
                calculator.pending = text;
                calculator.command = ["qalc", "-t", "-s", "decimal comma off", root.expression(text)];
                calculator.running = false;
                calculator.running = true;
            }
            if (text.length >= 3 && Config.launcherFiles) {
                finder.pending = text;
                finder.command = ["fd", "--type", "f", "--fixed-strings", "--ignore-case", "--max-results", "8", "--", text, Quickshell.env("HOME")];
                finder.running = false;
                finder.running = true;
            }
        }
    }
    // What a run answers is set when it starts: a run killed for a newer query reports its output after the newer
    // query was asked for, and before the newer run starts (Store.qml does the same).
    Process {
        id: calculator
        property string asked: ""
        property string pending: ""
        onStarted: asked = pending
        stdout: StdioCollector {
            onStreamFinished: {
                if (calculator.asked !== root.query.trim())
                    return;
                const result = text.trim().split("\n").pop() ?? "";
                // qalc echoes words it does not know: only an answer that differs from the question counts.
                root.calc = result !== "" && result !== calculator.asked && !/error|warning/i.test(result) ? result : "";
            }
        }
        onExited: (code, status) => {
            if (code !== 0 && calculator.asked === root.query.trim())
                root.calc = "";
        }
    }
    Process {
        id: finder
        property string asked: ""
        property string pending: ""
        onStarted: asked = pending
        stdout: StdioCollector {
            onStreamFinished: {
                if (finder.asked === root.query.trim())
                    root.files = text.split("\n").filter(line => line !== "");
            }
        }
    }
}
