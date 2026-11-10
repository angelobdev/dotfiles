pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "JobRecord.js" as JobRecord
import ".."

// Available updates: updates.py check (desktop-updates.timer 5 minutes after login and every 6 hours, or Check
// now in the panel) writes updates.json: system packages, Flatpak apps and the new commits of this repository
// (one update, however many commits). The bar shows an icon while there are any, and a notification announces
// updates that were not there at the previous check.
Singleton {
    id: root
    readonly property string wrapper: Quickshell.env("HOME") + "/.local/bin/desktop-updates"
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell"
    property var data: ({})
    // The first read (a shell start) only takes the list: the notification is for updates found later.
    property bool loaded: false
    readonly property var packages: Array.isArray(data.packages) ? data.packages : []
    readonly property var flatpaks: Array.isArray(data.flatpaks) ? data.flatpaks : []
    // The repository against its upstream branch: {upstream, head, behind, ahead, dirty, commits}, or {}.
    readonly property var repository: data.repository && typeof data.repository === "object" && !Array.isArray(data.repository) ? data.repository : ({})
    readonly property int behind: Number.isInteger(repository.behind) && repository.behind > 0 ? repository.behind : 0
    readonly property var commits: Array.isArray(repository.commits) ? repository.commits.filter(commit => commit && typeof commit === "object") : []
    readonly property int count: packages.length + flatpaks.length + (behind > 0 ? 1 : 0)
    // Hyprland is among them: the plugins need rebuilding after the update and a new login.
    readonly property bool compositor: data.compositor === true
    readonly property var errors: Array.isArray(data.errors) ? data.errors : []
    readonly property real checked: (data.checked ?? 0) * 1000
    readonly property bool checking: checker.running
    function parse(text) {
        try {
            const value = JSON.parse(text);
            return value && typeof value === "object" ? value : {};
        } catch (failure) {
            return {};
        }
    }
    function names(value) {
        // Guarded like the properties above: a malformed file must not stop onLoaded before data is updated.
        const list = items => Array.isArray(items) ? items.filter(item => item && typeof item === "object") : [];
        const repository = value.repository && typeof value.repository === "object" ? value.repository : {};
        // The repository by the commit its upstream is at: new commits are a new update.
        const pull = Number.isInteger(repository.behind) && repository.behind > 0 ? ["repository " + repository.head] : [];
        return list(value.packages).map(p => p.name + " " + p.version).concat(list(value.flatpaks).map(f => f.id + " " + f.version), pull);
    }
    function check() {
        if (!checker.running)
            checker.running = true;
    }
    // Applying them, without a terminal: desktop-updates apply runs the updates screen's apply in the background,
    // with one pkexec prompt when root is needed; updates-apply.json holds its state and the log its output.
    property var applyState: ({})
    property var applyLog: []
    // When apply() asked, in seconds: until updates.py records that run, the file still holds the one before.
    property real requested: 0
    readonly property bool applying: applyState.running === true
    // The repository can be fast-forwarded: behind its upstream, with nothing of its own and no local changes.
    readonly property bool pullable: behind > 0 && !(repository.ahead > 0) && repository.dirty !== true
    function apply(keys) {
        if (applying || keys.length === 0)
            return;
        // Shown at once; updates.py writes the same as soon as it holds its lock.
        requested = Date.now() / 1000;
        applyState = {
            running: true,
            keys: keys
        };
        applyLog = [];
        Quickshell.execDetached([wrapper, "apply", keys.join(",")]);
    }
    function readApply() {
        if (!applyReader.running)
            applyReader.running = true;
    }
    function announce(next) {
        const before = names(data);
        const added = names(next).filter(name => !before.includes(name));
        if (added.length === 0)
            return;
        const total = names(next).length;
        notifier.title = I18n.plural("updates.notice.one", "updates.notice.other", total);
        notifier.body = I18n.tr(next.compositor ? "updates.compositor" : "updates.noticeBody");
        notifier.running = false;
        notifier.running = true;
    }
    Process {
        id: checker
        command: [root.wrapper, "check"]
    }
    Process {
        id: applyReader
        command: [root.wrapper, "apply-status"]
        stdout: StdioCollector {
            onStreamFinished: {
                const value = root.parse(text);
                // Not the file of an earlier apply over the one just started (unless it never started), as Job.qml.
                if (JobRecord.stale(value, root.requested, Date.now() / 1000))
                    return;
                root.requested = 0;
                root.applyLog = Array.isArray(value.log) ? value.log.filter(line => typeof line === "string") : [];
                delete value.log;
                root.applyState = value;
            }
        }
    }
    // The log grows while it runs.
    Timer {
        interval: 2000
        repeat: true
        running: root.applying
        onTriggered: root.readApply()
    }
    FileView {
        path: root.stateDir + "/updates-apply.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.readApply()
    }
    Process {
        id: notifier
        property string title
        property string body
        command: ["notify-send", "--wait", "--app-name=" + I18n.tr("updates.title"), "--app-icon=system-software-update", "--action=default=" + I18n.tr("updates.title"), title, body]
        stdout: StdioCollector {
            onStreamFinished: {
                if (text.trim() === "default")
                    ShellState.open("updates");
            }
        }
    }
    FileView {
        path: root.stateDir + "/updates.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            const next = root.parse(text());
            if (root.loaded)
                root.announce(next);
            root.data = next;
            root.loaded = true;
        }
        onLoadFailed: root.loaded = true
    }
}
