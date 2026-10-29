pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root
    readonly property color background: colors.background
    readonly property color surface: colors.surface
    readonly property color raised: colors.raised
    readonly property color tile: colors.tile
    readonly property color accentText: colors.accentText
    readonly property color track: colors.track
    readonly property color stroke: colors.stroke
    readonly property color text: colors.text
    readonly property color muted: colors.muted
    readonly property color accent: colors.accent
    readonly property color danger: colors.danger
    readonly property color scrim: colors.scrim
    readonly property color scrimModal: colors.scrimModal
    readonly property color scrimStrong: colors.scrimStrong
    readonly property color tooltip: colors.tooltip
    readonly property color handlePressed: colors.handlePressed
    readonly property color handleFocus: colors.handleFocus
    // Bar gradient and the share picker shade, formerly literals in Bar.qml and share.qml.
    readonly property color barShadeTop: colors.barShadeTop
    readonly property color barShadeBottom: colors.barShadeBottom
    readonly property color shareShade: colors.shareShade
    readonly property string font: colors.font
    readonly property int radius: 18
    readonly property int panelPadding: 16
    readonly property int dialogPadding: 22
    // Motion shared with Hyprland's "out" and "accel" curves in appearance.lua.
    readonly property int motionFast: Config.reduceMotion ? 0 : 120
    readonly property int motionNormal: Config.reduceMotion ? 0 : 220
    readonly property int motionSlow: Config.reduceMotion ? 0 : 320
    readonly property var easeOut: [0.16, 1, 0.3, 1, 1, 1]
    readonly property var easeIn: [0.3, 0, 0.8, 0.15, 1, 1]
    // desktop-theme renders the current theme here; the defaults are Graphite, so a missing or broken file
    // changes nothing and edits apply live.
    FileView {
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-theme/quickshell.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        adapter: JsonAdapter {
            id: colors
            property color background: "#f2191a1d"
            property color surface: "#d9191a1d"
            property color raised: "#e6202226"
            property color tile: "#e6292b30"
            property color accentText: "#191a1d"
            property color track: "#805c6068"
            property color stroke: "#28ffffff"
            property color text: "#f0f0f2"
            property color muted: "#b8bbc1"
            property color accent: "#d4d6dc"
            property color danger: "#e99595"
            property color scrim: "#14000000"
            property color scrimModal: "#99000000"
            property color scrimStrong: "#bb000000"
            property color tooltip: "#f02b2d32"
            property color handlePressed: "#ffffff"
            property color handleFocus: "#888c94"
            property color barShadeTop: "#55000000"
            property color barShadeBottom: "#44000000"
            property color shareShade: "#28000000"
            property string font: "Adwaita Sans"
        }
    }
}
