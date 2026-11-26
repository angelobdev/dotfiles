import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import "../.."
import ".."

// The keyboard layout in use, as its short code; a click switches to the next one.
BarButton {
    id: root
    property var bar
    property bool shown: true
    property var layouts: []
    property int active: 0
    text: (layouts[active] ?? "").toUpperCase()
    tooltip: I18n.tr("bar.widgets.keyboardLayout.tooltip")
    onClicked: Quickshell.execDetached(["hyprctl", "switchxkblayout", "main", "next"])
    Component.onCompleted: reader.running = true
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "activelayout" && !reader.running)
                reader.running = true;
        }
    }
    Process {
        id: reader
        command: ["hyprctl", "devices", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const main = JSON.parse(text).keyboards.find(keyboard => keyboard.main);
                    if (main) {
                        root.layouts = main.layout.split(",");
                        root.active = main.active_layout_index;
                    }
                } catch (failure) {}
            }
        }
    }
}
