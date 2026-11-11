pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// The options of the shell. ~/.config/desktop/shell.json changes any of them by name, as in
// {"dockIconSize": 48, "primaryMonitor": "DP-1"}: it lives outside this repository, so a pull never meets a
// local change. The file is watched; a value of another type than the default keeps the default.
// Settings writes it too (set, reset): only values that differ from the default, other keys left as they are.
Singleton {
    id: root
    property var user: ({})
    // The file exists but is not a JSON object: Settings leaves it alone instead of writing over it.
    property bool unreadable: false
    function isSet(name) {
        return user[name] !== undefined && user[name] !== null;
    }
    // A value equal to the default removes the option, so the file keeps only what was changed.
    function set(name, value, fallback) {
        const next = Object.assign({}, user);
        if (JSON.stringify(value) === JSON.stringify(fallback))
            delete next[name];
        else
            next[name] = value;
        return save(next);
    }
    function reset(name) {
        const next = Object.assign({}, user);
        delete next[name];
        return save(next);
    }
    // Several options back to their defaults at once (Settings → System → Advanced).
    function resetMany(names) {
        const next = Object.assign({}, user);
        for (const name of names)
            delete next[name];
        return save(next);
    }
    function save(next) {
        if (unreadable)
            return false;
        user = next;
        pending = JSON.stringify(next, null, 2) + "\n";
        // ~/.config/desktop may not exist yet on a new install: made once before the first write.
        if (folderMade)
            file.setText(pending);
        else if (!folder.running)
            folder.running = true;
        return true;
    }
    readonly property string directory: (Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config") + "/desktop"
    property string pending: ""
    property bool folderMade: false
    Process {
        id: folder
        command: ["mkdir", "-p", root.directory]
        onExited: code => {
            root.folderMade = code === 0;
            if (root.folderMade)
                file.setText(root.pending);
        }
    }
    function pick(name, fallback) {
        const value = user[name];
        if (value === undefined || value === null)
            return fallback;
        if (typeof value !== typeof fallback || Array.isArray(value) !== Array.isArray(fallback)) {
            console.warn("shell.json:", name, "should be like", JSON.stringify(fallback));
            return fallback;
        }
        return value;
    }
    function parse(text) {
        unreadable = false;
        // An empty file is an empty set of options.
        if (text.trim() === "")
            return {};
        try {
            const value = JSON.parse(text);
            if (value && typeof value === "object" && !Array.isArray(value))
                return value;
            console.warn("shell.json: not a JSON object");
        } catch (error) {
            console.warn("shell.json:", error);
        }
        unreadable = true;
        return {};
    }
    FileView {
        id: file
        path: root.directory + "/shell.json"
        blockLoading: true
        watchChanges: true
        printErrors: false
        // Written whole through a temporary file: a reader never sees half of it.
        atomicWrites: true
        onFileChanged: reload()
        onLoaded: root.user = root.parse(text())
        onLoadFailed: {
            root.unreadable = false;
            root.user = ({});
        }
    }
    readonly property int minimumWorkspaces: pick("minimumWorkspaces", 2)
    // The coding agent Super + A opens (an id of agents.py, Settings → Assistant); "" picks the first installed.
    readonly property string aiPrimary: pick("aiPrimary", "")
    readonly property bool workspaceScroll: pick("workspaceScroll", true)
    // Numbers in the workspace pills of the bar instead of bare dots.
    readonly property bool workspaceNumbers: pick("workspaceNumbers", false)
    // Turns the shell's own animations off (Hyprland's live in hypr/config/appearance.lua).
    readonly property bool reduceMotion: pick("reduceMotion", false)
    readonly property bool clipboardEnabled: pick("clipboardEnabled", true)
    readonly property int clipboardMaxItems: pick("clipboardMaxItems", 200)
    readonly property int recordingFramerate: pick("recordingFramerate", 30)
    readonly property string recordingCodec: pick("recordingCodec", "libvpx-vp9")
    // Desktop-entry IDs the launcher leaves out: GNOME Settings (GDM needs it, it runs only in GNOME) and the
    // OpenCASCADE tool that the plugin build dependencies bring, and the uwsm unit menu.
    // Weather in the calendar panel (Open-Meteo). An empty city means where GeoClue says the computer is.
    readonly property bool weatherEnabled: pick("weatherEnabled", true)
    readonly property string weatherCity: pick("weatherCity", "")
    // Bar: what plays, with play/pause on a click (MPRIS).
    readonly property bool barMedia: pick("barMedia", true)
    // Launcher: files in the home folder below the apps (fd, from three typed characters).
    readonly property bool launcherFiles: pick("launcherFiles", true)
    // Launcher: apps opened from it or the dock come first, by how often and how lately (services/Apps.qml).
    readonly property bool launcherHistory: pick("launcherHistory", true)
    readonly property var launcherHidden: pick("launcherHidden", ["org.gnome.Settings", "opencascade-draw", "uuctl"])
    // Dock: desktop-entry IDs pinned in this order, a reveal strip along the bottom edge (logical px) and its hover delay (ms).
    // An ID with no entry is skipped: Zen is zen-browser on Fedora, zen from the AUR on Arch.
    readonly property bool dockEnabled: pick("dockEnabled", true)
    readonly property var dockPinned: pick("dockPinned", ["kitty", "zen-browser", "zen", "org.gnome.Nautilus", "com.microsoft.VSCode", "steam"])
    readonly property int dockIconSize: pick("dockIconSize", 44)
    // Peak scale of the icon under the pointer; 1 turns magnification off.
    readonly property real dockMagnification: pick("dockMagnification", 1.4)
    readonly property int dockTriggerHeight: pick("dockTriggerHeight", 3)
    readonly property int dockRevealDelay: pick("dockRevealDelay", 120)
    // Assist button (touch): the pages of its menu with their actions in order (names in services/Assist.qml:
    // also window, the window menu), and what a long press on the button runs.
    readonly property var assistPages: pick("assistPages", [
        {
            name: "apps",
            actions: ["keyboard", "assistant", "launcher", "dock", "overview", "notifications", "controls", "emoji", "workspacePrevious", "workspaceNext"]
        },
        {
            name: "window",
            actions: ["windowClose", "windowFullscreen", "windowFloating", "windowSplit", "windowLeft", "windowRight", "windowToPrevious", "windowToNext"]
        },
        {
            name: "system",
            actions: ["screenshotArea", "screenshotDisplay", "areaText", "areaAsk", "recording", "clipboard", "theming", "wallpaper", "nextWallpaper", "colorPicker", "zoom", "hints", "lock", "session", "rotationLock"]
        }
    ])
    readonly property string assistLongPress: pick("assistLongPress", "keyboard")
    // On-screen keyboard layout: osk/layouts/<name>.json, matching the Hyprland kb_layout.
    readonly property string oskLayout: pick("oskLayout", "it")
    // In tablet mode, open the keyboard when a text field takes the focus (apps with text-input-v3).
    readonly property bool oskAutoShow: pick("oskAutoShow", true)
    // Likely next letters are a little easier to hit, from Italian and English word lists fetched on first use.
    readonly property bool oskPrediction: pick("oskPrediction", true)
    // Learns the words typed in ordinary fields, as single words with a count, for the suggestions.
    readonly property bool oskLearning: pick("oskLearning", true)
    // Keeps totals of how far touches land from the centre of their letter, never which letter or when.
    readonly property bool oskTouchStats: pick("oskTouchStats", true)
    // In tablet mode the shell hit targets (bar, buttons, switches, rows, dock icons) grow by this factor.
    readonly property real touchScale: pick("touchScale", 1.25)
    // Order and presence of modules. Unknown names are ignored.
    readonly property var controlCenterModules: pick("controlCenterModules", ["network", "bluetooth", "brightness", "audio", "media", "switches"])
    readonly property int controlCenterWidth: pick("controlCenterWidth", 400)
    // Night shift (hyprsunset): its temperature until changed in the Control Center (K), and the automatic
    // window, which may cross midnight.
    readonly property int nightShiftTemperature: pick("nightShiftTemperature", 4000)
    readonly property string nightShiftStart: pick("nightShiftStart", "20:00")
    readonly property string nightShiftEnd: pick("nightShiftEnd", "07:00")
    readonly property bool expandMonitors: pick("expandMonitors", false)
    readonly property bool expandAudioDevices: pick("expandAudioDevices", false)
    // DNS choices in the network details view; each preset lists IPv4 and IPv6 servers.
    readonly property var dnsPresets: pick("dnsPresets", [
        {
            name: "Cloudflare",
            servers: ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"]
        },
        {
            name: "Quad9",
            servers: ["9.9.9.9", "149.112.112.112", "2620:fe::fe", "2620:fe::9"]
        },
        {
            name: "Google",
            servers: ["8.8.8.8", "8.8.4.4", "2001:4860:4860::8888", "2001:4860:4860::8844"]
        },
        {
            name: "AdGuard",
            servers: ["94.140.14.14", "94.140.15.15", "2a10:50c0::ad1:ff", "2a10:50c0::ad2:ff"]
        }
    ])
    // If disconnected, use the first connected screen.
    readonly property string primaryMonitor: pick("primaryMonitor", "eDP-1")
    // Length of a focus session (Do Not Disturb for a while), in minutes.
    readonly property int focusMinutes: pick("focusMinutes", 25)
    // Battery warnings (percent, on battery only): low turns Power Saver on (or offers it), critical stays
    // until dismissed.
    readonly property int batteryLow: pick("batteryLow", 20)
    readonly property int batteryCritical: pick("batteryCritical", 10)
    // Peripheral batteries (stylus, mouse, headset) warn once below this.
    readonly property int peripheralLow: pick("peripheralLow", 15)
    // UPower native-path prefixes of stylus batteries it does not type as a pen: the ELAN pen of the OmniBook
    // reports through the touchscreen controller as a keyboard.
    readonly property var stylusBatteries: pick("stylusBatteries", ["hid-0018:04F3:4302"])
    // OSD: logical pixels and timeout in milliseconds.
    readonly property bool osdEnabled: pick("osdEnabled", true)
    readonly property int osdTimeout: pick("osdTimeout", 1700)
    readonly property int osdWidth: pick("osdWidth", 320)
    readonly property int osdBottomMargin: pick("osdBottomMargin", 96)
    // Empty list includes all enabled GNOME/Online Accounts calendars; otherwise use EDS source UIDs.
    readonly property var calendarSources: pick("calendarSources", [])
    // Internal panels are detected automatically when there is one backlight.
    // External example: ({ "DP-1": { "type": "ddc", "bus": 6 } })
    // Explicit backlight: { "type": "backlight", "device": "intel_backlight" }
    readonly property var brightnessDevices: pick("brightnessDevices", ({}))
    // Panels are created when they open and dropped this long after they close (seconds).
    readonly property int panelKeepSeconds: pick("panelKeepSeconds", 60)
}
