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
    Process {
        id: watcher
        command: ["python3", root.helper]
        running: true
        stdout: SplitParser {
            onRead: data => {
                try {
                    root.hiddenMonitors = JSON.parse(data);
                } catch (error) {
                    root.hiddenMonitors = [];
                }
            }
        }
        onExited: {
            root.hiddenMonitors = [];
            retry.restart();
        }
    }
    Timer {
        id: retry
        interval: 2000
        onTriggered: watcher.running = true
    }
}
