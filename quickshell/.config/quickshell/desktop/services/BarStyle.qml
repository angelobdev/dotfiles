pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// Bar colours. Shaded, they are the theme ones. On a transparent bar theme.py measures the wallpaper strip
// under the bar, and text and icons take whichever of the theme text colours contrasts more with it.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/theme.py"
    readonly property bool transparent: Theme.barStyle === "transparent"
    property bool lightBackdrop: false
    readonly property bool darkText: transparent && lightBackdrop
    readonly property color foreground: darkText ? Theme.accentText : Theme.text
    readonly property color muted: darkText ? Qt.alpha(Theme.accentText, 0.72) : Theme.muted
    readonly property color accent: darkText ? Theme.accentText : Theme.accent
    function measure() {
        if (transparent && !tone.running)
            tone.running = true;
    }
    function toggle() {
        Quickshell.execDetached(["python3", helper, "bar-style", "toggle"]);
    }
    onTransparentChanged: measure()
    Component.onCompleted: measure()
    Process {
        id: tone
        command: ["python3", root.helper, "tone"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.lightBackdrop = JSON.parse(text).text === "dark";
                } catch (failure) {
                    root.lightBackdrop = false;
                }
            }
        }
    }
    // wallpaper.py rewrites this after every change, so the tone is measured again.
    FileView {
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session/wallpaper/selection.json"
        watchChanges: true
        printErrors: false
        onFileChanged: {
            reload();
            root.measure();
        }
    }
}
