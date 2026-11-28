import QtQuick
import QtMultimedia

// A moving wallpaper (components/WallpaperVideo.qml): one video, muted, filling the screen as the still does
// (cropped, never letterboxed). The only file of the wallpaper that needs QtMultimedia: WallpaperVideo loads it, and
// without the module the still simply stays.
Item {
    id: root
    property string source: ""
    property bool looping: false
    property bool playing: false
    // Ended (an intro), or could not play: the still takes over.
    signal finished
    MediaPlayer {
        id: media
        source: root.source
        loops: root.looping ? MediaPlayer.Infinite : 1
        videoOutput: output
        // play() before the new source is set would be undone by it, so the player follows its own source.
        onSourceChanged: root.follow()
        onMediaStatusChanged: {
            if (mediaStatus === MediaPlayer.LoadedMedia)
                root.follow();
            else if (mediaStatus === MediaPlayer.EndOfMedia && !root.looping)
                root.finished();
        }
        onErrorOccurred: root.finished()
    }
    VideoOutput {
        id: output
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectCrop
    }
    function follow() {
        if (playing && source !== "")
            media.play();
        else
            media.pause();
    }
    onPlayingChanged: follow()
    Component.onCompleted: follow()
}
