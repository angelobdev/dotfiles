import QtQuick
import QtMultimedia
import "../.."

// The picture of the Radio panel: the video-only stream of what mpv plays (Radio.videoStream, from radio.py video),
// muted, since mpv keeps the sound. follow() keeps it in step with mpv: its pause, and its position when they drift
// apart. The only file of the shell that needs QtMultimedia: RadioPanel loads it, and says so when the module is
// missing (the radio profile installs it).
Item {
    id: root
    property string source: ""
    property real start: 0
    readonly property bool loading: player.mediaStatus === MediaPlayer.LoadingMedia || player.mediaStatus === MediaPlayer.BufferingMedia || player.mediaStatus === MediaPlayer.StalledMedia
    property bool started: false
    // How far apart the picture and the sound may get before the picture jumps, and what status lags behind mpv.
    readonly property real tolerance: 0.6
    readonly property real lag: 0.15
    signal failed(string message)
    function follow(seconds, paused) {
        if (!started)
            return;
        if (paused && player.playbackState === MediaPlayer.PlayingState)
            player.pause();
        else if (!paused && player.playbackState !== MediaPlayer.PlayingState)
            player.play();
        if (player.seekable && Math.abs(player.position / 1000 - seconds) > tolerance)
            player.setPosition((seconds + (paused ? 0 : lag)) * 1000);
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
        onMediaStatusChanged: {
            // Where mpv was, once the stream is known; from then on follow() keeps it there.
            if (!root.started && (mediaStatus === MediaPlayer.LoadedMedia || mediaStatus === MediaPlayer.BufferedMedia)) {
                root.started = true;
                if (root.start > 1 && seekable)
                    setPosition(root.start * 1000);
                play();
            }
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
