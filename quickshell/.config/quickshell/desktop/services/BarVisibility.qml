pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root
    property var hiddenMonitors: []
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/bar_visibility.py"
    function hidden(name) {
        return hiddenMonitors.indexOf(name) !== -1;
    }
    // The overview is about to open: read the layers often for a while (bar_visibility.py).
    function wake() {
        if (watcher.running)
            watcher.write("wake\n");
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
