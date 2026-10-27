pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Networking
import ".."

Singleton {
    id: root
    // Keyed by interface name: addresses, router, DNS, MAC and Wi-Fi band from network.py.
    property var details: ({})
    property var profile: null
    property string secret: ""
    property var qr: null
    property bool copied: false
    property string error: ""
    property string pendingDevice: ""
    // Seconds until network.py clears a copied password; reported by the helper.
    property int clearAfter: 0
    readonly property bool busy: operation.running || profileLoader.running
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/network.py"
    function icon(network) {
        if (network?.device?.type === DeviceType.Wired)
            return "ethernet";
        const strength = network?.signalStrength ?? 1;
        return strength < 0.34 ? "wifi-1" : strength < 0.67 ? "wifi-2" : "wifi";
    }
    function refreshDetails(device) {
        if (!device)
            return;
        if (detailsLoader.running) {
            pendingDevice = device;
            return;
        }
        detailsLoader.command = ["python3", helper, "details", device];
        detailsLoader.running = true;
    }
    // Callers match profile.uuid, so a stale profile is never shown and need not be cleared here.
    function loadProfile(uuid) {
        profileLoader.command = ["python3", helper, "profile", uuid];
        profileLoader.running = true;
    }
    function run(action, args) {
        if (operation.running)
            return;
        error = "";
        operation.action = action;
        operation.command = ["python3", helper, action].concat(args);
        operation.running = true;
    }
    function forgetSensitive() {
        secret = "";
        qr = null;
        copied = false;
        error = "";
    }
    Process {
        id: detailsLoader
        stdout: StdioCollector {
            id: detailsData
        }
        onExited: (code, status) => {
            if (code === 0) {
                try {
                    const data = JSON.parse(detailsData.text);
                    root.details = Object.assign({}, root.details, {
                        [data.device]: data
                    });
                } catch (e) {}
            }
            if (root.pendingDevice !== "") {
                const device = root.pendingDevice;
                root.pendingDevice = "";
                root.refreshDetails(device);
            }
        }
    }
    Process {
        id: profileLoader
        stdout: StdioCollector {
            id: profileData
        }
        stderr: StdioCollector {
            id: profileErrors
        }
        onExited: (code, status) => {
            try {
                root.profile = code === 0 ? JSON.parse(profileData.text) : null;
            } catch (e) {
                root.profile = null;
            }
            if (code !== 0)
                root.error = profileErrors.text.trim();
        }
    }
    Process {
        id: operation
        property string action: ""
        stdout: StdioCollector {
            id: result
        }
        stderr: StdioCollector {
            id: errors
        }
        onExited: (code, status) => {
            if (code !== 0) {
                root.error = errors.text.trim() || I18n.tr("network.errors.commandFailed", [code]);
                return;
            }
            try {
                const data = JSON.parse(result.text);
                if (operation.action === "secret")
                    root.secret = data.secret;
                else if (operation.action === "qr")
                    root.qr = data;
                else if (operation.action === "copy-secret") {
                    root.clearAfter = data.clearAfter;
                    root.copied = true;
                    copiedTimer.restart();
                } else
                    root.profile = data;
            } catch (e) {
                root.error = I18n.tr("network.errors.commandFailed", [result.text.trim()]);
            }
        }
    }
    Timer {
        id: copiedTimer
        interval: root.clearAfter * 1000
        onTriggered: root.copied = false
    }
}
