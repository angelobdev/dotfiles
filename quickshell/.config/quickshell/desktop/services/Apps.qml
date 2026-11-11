pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."
import "LauncherRank.js" as Rank

// Launches desktop entries for the launcher and the dock, and remembers when, so the launcher can list the apps in
// use first: launches.json in the shell state, off and cleared from Settings → Privacy (Config.launcherHistory).
Singleton {
    id: root
    readonly property string stateFile: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell/launches.json"
    // Desktop-entry id -> launch times (ms), oldest first; trimmed by LauncherRank.js.
    property var launches: ({})
    readonly property int remembered: Object.keys(launches).length
    function launch(entry) {
        if (!entry)
            return;
        // Never pass desktop-file Exec strings through a shell.
        if (entry.runInTerminal)
            Quickshell.execDetached({
                command: ["kitty", "-e"].concat(entry.command),
                workingDirectory: entry.workingDirectory || Quickshell.env("HOME")
            });
        else
            entry.execute();
        remember(entry.id);
    }
    function remember(id) {
        if (!Config.launcherHistory || !id)
            return;
        launches = Rank.record(launches, id, Date.now());
        saver.restart();
    }
    function clearHistory() {
        launches = {};
        saver.stop();
        file.setText(Rank.serialize(launches));
    }
    // Launches in a row are written once.
    Timer {
        id: saver
        interval: 2000
        onTriggered: file.setText(Rank.serialize(root.launches))
    }
    // Only the shell writes this file; a missing or broken one is an empty history.
    FileView {
        id: file
        path: root.stateFile
        // Read at once: a launch saved before the first read would write the rest of the history away.
        blockLoading: true
        atomicWrites: true
        printErrors: false
        onLoaded: root.launches = Rank.parse(text(), Date.now())
    }
}
