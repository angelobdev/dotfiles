pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."
import "BindKeys.js" as BindKeys

// Hyprland settings chosen in Settings: the keyboard layout, personal shortcuts and the language of the assistant.
// They are kept under "hyprland" in ~/.config/desktop/shell.json (Config.set) and rendered into
// ~/.config/desktop/settings.lua by hyprsettings.py; hyprland.lua loads that before hypr.lua of the user, and
// Hyprland reloads it on its own.
Singleton {
    id: root
    readonly property var current: (Config.user.hyprland && typeof Config.user.hyprland === "object" && !Array.isArray(Config.user.hyprland)) ? Config.user.hyprland : ({})
    readonly property string layout: current.keyboard?.layout ?? ""
    readonly property string variant: current.keyboard?.variant ?? ""
    readonly property string language: current.assistantLanguage ?? ""
    readonly property var binds: Array.isArray(current.binds) ? current.binds : []
    // Per monitor name: { mode, position, scale } as chosen in Settings → Displays.
    readonly property var monitors: (current.monitors && typeof current.monitors === "object" && !Array.isArray(current.monitors)) ? current.monitors : ({})
    // What hyprsettings.py left out as not valid, by name (keyboard, assistantLanguage, binds.N).
    property var skipped: []
    property string error: ""
    // The layout Hyprland uses now, shown when none is chosen here.
    property string active: ""
    // Every bind Hyprland has now outside submaps, as { mask, key, description }, to warn about taken keys.
    property var taken: []
    function combo(text) {
        return BindKeys.combo(text);
    }
    // The binds already on these keys, except the one this row itself put there (same description).
    function takenBy(keys, description) {
        return BindKeys.takenBy(taken, keys, description);
    }
    // The same checks as hyprsettings.py, so a field can say what is wrong before it is saved.
    function validLayout(text) {
        return /^[a-z]{2,8}(,[a-z]{2,8})*$/.test(text);
    }
    function validVariant(text) {
        return /^[a-z0-9_-]*(,[a-z0-9_-]*)*$/.test(text);
    }
    function validKeys(text) {
        return BindKeys.valid(text);
    }
    // Empty parts drop out, so a cleared setting leaves no trace in shell.json.
    function save(next) {
        const cleaned = {};
        const keyboard = next.keyboard ?? {};
        if ((keyboard.layout ?? "") !== "")
            cleaned.keyboard = {
                layout: keyboard.layout,
                variant: keyboard.variant ?? ""
            };
        if ((next.assistantLanguage ?? "") !== "")
            cleaned.assistantLanguage = next.assistantLanguage;
        if ((next.binds ?? []).length > 0)
            cleaned.binds = next.binds;
        if (Object.keys(next.monitors ?? {}).length > 0)
            cleaned.monitors = next.monitors;
        if (!Config.set("hyprland", cleaned, {})) {
            error = I18n.tr("settings.unreadable", [Config.directory + "/shell.json"]);
            return;
        }
        error = "";
        renderer.command = ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/hyprsettings.py", "render", "--json", JSON.stringify(cleaned)];
        renderer.running = true;
    }
    function setKeyboard(layout, variant) {
        save(Object.assign({}, current, {
            keyboard: {
                layout: layout.trim(),
                variant: variant.trim()
            }
        }));
    }
    function setLanguage(language) {
        save(Object.assign({}, current, {
            assistantLanguage: language
        }));
    }
    // A monitor's settings, or null to give it back to its own rules.
    function setMonitor(name, fields) {
        const monitors = Object.assign({}, current.monitors ?? {});
        if (fields)
            monitors[name] = fields;
        else
            delete monitors[name];
        save(Object.assign({}, current, {
            monitors: monitors
        }));
    }
    // All monitors at once (the revert of Settings → Displays).
    function setMonitors(monitors) {
        save(Object.assign({}, current, {
            monitors: monitors
        }));
    }
    function setBinds(list) {
        save(Object.assign({}, current, {
            binds: list
        }));
    }
    function readActive() {
        if (!reader.running)
            reader.running = true;
        if (!bindReader.running)
            bindReader.running = true;
    }
    Process {
        id: bindReader
        command: ["hyprctl", "binds", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.taken = JSON.parse(text).filter(bind => bind.submap === "" && !bind.mouse).map(bind => ({
                                mask: bind.modmask,
                                key: String(bind.key).toLowerCase(),
                                description: bind.description || bind.key
                            }));
                } catch (failure) {
                    root.taken = [];
                }
            }
        }
    }
    Process {
        id: renderer
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.skipped = JSON.parse(text).skipped ?? [];
                } catch (failure) {
                    root.skipped = [];
                }
            }
        }
        stderr: StdioCollector {
            onStreamFinished: if (text.trim() !== "")
                root.error = text.trim()
        }
        // Hyprland reloads settings.lua by itself; the layout it then uses is read again.
        onExited: activeLater.restart()
    }
    Timer {
        id: activeLater
        interval: 700
        onTriggered: root.readActive()
    }
    Process {
        id: reader
        command: ["hyprctl", "getoption", "input:kb_layout", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.active = JSON.parse(text).str ?? "";
                } catch (failure) {
                    root.active = "";
                }
            }
        }
    }
}
