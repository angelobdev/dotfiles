import QtQuick
import Quickshell.Io

// A long-lived helper the shell keeps running while wanted: started and stopped with wanted, and started again
// when it exits while still wanted, later after each quick failure (Backoff: 3 s, doubled after each run shorter
// than a minute, up to a minute), so a helper that fails at start does not respawn every few seconds all session.
// Its stderr reaches qs log under name, unless the use collects stderr itself.
Process {
    id: root
    property bool wanted: true
    property string name: ""
    property alias retryBase: backoff.base
    stderr: SplitParser {
        onRead: line => console.warn(root.name + ":", line)
    }
    onWantedChanged: {
        retry.stop();
        running = wanted;
    }
    Component.onCompleted: running = wanted
    onStarted: backoff.started()
    onExited: {
        backoff.ended();
        if (wanted)
            retry.restart();
    }
    readonly property Backoff backoff: Backoff {
        id: backoff
        base: 3000
    }
    readonly property Timer retry: Timer {
        id: retry
        interval: backoff.interval
        onTriggered: if (root.wanted && !root.running)
            root.running = true
    }
}
