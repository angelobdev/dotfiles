pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

Singleton {
    id: root
    property bool registered: false
    property var prompt: null
    property string error: ""
    property var pairing: []
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
        command: ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/bluetooth_agent.py"]
        running: true
        stdinEnabled: true
        stdout: SplitParser {
            onRead: line => {
                try {
                    const data = JSON.parse(line);
                    if (data.type === "status") {
                        root.registered = data.registered;
                        root.error = data.error || "";
                    } else if (data.type === "prompt")
                        root.prompt = data.prompt;
                    else if (data.type === "error") {
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
