pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."

// The AI coding assistant (desktop-ai) and its drop-down console, the special workspace "ai" laid out
// by hypr/config/console.lua: which agent is configured or detected, which screen shows the console, what
// the agent is doing (agent.json from hooks or session watching in agent.py), optional rate-limit usage,
// and notifications sent while the console is hidden.
Singleton {
    id: root
    readonly property string launcher: Quickshell.env("HOME") + "/.local/bin/desktop-ai"
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/agent.py"
    readonly property string runtimeDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/desktop-shell"
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell"
    readonly property string configuredAgent: Config.aiAgent
    readonly property string configuredDirectory: Config.aiDirectory
    property bool available: false
    property bool probeLoaded: false
    property string probedAgent: ""
    property string probedName: ""
    property string autoAgent: ""
    property string autoName: ""
    property var installedAgents: []
    property bool agyStatusline: false
    property bool agyStatuslineCustom: false
    property var sessionRecord: ({})
    readonly property bool running: Hyprland.toplevels.values.some(t => (t.wayland?.appId || t.lastIpcObject?.class) === "desktop-ai")
    readonly property string sessionAgent: running ? ((sessionRecord.agent || record.agent) ?? "") : ""
    readonly property string sessionName: running ? ((sessionRecord.name || record.name) ?? "") : ""
    readonly property string sessionDirectory: running ? (sessionRecord.directory ?? "") : ""
    readonly property string watchedAgent: sessionAgent !== "" ? sessionAgent : probedAgent
    readonly property string agent: running && sessionAgent !== "" ? sessionAgent : probedAgent
    readonly property string name: running && sessionName !== "" ? sessionName : (probedName !== "" ? probedName : I18n.tr("assistant.title"))
    readonly property bool hasNamedAgent: (running && sessionName !== "") || probedName !== ""
    readonly property bool needsRestart: running && available && probedAgent !== "" && sessionAgent !== "" && probedAgent !== sessionAgent
    // The screen showing the console, or "" while it is hidden.
    property string consoleScreen: ""
    readonly property bool consoleOpen: consoleScreen !== ""
    property var record: ({})
    // The first read (a shell start) only takes the state: notifications are for changes after it.
    property bool recordLoaded: false
    // ready, working, permission, finished or error; "" when the agent is not running or reported nothing yet.
    readonly property string state: running ? record.state ?? "" : ""
    readonly property string detail: running ? record.detail ?? "" : ""
    readonly property real since: (record.since ?? 0) * 1000
    // Finished, failed or asking while the console was hidden, and not looked at since.
    property bool unseen: false
    property var rawUsage: ({})
    readonly property var usage: {
        const recorded = rawUsage.agent ?? "";
        if (recorded === "" ? agent === "claude" : recorded === agent)
            return rawUsage;
        return {};
    }
    readonly property string plan: {
        const tier = (usage.tier ?? "").toLowerCase();
        const match = /max_(\d+)x/.exec(tier);
        if (match)
            return I18n.tr("assistant.plans.max", [match[1]]);
        if (/max/.test(tier))
            return I18n.tr("assistant.plans.maxPlain");
        if (/ultra/.test(tier))
            return I18n.tr("assistant.plans.ultra");
        if (/pro/.test(tier))
            return I18n.tr("assistant.plans.pro");
        return "";
    }
    readonly property bool hasBuckets: Array.isArray(usage.buckets) && usage.buckets.length > 0
    readonly property bool hasWindows: (usage.fiveHour !== null && usage.fiveHour !== undefined) || (usage.sevenDay !== null && usage.sevenDay !== undefined)
    readonly property bool hasLimits: hasBuckets || hasWindows || (agent === "claude" && plan !== "")
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
    function restartConsole() {
        Quickshell.execDetached([launcher, "restart"]);
    }
    function openHere() {
        Quickshell.execDetached([launcher, "here"]);
    }
    function setAgyStatusline(enable) {
        agyToggle.action = enable ? "on" : "off";
        agyToggle.running = false;
        agyToggle.running = true;
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
            notify(I18n.tr("assistant.notices.permission", [name]), detail);
        else if (state === "finished")
            notify(I18n.tr("assistant.notices.finished", [name]), detail);
        else
            notify(I18n.tr("assistant.notices.error", [name]), detail);
    }
    onConfiguredAgentChanged: {
        probe.running = false;
        probe.running = true;
    }
    onConfiguredDirectoryChanged: {
        probe.running = false;
        probe.running = true;
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
        command: ["notify-send", "--wait", "--app-name=" + root.name, "--app-icon=desktopai", "--hint=string:desktop-entry:desktop-ai", "--action=default=" + I18n.tr("assistant.openConsole"), "--action=open=" + I18n.tr("assistant.openConsole"), title, body]
        stdout: StdioCollector {
            onStreamFinished: {
                if (["default", "open"].includes(text.trim()))
                    root.showConsole();
            }
        }
    }
    Process {
        id: probe
        command: ["python3", root.helper, "probe"]
        stdout: StdioCollector {
            onStreamFinished: {
                const info = root.parse(text);
                root.available = Boolean(info.available);
                root.probedAgent = info.agent ?? "";
                root.probedName = info.name ?? "";
                root.autoAgent = info.autoAgent ?? "";
                root.autoName = info.autoName ?? "";
                root.installedAgents = Array.isArray(info.installed) ? info.installed : [];
                root.agyStatusline = Boolean(info.agyStatusline);
                root.agyStatuslineCustom = Boolean(info.agyStatuslineCustom);
                root.probeLoaded = true;
            }
        }
        onExited: code => {
            if (code !== 0) {
                root.available = false;
                root.probeLoaded = true;
            }
        }
    }
    Process {
        id: agyToggle
        property string action: "on"
        command: ["python3", root.helper, "agy-statusline", action]
        stdout: StdioCollector {
            onStreamFinished: {
                const info = root.parse(text);
                if (info.enabled !== undefined)
                    root.agyStatusline = Boolean(info.enabled);
                if (info.custom !== undefined)
                    root.agyStatuslineCustom = Boolean(info.custom);
                probe.running = false;
                probe.running = true;
            }
        }
    }
    // Non-Claude agents do not get per-window --settings hooks: agent.py watches their session files while the
    // console window exists, pinned to the harness of the running window, and removes agent.json when it closes.
    Process {
        id: watcher
        running: root.running && root.probeLoaded && root.watchedAgent !== "" && root.watchedAgent !== "claude"
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", root.helper, "watch", root.watchedAgent])
        stderr: SplitParser {
            onRead: line => console.warn("agent.py:", line)
        }
    }
    FileView {
        path: root.runtimeDir + "/agent-session.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.sessionRecord = root.parse(text())
        onLoadFailed: root.sessionRecord = {}
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
        onLoaded: root.rawUsage = root.parse(text())
        onLoadFailed: root.rawUsage = {}
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
    // A console on a monitor that went away is no longer open: it would keep holding back every notification.
    Connections {
        target: Quickshell
        function onScreensChanged() {
            if (root.consoleScreen !== "" && !Quickshell.screens.some(screen => screen.name === root.consoleScreen))
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
