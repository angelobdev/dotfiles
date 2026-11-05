pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// The KDE Store page of the Theming panel (store.py): search results for cursor or icon themes, installing
// one of an entry's files, and the folders it installed (which it alone may remove).
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/store.py"
    property string kind: "icons"
    property string query: ""
    property int page: 0
    property int total: 0
    property var items: []
    property bool searching: false
    // Entry id being installed, or 0.
    property int installing: 0
    property string error: ""
    property string message: ""
    // Folder name -> {id, name, kind, file}.
    property var installed: ({})
    readonly property bool more: items.length < total
    // An install or a removal is running: the next one waits for it (the panel disables its buttons).
    readonly property bool working: worker.running

    signal changed

    // A new search replaces one still running; an answer for an older search is dropped.
    function search(newKind, newQuery) {
        kind = newKind;
        query = newQuery.trim();
        page = 0;
        items = [];
        searcher.running = false;
        run(searcher, ["search", kind, query, "0"]);
    }
    function asked() {
        return [kind, query, page].join("\n");
    }
    function next() {
        if (searching || !more)
            return;
        page += 1;
        run(searcher, ["search", kind, query, String(page)]);
    }
    function install(id, index) {
        if (working)
            return;
        installing = id;
        error = "";
        message = "";
        run(worker, ["install", kind, String(id), String(index)]);
    }
    function remove(folders) {
        if (working || folders.length === 0)
            return;
        error = "";
        message = "";
        run(worker, ["remove"].concat(folders));
    }
    function foldersOf(id) {
        return Object.keys(installed).filter(folder => installed[folder].id === id);
    }
    function refreshInstalled() {
        run(ledger, ["installed"]);
    }
    function run(process, args) {
        process.command = ["python3", helper].concat(args);
        if (process === searcher) {
            searcher.asked = asked();
            searching = true;
        }
        process.running = true;
    }
    function parse(text) {
        try {
            const value = JSON.parse(text);
            return value && typeof value === "object" ? value : {};
        } catch (failure) {
            return {
                error: I18n.tr("store.errors.unavailable")
            };
        }
    }
    Process {
        id: searcher
        property string asked: ""
        stdout: StdioCollector {
            onStreamFinished: {
                if (searcher.asked !== root.asked())
                    return;
                const value = root.parse(text);
                root.searching = false;
                root.error = value.error ?? "";
                if (value.items) {
                    root.items = root.page === 0 ? value.items : root.items.concat(value.items);
                    root.total = value.total ?? 0;
                }
            }
        }
    }
    Process {
        id: worker
        stdout: StdioCollector {
            onStreamFinished: {
                const value = root.parse(text);
                root.installing = 0;
                root.error = value.error ?? "";
                if (value.installed)
                    root.message = I18n.tr("store.done", [value.installed.join(", ")]);
                root.refreshInstalled();
                Theming.refresh();
                root.changed();
            }
        }
    }
    Process {
        id: ledger
        stdout: StdioCollector {
            onStreamFinished: root.installed = root.parse(text).installed ?? {}
        }
    }
}
