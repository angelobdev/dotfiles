pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import ".."

Singleton {
    id: root
    property bool registered: false
    property var prompt: null
    // The focused monitor when the prompt came, set first so the prompt window opens there.
    property var promptScreen: null
    property string error: ""
    property var pairing: []
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/bluetooth_agent.py"
    function send(data) {
        if (process.running)
            process.write(JSON.stringify(data) + "\n");
    }
    function pair(device) {
        error = "";
        pairing = pairing.filter(p => p !== device.dbusPath).concat(device.dbusPath);
        send({
            action: "pair",
            device: device.dbusPath
        });
    }
    function cancel(device) {
        send({
            action: "cancel",
            device: device
        });
    }
    function reply(accepted, value) {
        if (!prompt)
            return;
        const current = prompt;
        send({
            action: "reply",
            id: current.id,
            accepted: accepted,
            value: value || ""
        });
        if (!accepted && ["DisplayPasskey", "DisplayPinCode"].includes(current.kind))
            cancel(current.device);
        prompt = null;
    }
    Process {
        id: process
        // Ends with the shell, even a killed one (setpriv: the kernel signals it).
        command: ["setpriv", "--pdeathsig", "TERM", "--"].concat(["python3", root.helper])
        running: true
        stdinEnabled: true
        stdout: SplitParser {
            onRead: line => {
                try {
                    const data = JSON.parse(line);
                    if (data.type === "status") {
                        root.registered = data.registered;
                        root.error = data.error || "";
                    } else if (data.type === "prompt") {
                        root.promptScreen = ShellState.screenNamed(Hyprland.focusedMonitor?.name);
                        root.prompt = data.prompt;
                    } else if (data.type === "error") {
                        root.error = data.error;
                        root.pairing = [];
                    } else if (data.type === "operation") {
                        root.pairing = root.pairing.filter(p => p !== data.device);
                        root.error = data.ok ? "" : data.error;
                    }
                } catch (e) {
                    root.error = I18n.tr("bluetooth.errors.invalidAgentResponse");
                }
            }
        }
        onExited: {
            root.registered = false;
            root.prompt = null;
            root.pairing = [];
            root.error = I18n.tr("bluetooth.errors.agentUnavailable");
        }
    }
    Timer {
        interval: 3000
        repeat: true
        running: !process.running
        onTriggered: process.running = true
    }
}
