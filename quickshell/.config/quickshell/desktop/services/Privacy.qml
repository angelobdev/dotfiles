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
    // Screen sharing: the screencast event says on or off but not which share, so a share that ends while another
    // runs turned the indicator off, and after a reload during a share it stayed off. XDPH also makes a PipeWire
    // stream for every share, which is there from the start and counts each one.
    property bool screencast: false
    readonly property var shareStreams: Pipewire.nodes.values.filter(n => (n.name ?? "").startsWith("xdph-streaming-"))
    readonly property bool sharing: screencast || shareStreams.length > 0
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
        // screencast>>STATE,OWNER: 1 when a share starts, 0 when it stops. A screencopy client such as
        // wf-recorder sends both for every frame it copies, so "off" waits for screencastEnd: the icon stays
        // on through a recording instead of flickering with each frame.
        function onRawEvent(event) {
            if (event.name !== "screencast")
                return;
            if (event.data.split(",")[0] === "1") {
                screencastEnd.stop();
                root.screencast = true;
            } else {
                screencastEnd.restart();
            }
        }
    }
    Timer {
        id: screencastEnd
        interval: 1500
        onTriggered: root.screencast = false
    }
    // privacy.py watch prints the holders whenever a camera opens or closes (inotify), nothing in between.
    Process {
        id: cameras
        // What a watcher that keeps failing says reaches qs log instead of nowhere.
        stderr: SplitParser {
            onRead: line => console.warn("privacy.py:", line)
        }
        // Ends with the shell, even a killed one (setpriv: the kernel signals it).
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/privacy.py", "watch"])
        running: true
        stdinEnabled: true
        stdout: SplitParser {
            onRead: data => {
                try {
                    const names = JSON.parse(data);
                    if (Array.isArray(names))
                        root.cameraHolders = names;
                } catch (error) {}
            }
        }
        onStarted: backoff.started()
        onExited: {
            backoff.ended();
            retry.restart();
        }
    }
    Backoff {
        id: backoff
        base: 5000
    }
    Timer {
        id: retry
        interval: backoff.interval
        onTriggered: cameras.running = true
    }
}
