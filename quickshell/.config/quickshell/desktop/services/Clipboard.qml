pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Singleton {
    id: root
    property bool paused: false
    property var entries: []
    property string error: ""
    readonly property bool busy: operation.running
    readonly property bool collecting: Config.clipboardEnabled && !paused
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/clipboard.py"
    readonly property string database: (Quickshell.env("XDG_CACHE_HOME") || Quickshell.env("HOME") + "/.cache") + "/cliphist/db"
    // The output of the last listing: the same one again changes nothing (the panel filters every entry anew).
    property string listed: ""
    function refresh() {
        if (operation.running)
            return;
        listing.request();
    }
    function act(action, id) {
        if (operation.running)
            return;
        error = "";
        operation.action = action;
        operation.command = ["python3", helper, action].concat(id ? [id] : []);
        operation.running = true;
    }
    Process {
        id: textWatcher
        // What a watcher that keeps failing says reaches qs log instead of nowhere.
        stderr: SplitParser {
            onRead: line => console.warn("clipboard.py watch-text:", line)
        }
        // Ends with the shell, even a killed one (setpriv: the kernel signals it).
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", root.helper, "watch-text", String(Config.clipboardMaxItems)])
        running: root.collecting
    }
    Process {
        id: imageWatcher
        // What a watcher that keeps failing says reaches qs log instead of nowhere.
        stderr: SplitParser {
            onRead: line => console.warn("clipboard.py watch-image:", line)
        }
        // Ends with the shell, even a killed one (setpriv: the kernel signals it).
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", root.helper, "watch-image", String(Config.clipboardMaxItems)])
        running: root.collecting
    }
    Timer {
        interval: 2000
        running: root.collecting && !(textWatcher.running && imageWatcher.running)
        repeat: true
        onTriggered: {
            if (!textWatcher.running)
                textWatcher.running = true;
            if (!imageWatcher.running)
                imageWatcher.running = true;
        }
    }
    onCollectingChanged: {
        textWatcher.running = collecting;
        imageWatcher.running = collecting;
    }
    // Asked while it runs (a copy during a listing), it lists once more after.
    CoalescedProcess {
        id: listing
        command: ["python3", root.helper, "list"]
        stdout: StdioCollector {
            id: data
        }
        stderr: StdioCollector {
            id: listingErrors
        }
        onExited: (code, status) => {
            if (code === 0) {
                if (data.text === root.listed && root.error === "")
                    return;
                try {
                    root.entries = JSON.parse(data.text);
                    root.listed = data.text;
                    root.error = "";
                } catch (e) {
                    root.error = I18n.tr("clipboard.errors.historyUnavailable");
                }
            } else
                root.error = listingErrors.text.trim();
        }
    }
    Process {
        id: operation
        property string action: ""
        stderr: StdioCollector {
            id: errors
        }
        onExited: (code, status) => {
            if (code !== 0)
                root.error = errors.text.trim();
            else if (action === "copy" && ShellState.panel === "clipboard")
                ShellState.close();
            root.refresh();
        }
    }
    // cliphist writes its database in place at each copy: while the panel is open, a change of it lists the
    // history again. Only the notification, never the file (megabytes). The panel lists it when it opens.
    FileView {
        path: root.database
        preload: false
        watchChanges: ShellState.panel === "clipboard"
        printErrors: false
        onFileChanged: root.refresh()
    }
}
