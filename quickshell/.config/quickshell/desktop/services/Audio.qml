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
    PwObjectTracker {
        objects: root.devices
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
