import QtQuick
import QtMultimedia
import "../.."

// The picture of the Radio panel: one stream with sound and picture (Radio.videoStream, from radio.py handoff), played
// by Qt Multimedia from where mpv paused. The only file of the shell that needs QtMultimedia: RadioPanel loads it, and
// says so when the module is missing (the media profile installs it).
Item {
    id: root
    property string source: ""
    property real start: 0
    readonly property bool playing: player.playbackState === MediaPlayer.PlayingState
    readonly property bool loading: player.mediaStatus === MediaPlayer.LoadingMedia || player.mediaStatus === MediaPlayer.BufferingMedia || player.mediaStatus === MediaPlayer.StalledMedia
    readonly property real seconds: player.position / 1000
    property bool started: false
    signal ended
    signal failed(string message)
    function toggle() {
        if (playing)
            player.pause();
        else
            player.play();
    }
    Rectangle {
        anchors.fill: parent
        radius: Theme.corner(12)
        color: "black"
    }
    MediaPlayer {
        id: player
        source: root.source
        videoOutput: output
        audioOutput: AudioOutput {}
        onMediaStatusChanged: {
            // Seek once the stream is known, then play: where mpv was.
            if (!root.started && (mediaStatus === MediaPlayer.LoadedMedia || mediaStatus === MediaPlayer.BufferedMedia)) {
                root.started = true;
                if (root.start > 1 && seekable)
                    setPosition(root.start * 1000);
                play();
            }
            if (mediaStatus === MediaPlayer.EndOfMedia)
                root.ended();
        }
        onErrorOccurred: (error, message) => root.failed(message)
    }
    VideoOutput {
        id: output
        anchors.fill: parent
        anchors.margins: 1
        fillMode: VideoOutput.PreserveAspectFit
    }
}
