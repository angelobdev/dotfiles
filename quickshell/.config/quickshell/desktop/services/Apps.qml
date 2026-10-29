pragma Singleton
import QtQuick
import Quickshell

Singleton {
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
    }
}
