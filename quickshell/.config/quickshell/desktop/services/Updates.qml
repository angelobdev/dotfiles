pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// Available system updates: updates.py check (desktop-updates.timer 5 minutes after login and every 6
// hours, or Check now in the panel) writes updates.json. The bar shows an icon while there are any, and a
// notification announces updates that were not there at the previous check.
Singleton {
    id: root
    readonly property string wrapper: Quickshell.env("HOME") + "/.local/bin/desktop-updates"
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell"
    property var data: ({})
    // The first read (a shell start) only takes the list: the notification is for updates found later.
    property bool loaded: false
    readonly property var packages: Array.isArray(data.packages) ? data.packages : []
    readonly property var flatpaks: Array.isArray(data.flatpaks) ? data.flatpaks : []
    readonly property int count: packages.length + flatpaks.length
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
        return (value.packages ?? []).map(p => p.name + " " + p.version).concat((value.flatpaks ?? []).map(f => f.id + " " + f.version));
    }
    function check() {
        if (!checker.running)
            checker.running = true;
    }
    function upgrade() {
        Quickshell.execDetached([wrapper, "upgrade"]);
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
        id: notifier
        property string title
        property string body
        command: ["notify-send", "--wait", "--app-name=" + I18n.tr("updates.title"), "--app-icon=system-software-update", "--action=default=" + I18n.tr("updates.title"), title, body]
        stdout: StdioCollector {
            onStreamFinished: {
                if (text.trim() === "default")
                    ShellState.show("updates");
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
