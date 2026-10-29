pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// While the dynamic theme is the current one, every wallpaper change generates it again from the new image,
// whoever changed the wallpaper (the panel, Custom..., Super+Ctrl+W). theme.py records the source it used,
// so the wallpaper it applies itself is not generated twice.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/theme.py"
    readonly property string stateHome: Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state"
    readonly property string configHome: Quickshell.env("XDG_CONFIG_HOME") || Quickshell.env("HOME") + "/.config"
    property string theme: ""
    // The current wallpaper source; the one watcher of selection.json, also read by Theming and BarStyle.
    property string wallpaper: ""
    property string source: ""
    readonly property bool active: theme === "dynamic"
    readonly property bool stale: active && wallpaper !== "" && wallpaper !== source
    property bool pending: false
    readonly property bool running: generator.running
    function parse(text) {
        try {
            return JSON.parse(text) ?? {};
        } catch (failure) {
            return {};
        }
    }
    function update() {
        if (!stale)
            return;
        // A change during a run is generated after it, from whatever the wallpaper is by then.
        if (generator.running) {
            pending = true;
            return;
        }
        generator.running = true;
    }
    onStaleChanged: update()
    Process {
        id: generator
        command: ["python3", root.helper, "generate"]
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "")
                    console.warn("dynamic theme:", text.trim());
            }
        }
        onExited: {
            dynamicFile.reload();
            if (root.pending) {
                root.pending = false;
                root.update();
            }
        }
    }
    FileView {
        path: root.stateHome + "/desktop-theme/current.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.theme = root.parse(text()).theme ?? ""
        onLoadFailed: root.theme = ""
    }
    FileView {
        path: root.stateHome + "/desktop-session/wallpaper/selection.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.wallpaper = root.parse(text()).source ?? ""
    }
    FileView {
        id: dynamicFile
        path: root.configHome + "/desktop/themes/dynamic/theme.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.source = root.parse(text()).source ?? ""
        onLoadFailed: root.source = ""
    }
}
