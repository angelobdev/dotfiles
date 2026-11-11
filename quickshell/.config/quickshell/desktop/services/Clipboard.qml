pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."
import "../components/FileUrl.js" as FileUrl

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
    // Thumbnails of image entries by id: a file URL, or "" when the entry has none. Made by clipboard.py when a row
    // showing the entry asks (rows on screen only), never for text; the helper removes those of entries gone.
    property var thumbnails: ({})
    property var thumbnailsWanted: []
    function refresh() {
        if (operation.running)
            return;
        listing.request();
    }
    function requestThumbnail(id) {
        if (thumbnails[id] !== undefined || thumbnailsWanted.includes(id))
            return;
        thumbnailsWanted = thumbnailsWanted.concat([id]);
        Qt.callLater(makeThumbnails);
    }
    function makeThumbnails() {
        if (thumbnailer.running || thumbnailsWanted.length === 0)
            return;
        thumbnailer.asked = thumbnailsWanted;
        thumbnailsWanted = [];
        thumbnailer.command = ["python3", helper, "thumbnails"].concat(thumbnailer.asked);
        thumbnailer.running = true;
    }
    // An image entry as a person reads it: "Image · 2448×1600 · 745 KiB".
    function label(entry) {
        if (!entry.image || !entry.size)
            return entry.preview;
        return entry.width ? I18n.tr("clipboard.image", [entry.width, entry.height, entry.size]) : I18n.tr("clipboard.imageSize", [entry.size]);
    }
    function act(action, id) {
        if (operation.running)
            return;
        error = "";
        operation.action = action;
        operation.command = ["python3", helper, action].concat(id ? [id] : []);
        operation.running = true;
    }
    // Started and stopped with collecting, and started again after an exit (Watcher).
    Watcher {
        id: textWatcher
        wanted: root.collecting
        name: "clipboard.py watch-text"
        // Ends with the shell, even a killed one (setpriv: the kernel signals it).
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", root.helper, "watch-text", String(Config.clipboardMaxItems)])
    }
    Watcher {
        id: imageWatcher
        wanted: root.collecting
        name: "clipboard.py watch-image"
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", root.helper, "watch-image", String(Config.clipboardMaxItems)])
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
                    // Only the thumbnails of entries still listed; the helper has removed the files of the others.
                    const kept = {};
                    for (const entry of root.entries)
                        if (root.thumbnails[entry.id] !== undefined)
                            kept[entry.id] = root.thumbnails[entry.id];
                    root.thumbnails = kept;
                } catch (e) {
                    root.error = I18n.tr("clipboard.errors.historyUnavailable");
                }
            } else
                root.error = listingErrors.text.trim();
        }
    }
    Process {
        id: thumbnailer
        property var asked: []
        stdout: StdioCollector {
            id: thumbnailData
        }
        onExited: (code, status) => {
            let made = {};
            try {
                made = code === 0 ? JSON.parse(thumbnailData.text) : {};
            } catch (error) {}
            const next = Object.assign({}, root.thumbnails);
            for (const id of asked)
                next[id] = made[id] ? FileUrl.of(made[id]) : "";
            root.thumbnails = next;
            root.makeThumbnails();
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
