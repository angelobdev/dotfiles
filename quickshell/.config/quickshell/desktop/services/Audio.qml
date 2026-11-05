pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.Pipewire

Singleton {
    id: root
    readonly property var sink: Pipewire.defaultAudioSink
    readonly property var source: Pipewire.defaultAudioSource
    readonly property var devices: Pipewire.nodes.values.filter(n => n.audio && !n.isStream)
    readonly property var outputs: devices.filter(n => n.isSink).sort((a, b) => a.description.localeCompare(b.description))
    readonly property var inputs: devices.filter(n => !n.isSink).sort((a, b) => a.description.localeCompare(b.description))
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
}
