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
    function refresh() {
        if (listing.running || operation.running)
            return;
        listing.running = true;
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
        command: ["python3", root.helper, "watch-text", String(Config.clipboardMaxItems)]
        running: root.collecting
    }
    Process {
        id: imageWatcher
        command: ["python3", root.helper, "watch-image", String(Config.clipboardMaxItems)]
        running: root.collecting
    }
    Timer {
        interval: 2000
        running: root.collecting
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
    Process {
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
                try {
                    root.entries = JSON.parse(data.text);
                    root.error = "";
                } catch (e) {
                    root.error = I18n.tr("Storico clipboard non disponibile.");
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
    Timer {
        interval: 1000
        running: ShellState.panel === "clipboard"
        repeat: true
        onTriggered: root.refresh()
    }
}
