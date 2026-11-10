pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."

// The coding assistant (desktop-ai) and its drop-down console, the special workspace "ai" laid out by
// hypr/config/console.lua: which screen shows it, what the agents are doing, the subscription usage of Claude
// Code status line, and the notifications sent while the console is hidden.
// With herdr installed (herdr-core and herdr-app) the console is the Herdr app and the state comes from
// herdr-core (`hc events`, then `hc ls`), for every agent it recognises; without it, from the hooks of Claude Code
// (desktop-ai, agent.py, agent.json), as before.
Singleton {
    id: root
    readonly property string launcher: Quickshell.env("HOME") + "/.local/bin/desktop-ai"
    readonly property string runtimeDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/desktop-shell"
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell"
    // The coding agents (agents.py list: one JSON file each), the primary one Super + A opens, and herdr.
    property var catalog: ({
            agents: [],
            primary: "",
            chosen: "",
            override: ""
        })
    readonly property var primaryAgent: (catalog.agents ?? []).find(agent => agent.id === catalog.primary) ?? null
    // Claude Code with its hooks: only then does the Kitty console report a detailed state.
    readonly property bool claude: primaryAgent?.hooks === "claude"
    property bool herdr: false
    readonly property bool available: primaryAgent !== null || herdr
    readonly property string title: herdr ? I18n.tr("assistant.agents") : primaryAgent?.name ?? I18n.tr("assistant.title")
    // An agent installed from Settings: its installer in the background (jobs.py), its output there, then the
    // list read again.
    readonly property bool installing: installJob.running || installer.running
    readonly property alias installJob: installJob
    property string installName: ""
    function refreshCatalog() {
        if (!catalogReader.running)
            catalogReader.running = true;
    }
    function install(id) {
        if (installing)
            return;
        installError = "";
        installer.command = ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/agents.py", "install", id];
        installer.running = true;
    }
    property string installError: ""
    readonly property bool windowOpen: Hyprland.toplevels.values.some(t => (t.wayland?.appId || t.lastIpcObject?.class) === (herdr ? "herdr-app" : "desktop-ai"))
    readonly property bool running: herdr ? windowOpen || agents.length > 0 : windowOpen
    // herdr: every terminal running a known agent, as { address, app, name, state (ready, working, permission,
    // finished, error), kind, msg, where, since }, the one needing attention first.
    property var agents: []
    readonly property var lead: agents[0] ?? null
    // The screen showing the console, or "" while it is hidden.
    property string consoleScreen: ""
    readonly property bool consoleOpen: consoleScreen !== ""
    property var record: ({})
    // The first read (a shell start) only takes the state: notifications are for changes after it.
    property bool recordLoaded: false
    // ready, working, permission, finished or error; "" when no agent runs or reported nothing yet.
    // Another agent than Claude Code in the Kitty console has no hooks: it is only "running".
    readonly property string state: herdr ? lead?.state ?? "" : !running ? "" : claude ? record.state ?? "" : "running"
    readonly property string detail: herdr ? lead?.msg ?? "" : running ? record.detail ?? "" : ""
    readonly property real since: herdr ? lead?.since ?? 0 : (record.since ?? 0) * 1000
    // The agent the last notification was about (herdr), shown when it is clicked.
    property string noticeTerminal: ""
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
    // The console on one agent of herdr: its terminal shown in the Herdr app.
    function showAgent(address) {
        showConsole();
        if (herdr && address !== "")
            Quickshell.execDetached(["sh", "-c", "PATH=\"$HOME/.local/bin:$PATH\" exec herdr-app do terminal.show \"$1\"", "sh", JSON.stringify({
                    terminal: address
                })]);
    }
    // The words of herdr-core for the state, as the rest of the shell names them.
    function mapped(status) {
        switch (status?.state) {
        case "blocked":
            return "permission";
        case "done":
            return "finished";
        case "error":
            return "error";
        case "working":
            return "working";
        default:
            return "ready";
        }
    }
    // herdr's name for an agent, as its JSON file names it, else a few herdr knows that have none here.
    function agentName(app) {
        const known = (catalog.agents ?? []).find(agent => agent.herdr === app);
        if (known)
            return known.name;
        const names = {
            "claude-code": "Claude Code",
            "codex": "Codex",
            "opencode": "opencode",
            "cursor": "Cursor",
            "gemini": "Gemini CLI",
            "grok": "Grok"
        };
        return names[app] ?? app;
    }
    // A new `hc ls`: the agents, most urgent first, and a notification for each that moved to asking,
    // finished or failed (none for the first read, a shell start).
    function takeAgents(text) {
        const order = {
            permission: 5,
            error: 4,
            working: 3,
            finished: 2,
            ready: 1
        };
        // `hc ls` says which agents run and their state ("agent", "status" as a word); the events keep the rest of
        // each one (status.msg, status.kind, status_ms), by address.
        let list = [];
        try {
            list = (JSON.parse(text).terminals ?? []).filter(terminal => terminal.state === "live" && (terminal.agent || details[terminal.address]?.status?.app)).map(terminal => {
                const detail = details[terminal.address] ?? {};
                const app = terminal.agent || detail.status?.app;
                const word = typeof terminal.status === "string" ? terminal.status : detail.status?.state;
                return {
                    address: terminal.address,
                    app: app,
                    name: agentName(app),
                    state: mapped({
                        state: word
                    }),
                    kind: detail.status?.kind ?? "",
                    msg: detail.status?.state === word ? detail.status?.msg ?? "" : "",
                    where: terminal.where ?? detail.labels?.where ?? "",
                    since: detail.status_ms ?? 0
                };
            });
        } catch (failure) {
            return;
        }
        list.sort((a, b) => (order[b.state] - order[a.state]) || (b.since - a.since));
        const before = {};
        for (const agent of agents)
            before[agent.address] = agent.state;
        const first = !herdrLoaded;
        agents = list;
        herdrLoaded = true;
        if (first)
            return;
        for (const agent of list)
            if (agent.state !== before[agent.address] && ["permission", "finished", "error"].includes(agent.state))
                agentMoved(agent);
    }
    property bool herdrLoaded: false
    // The last full record of each terminal from `hc events`, by address.
    property var details: ({})
    function takeEvent(line) {
        try {
            const event = JSON.parse(line);
            const next = Object.assign({}, details);
            for (const terminal of event.terminals ?? [])
                if (terminal?.address)
                    next[terminal.address] = terminal;
            details = next;
        } catch (failure) {}
        // Started, not restarted: a steady stream of events (an agent at work) would otherwise keep putting the
        // list off, and the bar stay on the old state.
        if (!relist.running)
            relist.start();
    }
    function agentMoved(agent) {
        if (consoleOpen)
            return;
        unseen = true;
        noticeTerminal = agent.address;
        const key = agent.state === "permission" ? "assistant.notices.agentPermission" : agent.state === "finished" ? "assistant.notices.agentFinished" : "assistant.notices.agentError";
        notify(I18n.tr(key, [agent.name]), [agent.msg, agent.where].filter(part => part !== "").join("\n"));
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
        if (herdr || consoleOpen || !running || !["permission", "finished", "error"].includes(state))
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
        command: ["notify-send", "--wait", "--app-name=" + (root.herdr ? "Herdr" : root.title), "--app-icon=" + (root.herdr ? "herdr-app" : "desktopai"), "--hint=string:desktop-entry:desktop-ai", "--action=default=" + I18n.tr("assistant.openConsole"), "--action=open=" + I18n.tr("assistant.openConsole"), title, body]
        stdout: StdioCollector {
            onStreamFinished: {
                if (["default", "open"].includes(text.trim()))
                    root.herdr ? root.showAgent(root.noticeTerminal) : root.showConsole();
            }
        }
    }
    Process {
        id: catalogReader
        command: ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/agents.py", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                const data = root.parse(text);
                if (Array.isArray(data.agents))
                    root.catalog = data;
            }
        }
    }
    // agents.py install says how; the job runs it.
    Process {
        id: installer
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const value = JSON.parse(text);
                    root.installName = value.name;
                    installJob.start(value.argv, false, I18n.tr("assistant.install.title", [value.name]));
                } catch (failure) {}
            }
        }
        stderr: StdioCollector {
            onStreamFinished: root.installError = text.trim()
        }
    }
    Job {
        id: installJob
        name: "agent-install"
        onFinished: root.refreshCatalog()
    }
    // The primary agent chosen in Settings: read again so the title and the console follow. Only that value:
    // agents.py reads nothing else of shell.json, which every other setting (each slider step) rewrites.
    Connections {
        target: Config
        function onAiPrimaryChanged() {
            root.refreshCatalog();
        }
    }
    // herdr: both programs, unless DESKTOP_AI_CONSOLE=kitty keeps the Kitty console (desktop-ai decides alike).
    Process {
        id: herdrProbe
        command: ["sh", "-c", "[ \"${DESKTOP_AI_CONSOLE:-}\" != kitty ] && PATH=\"$HOME/.local/bin:$PATH\" command -v herdr-core >/dev/null && PATH=\"$HOME/.local/bin:$PATH\" command -v herdr-app >/dev/null"]
        onExited: code => {
            root.herdr = code === 0;
            if (root.herdr) {
                events.running = true;
                lister.request();
            }
        }
    }
    // Each change herdr-core reports asks for the whole list again, at most every 150 ms.
    Process {
        id: events
        command: ["sh", "-c", "PATH=\"$HOME/.local/bin:$PATH\" exec herdr-core events --json"]
        stdout: SplitParser {
            onRead: line => root.takeEvent(line)
        }
        // The stream ends when herdr-core restarts or updates: followed again a little later.
        onExited: if (root.herdr)
            reconnect.restart()
    }
    Timer {
        id: reconnect
        interval: 3000
        onTriggered: {
            events.running = true;
            relist.restart();
        }
    }
    Timer {
        id: relist
        interval: 150
        onTriggered: lister.request()
    }
    // Asked while it runs, it runs once more after: the last change (an agent that finished) is never lost.
    CoalescedProcess {
        id: lister
        command: ["sh", "-c", "PATH=\"$HOME/.local/bin:$PATH\" exec herdr-core ls --json"]
        stdout: StdioCollector {
            onStreamFinished: root.takeAgents(text)
        }
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
        refreshCatalog();
        herdrProbe.running = true;
    }
}
