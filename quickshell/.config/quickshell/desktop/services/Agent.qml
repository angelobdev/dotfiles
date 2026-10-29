pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."

// The Claude Code assistant (desktop-ai) and its drop-down console, the special workspace "ai" laid out
// by hypr/config/console.lua: which screen shows it, what Claude is doing (the hooks of desktop-ai write
// agent.json through agent.py), the subscription usage of its status line, and the notifications sent
// while the console is hidden.
Singleton {
    id: root
    readonly property string launcher: Quickshell.env("HOME") + "/.local/bin/desktop-ai"
    readonly property string runtimeDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/desktop-shell"
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell"
    // Claude Code installed (desktop-ai adds ~/.local/bin, where its installer puts it).
    property bool available: false
    readonly property bool running: Hyprland.toplevels.values.some(t => (t.wayland?.appId || t.lastIpcObject?.class) === "desktop-ai")
    // The screen showing the console, or "" while it is hidden.
    property string consoleScreen: ""
    readonly property bool consoleOpen: consoleScreen !== ""
    property var record: ({})
    // The first read (a shell start) only takes the state: notifications are for changes after it.
    property bool recordLoaded: false
    // ready, working, permission, finished or error; "" when Claude is not running or reported nothing yet.
    readonly property string state: running ? record.state ?? "" : ""
    readonly property string detail: running ? record.detail ?? "" : ""
    readonly property real since: (record.since ?? 0) * 1000
    // Finished, failed or asking while the console was hidden, and not looked at since.
    property bool unseen: false
    property var usage: ({})
    readonly property string plan: {
        const tier = usage.tier ?? "";
        const match = /max_(\d+)x/.exec(tier);
        if (match)
            return I18n.tr("assistant.plans.max", [match[1]]);
        if (/max/.test(tier))
            return I18n.tr("assistant.plans.maxPlain");
        if (/pro/.test(tier))
            return I18n.tr("assistant.plans.pro");
        return "";
    }
    function parse(text) {
        try {
            const data = JSON.parse(text);
            return data && typeof data === "object" ? data : {};
        } catch (failure) {
            return {};
        }
    }
    function toggleConsole() {
        Quickshell.execDetached([launcher]);
    }
    function showConsole() {
        if (!consoleOpen)
            toggleConsole();
    }
    function hideConsole(screenName) {
        Quickshell.execDetached(["hyprctl", "eval", "if desktop_console_hide then desktop_console_hide(" + JSON.stringify(screenName) + ") end"]);
    }
    function readMonitors() {
        let found = "";
        for (const monitor of Hyprland.monitors.values)
            if (monitor.lastIpcObject?.specialWorkspace?.name === "special:ai")
                found = monitor.name;
        consoleScreen = found;
    }
    function markup(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
    // One notification at a time: a new one replaces the previous (its notify-send then exits).
    function closeNotices() {
        for (const notification of Notices.notifications.values.slice())
            if (notification.desktopEntry === "desktop-ai")
                notification.dismiss();
    }
    function notify(title, body) {
        closeNotices();
        notifier.running = false;
        notifier.title = title;
        notifier.body = markup(body);
        notifier.running = true;
    }
    function stateMoved() {
        if (consoleOpen || !running || !["permission", "finished", "error"].includes(state))
            return;
        unseen = true;
        if (state === "permission")
            notify(I18n.tr("assistant.notices.permission"), detail);
        else if (state === "finished")
            notify(I18n.tr("assistant.notices.finished"), detail);
        else
            notify(I18n.tr("assistant.notices.error"), detail);
    }
    onConsoleOpenChanged: {
        if (!consoleOpen)
            return;
        unseen = false;
        closeNotices();
    }
    onRunningChanged: if (!running)
        unseen = false
    Process {
        id: notifier
        property string title
        property string body
        command: ["notify-send", "--wait", "--app-name=" + I18n.tr("assistant.claude"), "--app-icon=desktopai", "--hint=string:desktop-entry:desktop-ai", "--action=default=" + I18n.tr("assistant.openConsole"), "--action=open=" + I18n.tr("assistant.openConsole"), title, body]
        stdout: StdioCollector {
            onStreamFinished: {
                if (["default", "open"].includes(text.trim()))
                    root.showConsole();
            }
        }
    }
    Process {
        id: probe
        command: ["sh", "-c", "PATH=\"$HOME/.local/bin:$PATH\" command -v claude"]
        onExited: code => root.available = code === 0
    }
    FileView {
        path: root.runtimeDir + "/agent.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            const next = root.parse(text());
            const moved = root.recordLoaded && next.state !== root.record.state;
            root.record = next;
            root.recordLoaded = true;
            if (moved)
                root.stateMoved();
        }
        onLoadFailed: {
            root.record = {};
            root.recordLoaded = true;
        }
    }
    FileView {
        path: root.stateDir + "/agent-usage.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.usage = root.parse(text())
        onLoadFailed: root.usage = {}
    }
    // activespecial>>WORKSPACE,MONITOR, with an empty workspace when the special one closes.
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name !== "activespecial")
                return;
            const [workspace, monitor] = event.data.split(",");
            if (workspace === "special:ai")
                root.consoleScreen = monitor;
            else if (root.consoleScreen === monitor)
                root.consoleScreen = "";
        }
    }
    // At start (a shell reload with the console open): lastIpcObject is filled by the refresh.
    Timer {
        interval: 1000
        running: true
        onTriggered: root.readMonitors()
    }
    Component.onCompleted: {
        Hyprland.refreshMonitors();
        probe.running = true;
    }
}
