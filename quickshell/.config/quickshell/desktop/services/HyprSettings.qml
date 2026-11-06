pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

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
    // What hyprsettings.py left out as not valid, by name (keyboard, assistantLanguage, binds.N).
    property var skipped: []
    property string error: ""
    // The layout Hyprland uses now, shown when none is chosen here.
    property string active: ""
    // The same checks as hyprsettings.py, so a field can say what is wrong before it is saved.
    function validLayout(text) {
        return /^[a-z]{2,8}(,[a-z]{2,8})*$/.test(text);
    }
    function validVariant(text) {
        return /^[a-z0-9_-]*(,[a-z0-9_-]*)*$/.test(text);
    }
    function validKeys(text) {
        const parts = String(text).split("+").map(part => part.trim());
        if (parts.length === 0 || parts.some(part => part === ""))
            return false;
        const key = parts.pop();
        return parts.every(part => ["SUPER", "SHIFT", "CTRL", "CONTROL", "ALT", "MOD2", "MOD3", "MOD5"].includes(part.toUpperCase())) && /^[A-Za-z0-9_]+$/.test(key);
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
    function setBinds(list) {
        save(Object.assign({}, current, {
            binds: list
        }));
    }
    function readActive() {
        if (!reader.running)
            reader.running = true;
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
