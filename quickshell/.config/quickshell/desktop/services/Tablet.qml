pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// The 2-in-1 posture and the rotation that follows it. Hyprland reports the tablet mode switch through
// desktop-shell; the accelerometer is read only in tablet mode, and leaving it puts the internal display
// upright again. Rotation lock keeps the current orientation and is saved like Keep awake.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/rotation.py"
    readonly property string runtimeDir: (Quickshell.env("XDG_RUNTIME_DIR") || "/tmp") + "/desktop-shell"
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session"
    // Only the desktop shell (shell.qml) enables it; another Quickshell config that loads Theme, like the
    // share picker, just reads the posture and runs no sensor or rotation.
    property bool enabled: false
    onEnabledChanged: rotate()
    readonly property bool active: posture.tablet === true
    readonly property bool locked: SessionState.rotationLock
    // Whether there is an accelerometer at all; the Control Center tile shows only then.
    property bool available: false
    property string orientation: ""
    // Last transform the sensor reported, and the one Hyprland has; both start from the saved rotation.
    property int sensed: 0
    property int transform: 0
    property bool postureLoaded: false
    property bool rotationLoaded: false
    readonly property bool ready: postureLoaded && rotationLoaded
    onReadyChanged: rotate()
    readonly property int wanted: !active ? 0 : locked ? transform : sensed
    // A new tablet session starts upright until the sensor reports, not in the last orientation of the
    // previous one (which flipped twice on entry).
    onActiveChanged: if (!active)
        sensed = 0
    onWantedChanged: rotate()
    function rotate() {
        if (!enabled || !ready || wanted === transform)
            return;
        transform = wanted;
        if (!applier.running) {
            applier.command = ["python3", helper, "apply", String(transform)];
            applier.running = true;
        }
    }
    function setActive(value) {
        if (!enabled || posture.tablet === value)
            return;
        posture.tablet = value;
        postureFile.writeAdapter();
    }
    function setLocked(value) {
        SessionState.set("rotationLock", value);
    }
    // IPC: the switch binds send "on" and "off"; "toggle" is there to try it without flipping the screen.
    function request(action) {
        if (!["toggle", "on", "off"].includes(action))
            return false;
        setActive(action === "toggle" ? !active : action === "on");
        return true;
    }
    function requestLock(action) {
        if (!["toggle", "on", "off"].includes(action))
            return false;
        setLocked(action === "toggle" ? !locked : action === "on");
        Osd.showState(locked ? "rotate-lock" : "rotate", I18n.tr("tablet.rotationLock"), I18n.tr(locked ? "common.on" : "common.off"));
        return true;
    }
    Process {
        id: applier
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "")
                    console.warn("rotation:", text.trim());
            }
        }
        // A change during a run is applied after it.
        onExited: {
            if (command[3] !== String(root.transform)) {
                command = ["python3", root.helper, "apply", String(root.transform)];
                running = true;
            }
        }
    }
    Process {
        running: root.enabled
        command: ["python3", root.helper, "probe"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.available = JSON.parse(text).available === true;
                } catch (failure) {
                    root.available = false;
                }
            }
        }
    }
    // Claims the accelerometer only while its reading can rotate the display; restarted if it exits while
    // still needed (a binding on running would not run it again once the process has set it false).
    readonly property bool watching: enabled && ready && active && !locked && available
    onWatchingChanged: watcher.running = watching
    Timer {
        interval: 3000
        repeat: true
        running: root.watching && !watcher.running
        onTriggered: watcher.running = true
    }
    Process {
        id: watcher
        command: ["python3", root.helper, "watch"]
        stdout: SplitParser {
            onRead: data => {
                try {
                    const reading = JSON.parse(data);
                    root.orientation = reading.orientation ?? "";
                    // Lying flat reports no transform: the display keeps its rotation.
                    if (typeof reading.transform === "number")
                        root.sensed = reading.transform;
                } catch (failure) {}
            }
        }
    }
    // The posture outlives shell restarts but not the session: a flip while the shell was away is missed,
    // a reboot starts in laptop mode until the switch reports again.
    FileView {
        id: postureFile
        path: root.runtimeDir + "/tablet.json"
        // Read at once: a write before the first read would save the defaults over the saved values.
        blockLoading: true
        atomicWrites: true
        printErrors: false
        adapter: JsonAdapter {
            id: posture
            property bool tablet: false
        }
        onLoaded: root.postureLoaded = true
        onLoadFailed: root.postureLoaded = true
    }
    // The rotation Hyprland applied at startup (config/tablet.lua reads the same file).
    FileView {
        path: root.stateDir + "/rotation.lua"
        printErrors: false
        onLoaded: {
            const match = /transform\s*=\s*([0-3])/.exec(text());
            root.transform = match ? Number(match[1]) : 0;
            root.sensed = root.transform;
            root.rotationLoaded = true;
        }
        onLoadFailed: root.rotationLoaded = true
    }
}
