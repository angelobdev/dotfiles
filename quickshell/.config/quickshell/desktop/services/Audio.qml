pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.Pipewire
Singleton {
    readonly property var sink: Pipewire.defaultAudioSink
    readonly property var source: Pipewire.defaultAudioSource
    readonly property int volume: sink?.audio ? Math.round(sink.audio.volume * 100) : 0
    readonly property bool muted: sink?.audio?.muted ?? true
    PwObjectTracker { objects: [Pipewire.defaultAudioSink, Pipewire.defaultAudioSource].filter(n => n !== null) }
    function setVolume(value) { if (sink?.audio) sink.audio.volume = Math.max(0, Math.min(1, value)); }
    function toggleMute() { if (sink?.audio) sink.audio.muted = !sink.audio.muted; }
    function toggleMic() { if (source?.audio) source.audio.muted = !source.audio.muted; }
}
