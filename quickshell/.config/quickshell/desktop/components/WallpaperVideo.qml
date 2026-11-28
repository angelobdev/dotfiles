import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Wayland
import ".."
import "../services"

// The moving wallpaper of one screen, after Omarchy: a still of a theme may have a loop (loops/<stem>.mp4 beside it),
// which plays in its place, and an intro (intros/<stem>.mp4), which plays once before it. A layer over the still
// (hyprpaper), under every window, that takes no input; shown only while a video plays.
// - The loop plays while the animations are on (Theme.reduceMotion), on AC power, and Config.wallpaperLoops; it
//   pauses while a fullscreen window covers the screen. Otherwise the still shows.
// - The intro plays when the wallpaper changes (a theme switch, a wallpaper chosen) and once at the first start of the
//   shell after a login, with Config.wallpaperIntros and the animations on.
PanelWindow {
    id: root
    WlrLayershell.layer: WlrLayer.Background
    WlrLayershell.namespace: "desktop-wallpaper-video"
    exclusionMode: ExclusionMode.Ignore
    anchors {
        top: true
        bottom: true
        left: true
        right: true
    }
    color: "transparent"
    // Clicks go to the desktop below (the desktop menu), never to the video.
    mask: Region {}
    readonly property string still: DynamicTheme.wallpaper
    readonly property string loopFile: video(still, "loops")
    readonly property string introFile: video(still, "intros")
    // A video beside a still: <folder>/<kind>/<stem>.mp4. A function of the path, so a handler of still reads it new.
    function video(path, kind) {
        const slash = path.lastIndexOf("/");
        return path.substring(0, slash) + "/" + kind + "/" + path.substring(slash + 1).replace(/\.[^.]*$/, "") + ".mp4";
    }
    property bool hasLoop: false
    property bool hasIntro: false
    property bool introPlaying: false
    readonly property bool animated: !Theme.reduceMotion
    readonly property bool covered: Hyprland.monitorFor(screen)?.activeWorkspace?.hasFullscreen ?? false
    readonly property bool loopAllowed: Config.wallpaperLoops && animated && !Battery.discharging && hasLoop
    readonly property string playing: introPlaying ? introFile : loopAllowed ? loopFile : ""
    visible: playing !== "" && player.status === Loader.Ready
    // A new wallpaper: what it has beside it, then its intro. The first one seen is the one the session starts with
    // (it arrives from DynamicTheme after the window is made): its intro is the one of the login.
    property bool started: false
    onStillChanged: check(started)
    Component.onCompleted: if (still !== "")
        check(false)
    function check(changed) {
        introPlaying = false;
        if (still === "") {
            hasLoop = false;
            hasIntro = false;
            return;
        }
        started = true;
        finder.changed = changed;
        finder.command = ["sh", "-c", "[ -f \"$1\" ] && echo loop; [ -f \"$2\" ] && echo intro; true", "sh", video(still, "loops"), video(still, "intros")];
        finder.running = true;
    }
    function intro() {
        if (hasIntro && Config.wallpaperIntros && animated)
            introPlaying = true;
    }
    Process {
        id: finder
        property bool changed: false
        stdout: StdioCollector {
            onStreamFinished: {
                root.hasLoop = text.includes("loop");
                root.hasIntro = text.includes("intro");
                if (finder.changed)
                    root.intro();
                else
                    login.running = true;
            }
        }
    }
    // Once per login: the first start of the shell after it plays the intro, a restart does not.
    Process {
        id: login
        command: ["sh", "-c", "m=\"${XDG_RUNTIME_DIR:-/tmp}/desktop-shell/wallpaper-intro\"; [ -e \"$m\" ] && exit 1; mkdir -p \"${m%/*}\" && touch \"$m\""]
        onExited: (code, status) => {
            if (code === 0)
                root.intro();
        }
    }
    Loader {
        id: player
        anchors.fill: parent
        source: Qt.resolvedUrl("WallpaperPlayer.qml")
        opacity: root.playing !== "" ? 1 : 0
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.motionNormal
            }
        }
        onLoaded: item.finished.connect(() => root.introPlaying = false)
        Binding {
            target: player.item
            property: "source"
            value: root.playing === "" ? "" : "file://" + root.playing
            when: player.status === Loader.Ready
        }
        Binding {
            target: player.item
            property: "looping"
            value: !root.introPlaying
            when: player.status === Loader.Ready
        }
        Binding {
            target: player.item
            property: "playing"
            value: root.playing !== "" && !root.covered
            when: player.status === Loader.Ready
        }
    }
}
