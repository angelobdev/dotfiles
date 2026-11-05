import QtQuick
import Quickshell.Io

// A Process asked for again while it runs runs once more when it ends, with its command by then: setting
// running on a running Process does nothing, so the last of several quick requests would be lost.
Process {
    id: root
    property bool again: false
    function request() {
        if (running)
            again = true;
        else
            running = true;
    }
    onExited: {
        if (again) {
            again = false;
            running = true;
        }
    }
}
