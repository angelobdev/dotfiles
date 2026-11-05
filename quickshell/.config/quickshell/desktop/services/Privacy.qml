pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Services.Pipewire
import ".."

// What is listening or watching right now, for the privacy indicator of the bar: apps recording audio
// (PipeWire capture streams), processes with a camera open (privacy.py; PipeWire itself stands for the apps
// reading the camera through it, named from its video streams), and screen sharing (screencast events).
Singleton {
    id: root
    readonly property var recorders: Pipewire.nodes.values.filter(n => n.audio && n.isStream && !n.isSink)
    readonly property var videoStreams: Pipewire.nodes.values.filter(n => !n.audio && n.isStream)
    property var cameraHolders: []
    property bool sharing: false
    readonly property var microphoneApps: unique(recorders.map(n => appName(n)))
    readonly property var cameraApps: unique(Array.from(cameraHolders).reduce((names, name) => names.concat(name === "pipewire" || name === "wireplumber" ? videoStreams.map(n => appName(n)) : [name]), []))
    readonly property bool microphone: recorders.length > 0
    readonly property bool camera: cameraHolders.length > 0
    readonly property bool active: microphone || camera || sharing

    function appName(node) {
        const properties = node?.properties ?? {};
        return properties["application.name"] || node?.description || node?.name || "";
    }
    function unique(names) {
        return names.filter((name, index) => name !== "" && names.indexOf(name) === index);
    }
    PwObjectTracker {
        objects: root.recorders.concat(root.videoStreams)
    }
    Connections {
        target: Hyprland
        // screencast>>STATE,OWNER: 1 when a share starts, 0 when it stops.
        function onRawEvent(event) {
            if (event.name === "screencast")
                root.sharing = event.data.split(",")[0] === "1";
        }
    }
    Timer {
        interval: 3000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: if (!cameras.running)
            cameras.running = true
    }
    Process {
        id: cameras
        command: ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/privacy.py", "cameras"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const names = JSON.parse(text);
                    if (Array.isArray(names) && JSON.stringify(names) !== JSON.stringify(root.cameraHolders))
                        root.cameraHolders = names;
                } catch (error) {}
            }
        }
    }
}
