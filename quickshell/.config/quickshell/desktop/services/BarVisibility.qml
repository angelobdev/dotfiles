pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

Singleton {
    id: root
    property var hiddenMonitors: []
    // Hidden by the user (Super + B, the full-screen desktop): every bar, until shown again or the shell restarts.
    property bool userHidden: false
    // hide, show, toggle (desktop-shell bar, and the "desktop-bar" custom events of binds.lua).
    function request(action) {
        if (action === "hide" || action === "show")
            userHidden = action === "hide";
        else if (action === "toggle")
            userHidden = !userHidden;
        else
            return false;
        return true;
    }
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/bar_visibility.py"
    function hidden(name) {
        return hiddenMonitors.indexOf(name) !== -1;
    }
    // The overview is about to open: read the layers often for a while (bar_visibility.py).
    function wake() {
        if (watcher.running)
            watcher.write("wake\n");
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "custom" && /^desktop-bar (hide|show|toggle)$/.test(event.data))
                root.request(event.data.split(" ")[1]);
        }
    }
    Process {
        id: watcher
        // What a watcher that keeps failing says reaches qs log instead of nowhere.
        stderr: SplitParser {
            onRead: line => console.warn("bar_visibility.py:", line)
        }
        // Ends with the shell, even a killed one (setpriv: the kernel signals it).
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", root.helper])
        running: true
        stdinEnabled: true
        stdout: SplitParser {
            onRead: data => {
                try {
                    root.hiddenMonitors = JSON.parse(data);
                } catch (error) {
                    root.hiddenMonitors = [];
                }
            }
        }
        onStarted: backoff.started()
        onExited: {
            root.hiddenMonitors = [];
            backoff.ended();
            retry.restart();
        }
    }
    Backoff {
        id: backoff
        base: 2000
    }
    Timer {
        id: retry
        interval: backoff.interval
        onTriggered: watcher.running = true
    }
}
