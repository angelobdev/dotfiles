import QtQuick
import Quickshell
import ".."

// A panel window created when it opens and dropped Config.panelKeepSeconds after it closes, so closed panels
// cost no memory. One reopened meanwhile is still there; one busy (a running command) stays until it is done.
// What a panel keeps between openings lives in ShellState.recall / remember.
LazyLoader {
    id: root
    required property string name
    readonly property bool open: ShellState.panel === name
    property Timer keep: Timer {
        interval: Config.panelKeepSeconds * 1000
        // Checked each time the time is up, not bound (item depends on active): another round while busy.
        repeat: true
        onTriggered: if (!root.item?.busy)
            stop()
    }
    onOpenChanged: if (!open)
        keep.restart()
    active: open || keep.running
}
