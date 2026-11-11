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
    // The other text colour, as a soft halo behind text and icons on a transparent bar: the choice above fits
    // the strip on average, and the halo keeps them readable where one side differs (a bright sky on the left).
    readonly property color halo: darkText ? Theme.text : Theme.accentText
    // A wallpaper change during a measurement is measured again after it (two quick Next wallpaper).
    function measure() {
        if (transparent)
            tone.request();
    }
    function toggle() {
        Quickshell.execDetached(["python3", helper, "bar-style", "toggle"]);
    }
    onTransparentChanged: measure()
    Component.onCompleted: measure()
    CoalescedProcess {
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
    // A new wallpaper is measured again (DynamicTheme watches selection.json for the whole shell).
    Connections {
        target: DynamicTheme
        function onWallpaperChanged() {
            root.measure();
        }
    }
    // So is a new theme: the choice is between its own two text colours, and Generate keeps the wallpaper.
    Connections {
        target: Theme
        function onTextChanged() {
            root.measure();
        }
        function onAccentTextChanged() {
            root.measure();
        }
    }
}
