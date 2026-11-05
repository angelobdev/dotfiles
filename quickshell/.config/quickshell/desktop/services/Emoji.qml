pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."

// The emoji picker: the list from emoji.py, read the first time the picker opens, the recently used ones
// (session state), and putting one into the window that was focused: copied, then pasted with Ctrl + V, or
// Ctrl + Shift + V when that window is a terminal. Terminals are told by their process, not their class: kitty
// windows of the assistant and others carry their own classes. (Shift + Insert would paste the primary
// selection in kitty, which is off here: misc:middle_click_paste.)
Singleton {
    id: root
    property var groups: []
    property var emoji: []
    property string error: ""
    property bool loaded: false
    readonly property var recent: SessionState.emojiRecent === "" ? [] : SessionState.emojiRecent.split(" ")
    // The window to paste into, taken when the picker opens.
    property string target: ""
    readonly property var terminals: ["kitty", "foot", "alacritty", "wezterm-gui", "konsole", "ptyxis", "gnome-terminal-"]

    function load() {
        if (!loaded && !lister.running)
            lister.running = true;
    }
    function remember() {
        target = Hyprland.activeToplevel?.address ?? "";
    }
    function pick(character) {
        SessionState.set("emojiRecent", [character].concat(recent.filter(e => e !== character)).slice(0, 24).join(" "));
        Quickshell.execDetached(["wl-copy", "--", character]);
        ShellState.close();
        if (target !== "")
            clients.running = true;
    }
    // The pid of the target window from Hyprland (the toplevel's IPC data can still be empty for a new window),
    // its process name, then the paste once the picker has closed.
    Process {
        id: clients
        command: ["hyprctl", "clients", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                let pid = 0;
                try {
                    const address = root.target.startsWith("0x") ? root.target : "0x" + root.target;
                    pid = JSON.parse(text).find(c => c.address === address)?.pid ?? 0;
                } catch (failure) {}
                process.name = "";
                process.command = ["cat", "/proc/" + pid + "/comm"];
                process.running = true;
            }
        }
    }
    Process {
        id: process
        property string name: ""
        stdout: StdioCollector {
            onStreamFinished: process.name = text.trim()
        }
        onExited: paste.restart()
    }
    Timer {
        id: paste
        interval: 120
        onTriggered: {
            const address = root.target.startsWith("0x") ? root.target : "0x" + root.target;
            const terminal = root.terminals.some(name => process.name.startsWith(name));
            Hyprland.dispatch("hl.dsp.send_shortcut({ mods = \"" + (terminal ? "CTRL SHIFT" : "CTRL") + "\", key = \"V\", window = \"address:" + address + "\" })");
        }
    }
    Process {
        id: lister
        command: ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/emoji.py", "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    root.groups = data.groups ?? [];
                    root.emoji = data.emoji ?? [];
                    root.error = data.error ?? "";
                    root.loaded = root.error === "";
                } catch (failure) {
                    root.error = I18n.tr("emoji.errors.unreadable");
                }
            }
        }
    }
}
