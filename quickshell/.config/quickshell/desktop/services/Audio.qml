pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Pipewire
import ".."
import "DeviceNames.js" as DeviceNames

Singleton {
    id: root
    readonly property var sink: Pipewire.defaultAudioSink
    readonly property var source: Pipewire.defaultAudioSource
    readonly property var devices: Pipewire.nodes.values.filter(n => n.audio && !n.isStream)
    // The active port of each device by node name (DeviceNames.audioPorts): what PipeWire does not give the shell,
    // such as whether a monitor is plugged into an HDMI output and its name. Read at startup, when the device list
    // changes and when a panel showing devices opens, and while one is open on every change of a card (hotplug).
    property var ports: ({})
    readonly property bool looking: ShellState.panel === "audio" || ShellState.panel === "controls" || ShellState.panel === "settings"
    readonly property string deviceKey: devices.map(n => n.name).join("\n")
    // Each device by id: its name, told apart from another one that reads the same.
    readonly property var names: DeviceNames.distinct(devices.map(n => ({
                key: n.id,
                label: DeviceNames.audioName(n, ports[n.name], root.tr),
                detail: DeviceNames.isHdmi(n, ports[n.name]) ? DeviceNames.hdmiName(n, ports[n.name], root.tr) : n.description
            })))
    // HDMI and DisplayPort outputs with nothing plugged in stay listed, after the others and dimmed: a port that
    // misreports must not hide a working output.
    readonly property var outputs: devices.filter(n => n.isSink).sort((a, b) => Number(absent(a)) - Number(absent(b)) || deviceName(a).localeCompare(deviceName(b)))
    readonly property var inputs: devices.filter(n => !n.isSink).sort((a, b) => deviceName(a).localeCompare(deviceName(b)))
    readonly property int volume: sink?.audio ? Math.round(sink.audio.volume * 100) : 0
    readonly property int inputVolume: source?.audio ? Math.round(source.audio.volume * 100) : 0
    readonly property bool muted: sink?.audio?.muted ?? true
    readonly property bool inputMuted: source?.audio?.muted ?? true
    // Apps playing sound, one slider each in the Audio panel. A playback stream is a sink stream to PipeWire
    // (isSink); streams that record are left out.
    readonly property var streams: Pipewire.nodes.values.filter(n => n.audio && n.isStream && n.isSink)
    PwObjectTracker {
        objects: root.devices.concat(root.streams)
    }
    function tr(key, args) {
        return I18n.tr(key, args);
    }
    function deviceName(node) {
        return names[node?.id] ?? DeviceNames.audioName(node, ports[node?.name ?? ""], tr);
    }
    // The tooltip: whether nothing is plugged in, then the description and the node name PipeWire gives.
    function deviceDetails(node) {
        const lines = absent(node) ? [I18n.tr("audio.notConnected")] : [];
        for (const text of [node?.description ?? "", node?.name ?? ""])
            if (text !== "" && !lines.includes(text))
                lines.push(text);
        return lines.join("\n");
    }
    function absent(node) {
        return DeviceNames.absent(node, ports[node?.name ?? ""]);
    }
    function readPorts() {
        portReader.request();
    }
    function streamName(node) {
        const properties = node?.properties ?? {};
        return properties["application.name"] || node?.description || node?.name || "";
    }
    function streamIcon(node) {
        const properties = node?.properties ?? {};
        return properties["application.icon-name"] || properties["application.process.binary"] || "";
    }
    function setStreamVolume(node, value) {
        if (node?.audio)
            node.audio.volume = Math.max(0, Math.min(1, value));
    }
    function toggleStreamMute(node) {
        if (node?.audio)
            node.audio.muted = !node.audio.muted;
    }
    function selectOutput(node) {
        if (outputs.includes(node))
            Pipewire.preferredDefaultAudioSink = node;
    }
    function selectInput(node) {
        if (inputs.includes(node))
            Pipewire.preferredDefaultAudioSource = node;
    }
    function setVolume(value) {
        if (sink?.audio)
            sink.audio.volume = Math.max(0, Math.min(1, value));
    }
    function setInputVolume(value) {
        if (source?.audio)
            source.audio.volume = Math.max(0, Math.min(1, value));
    }
    function toggleMute() {
        if (sink?.audio)
            sink.audio.muted = !sink.audio.muted;
    }
    function toggleMic() {
        if (source?.audio)
            source.audio.muted = !source.audio.muted;
    }
    onLookingChanged: if (looking)
        readPorts()
    onDeviceKeyChanged: Qt.callLater(readPorts)
    Component.onCompleted: readPorts()
    // The C locale keeps the availability words English.
    CoalescedProcess {
        id: portReader
        command: ["env", "LC_ALL=C.UTF-8", "LANGUAGE=", "pactl", "-f", "json", "list"]
        stdout: StdioCollector {
            id: portData
        }
        onExited: (code, status) => {
            if (code !== 0)
                return;
            try {
                root.ports = DeviceNames.audioPorts(JSON.parse(portData.text));
            } catch (error) {
                console.warn("Audio: unreadable pactl listing:", error);
            }
        }
    }
    // Card events: a monitor plugged into or out of an HDMI port changes its card. Only while devices are on screen.
    Process {
        command: ["setpriv", "--pdeathsig", "TERM", "--", "pactl", "subscribe"]
        running: root.looking
        stdout: SplitParser {
            onRead: line => {
                if (/ on card #/.test(line))
                    root.readPorts();
            }
        }
    }
}
