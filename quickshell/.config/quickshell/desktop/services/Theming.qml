pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Data and actions for the Theming panel, all through theme.py; queried only while the panel is open.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/theme.py"
    readonly property string wallpaperHelper: Quickshell.env("HOME") + "/.local/libexec/desktop/wallpaper.py"
    property var themes: []
    // Corner rounding and border width of windows, as Hyprland applies them now.
    property var windows: ({
            rounding: 16,
            borderSize: 0
        })
    property string current: ""
    // The theme generated from the wallpaper: whether matugen is installed, its mode and palette style.
    property var dynamic: ({
            available: false,
            mode: "auto",
            scheme: "tonal-spot",
            source: null
        })
    // Shipped and user themes, then the dynamic one, with the colours it was generated with last, if any.
    readonly property var themeItems: themes.filter(t => t.id !== "dynamic").concat([
        {
            id: "dynamic",
            dynamic: true,
            name: "",
            preview: themes.find(t => t.id === "dynamic")?.preview ?? null
        }
    ])
    // Thumbnail of the current wallpaper when the gallery has one; else the image itself.
    readonly property string wallpaperThumb: wallpaperItems.find(e => e.path === wallpaper && e.thumb !== "")?.thumb ?? wallpaper
    property var pack: ({
            wallpapers: [],
            files: []
        })
    property var fonts: ({
            sans: [],
            mono: [],
            theme: {},
            effective: {},
            chosen: {}
        })
    property var icons: ({
            themes: [],
            theme: "",
            chosen: null
        })
    property string wallpaper: ""
    // Fonts and icons reach the shell through the Qt platform theme, read at startup. After such a change
    // the panel offers a restart, which reopens it on this tab; the user decides when.
    property string restartTab: ""
    property string error: ""
    // Message under the Other... field of the font or icon lists.
    property string customError: ""
    property string customKind: ""
    property var customCommand: []
    property var queue: []
    readonly property bool busy: action.running || queue.length > 0
    readonly property bool downloading: fetcher.running
    readonly property var wallpaperItems: {
        const entries = pack.wallpapers.length > 0 ? pack.wallpapers.map(e => ({
                    path: e.path,
                    name: e.file,
                    downloaded: e.downloaded,
                    thumb: e.thumbReady ? e.thumb : ""
                })) : pack.files.map(p => ({
                    path: p,
                    name: p.split("/").pop(),
                    downloaded: true,
                    thumb: pack.thumbsReady?.[p] ? pack.thumbs[p] : ""
                }));
        return entries.concat([
            {
                custom: true,
                path: "",
                name: "",
                downloaded: true,
                thumb: ""
            }
        ]);
    }
    readonly property bool missingWallpapers: pack.wallpapers.some(e => !e.downloaded)
    function refresh() {
        error = "";
        listing.running = true;
        packQuery.running = true;
        fontQuery.running = true;
        iconQuery.running = true;
    }
    // Commands run one after another, so a wallpaper is applied before it is remembered.
    function run(commands) {
        queue = queue.concat(commands);
        if (!action.running)
            next();
    }
    function next() {
        if (queue.length === 0) {
            listing.running = true;
            packQuery.running = true;
            fontQuery.running = true;
            iconQuery.running = true;
            return;
        }
        action.command = queue[0];
        queue = queue.slice(1);
        action.running = true;
    }
    function setTheme(id) {
        if (id !== current)
            run([["python3", helper, "set", id]]);
    }
    function generate() {
        if (dynamic.available)
            run([["python3", helper, "generate"]]);
    }
    function setDynamic(option, value) {
        run([["python3", helper, "dynamic", "--" + option, value]]);
    }
    function setWallpaper(path) {
        run([["python3", wallpaperHelper, path], ["python3", helper, "remember-wallpaper", path]]);
    }
    function setFont(kind, family) {
        restartTab = "font";
        // An empty family clears the preference, so the font of the theme applies again.
        run([["python3", helper, "font", "--" + kind, family]]);
    }
    function setSize(size) {
        restartTab = "font";
        run([["python3", helper, "font", "--size", String(size)]]);
    }
    function setUnified(on) {
        restartTab = "font";
        run([["python3", helper, "font", "--unified", on ? "on" : "off"]]);
    }
    function setIcons(id) {
        restartTab = "icons";
        run([["python3", helper, "icon-theme", id === "" ? "default" : id]]);
    }
    function setShellIcons(source) {
        restartTab = "icons";
        run([["python3", helper, "shell-icons", source]]);
    }
    function setWindowStyle(option, value) {
        run([["python3", helper, "window-style", option === "rounding" ? "--rounding" : "--border", String(value)]]);
    }
    function setBarStyle(style) {
        run([["python3", helper, "bar-style", style]]);
    }
    // A family or icon theme typed by hand is checked first, then applied like a list entry.
    function applyCustom(kind, name) {
        name = name.trim();
        if (name === "" || checker.running)
            return;
        customError = "";
        customKind = kind;
        customCommand = kind === "icons" ? ["icon-theme", name] : ["font", "--" + kind, name];
        checker.command = ["python3", helper, kind === "icons" ? "check-icons" : "check-font", name];
        checker.running = true;
    }
    function openFolder(kind) {
        run([["python3", helper, "open-folder", kind]]);
    }
    // Fonts added by hand reach fontconfig after a cache refresh; icon packs are picked up directly.
    function rescan(kind) {
        if (kind === "fonts")
            run([["fc-cache", "-f"]]);
        else
            refresh();
    }
    function restartShell() {
        const tab = restartTab || "theme";
        restartTab = "";
        Quickshell.execDetached([Quickshell.env("HOME") + "/.local/bin/desktop-shell", "restart", "theming", tab]);
    }
    function makeThumbs() {
        if (!thumbnailer.running)
            thumbnailer.running = true;
    }
    function fetch() {
        if (!fetcher.running)
            fetcher.running = true;
    }

    function parse(text, fallback) {
        try {
            return JSON.parse(text);
        } catch (failure) {
            return fallback;
        }
    }
    Process {
        id: action
        stderr: StdioCollector {
            id: actionErrors
        }
        onExited: (code, status) => {
            if (code !== 0) {
                root.error = actionErrors.text.trim();
                root.queue = [];
            }
            root.next();
        }
    }
    Process {
        id: checker
        stderr: StdioCollector {
            id: checkErrors
        }
        onExited: (code, status) => {
            if (code !== 0) {
                root.customError = checkErrors.text.trim();
                return;
            }
            root.restartTab = root.customKind === "icons" ? "icons" : "font";
            root.run([["python3", root.helper].concat(root.customCommand)]);
        }
    }
    // One JSON line per thumbnail; the gallery refreshes as they appear.
    Process {
        id: thumbnailer
        command: ["python3", root.helper, "thumbs"]
        stdout: SplitParser {
            onRead: data => {
                if (root.parse(data, null)?.status === "ready")
                    packQuery.running = true;
            }
        }
        onExited: packQuery.running = true
    }
    Process {
        id: listing
        command: ["python3", root.helper, "list", "--details"]
        stdout: StdioCollector {
            onStreamFinished: {
                const data = root.parse(text, null);
                if (data) {
                    root.themes = data.themes;
                    root.current = data.current;
                    root.windows = data.windows ?? root.windows;
                    root.dynamic = data.dynamic ?? root.dynamic;
                }
            }
        }
    }
    Process {
        id: packQuery
        command: ["python3", root.helper, "wallpapers"]
        stdout: StdioCollector {
            onStreamFinished: root.pack = root.parse(text, root.pack)
        }
    }
    Process {
        id: fontQuery
        command: ["python3", root.helper, "fonts"]
        stdout: StdioCollector {
            onStreamFinished: root.fonts = root.parse(text, root.fonts)
        }
    }
    Process {
        id: iconQuery
        command: ["python3", root.helper, "icons"]
        stdout: StdioCollector {
            onStreamFinished: root.icons = root.parse(text, root.icons)
        }
    }
    // One JSON line per file; each finished download refreshes the gallery.
    Process {
        id: fetcher
        command: ["python3", root.helper, "fetch"]
        stdout: SplitParser {
            onRead: data => {
                const line = root.parse(data, null);
                if (line?.status === "downloaded")
                    packQuery.running = true;
                else if (line?.status === "failed")
                    root.error = line.error;
            }
        }
        onExited: packQuery.running = true
    }
    // wallpaper.py records every applied wallpaper here, whoever applied it.
    FileView {
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session/wallpaper/selection.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.wallpaper = root.parse(text(), {}).source ?? ""
    }
}
