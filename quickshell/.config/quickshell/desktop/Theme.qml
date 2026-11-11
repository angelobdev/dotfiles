pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "services"

Singleton {
    id: root
    // Reduce effects (Theming panel): Hyprland draws no blur, shadows or glass, so the surfaces that relied on
    // them become nearly opaque and keep their text readable; motion stops as with Config.reduceMotion.
    readonly property bool reduceEffects: colors.reduceEffects
    readonly property bool reduceMotion: Config.reduceMotion || reduceEffects
    function solid(value) {
        return reduceEffects && value.a < 0.94 ? Qt.rgba(value.r, value.g, value.b, 0.94) : value;
    }
    readonly property color background: solid(colors.background)
    readonly property color surface: solid(colors.surface)
    readonly property color raised: colors.raised
    readonly property color tile: colors.tile
    // Background of popup notifications; the same as raised unless the theme sets it.
    readonly property color notice: solid(colors.notice)
    readonly property color accentText: colors.accentText
    readonly property color track: colors.track
    readonly property color stroke: colors.stroke
    readonly property color text: colors.text
    readonly property color muted: colors.muted
    readonly property color accent: colors.accent
    readonly property color danger: colors.danger
    // What is on or chosen (a tab, the current device, a switch tile) and where the keyboard selection is in a
    // list: a tint of the accent and a neutral one, so neither reads as the accent-filled primary action.
    readonly property color active: Qt.alpha(accent, 0.22)
    readonly property color selection: Qt.alpha(text, 0.12)
    readonly property color scrim: colors.scrim
    readonly property color scrimModal: colors.scrimModal
    readonly property color scrimStrong: colors.scrimStrong
    readonly property color tooltip: solid(colors.tooltip)
    readonly property color handlePressed: colors.handlePressed
    readonly property color handleFocus: colors.handleFocus
    // Bar gradient and the share picker shade, formerly literals in Bar.qml and share.qml.
    readonly property color barShadeTop: colors.barShadeTop
    readonly property color barShadeBottom: colors.barShadeBottom
    readonly property color shareShade: colors.shareShade
    readonly property string font: colors.font
    // "desktop" draws the shell glyphs from assets/icons, "pack" from the icon theme where it has them.
    readonly property string iconSource: colors.iconSource
    // "shade" keeps the bar gradient, "transparent" drops it (bar colours then follow BarStyle).
    readonly property string barStyle: colors.barStyle
    // Corners follow the window rounding chosen in the Theming panel. Top-level surfaces (panels, dock,
    // OSD, popup notifications, menus) take exactly that radius, so they match the windows and the glass
    // behind them; radii inside them scale from the design size of 16 through corner().
    readonly property real cornerScale: Math.max(0, colors.rounding) / 16
    readonly property int radius: Math.max(0, Math.round(colors.rounding))
    // In tablet mode hit targets grow for fingers (Config.touchScale); in laptop mode every size is the
    // design one. Text sizes do not change with it.
    readonly property real touchScale: Tablet.active ? Config.touchScale : 1
    // Text size chosen in the Theming panel (1 to 1.5); every drawn text size goes through textSize().
    readonly property real textScale: Math.max(1, Math.min(1.5, colors.textScale))
    readonly property int barHeight: hit(38)
    // Shell surfaces take the window border chosen in the Theming panel: its width, the active colour for
    // what has the focus (panels, menus) and the inactive one for the rest (dock, OSD, notifications).
    // Without a border they keep the thin neutral stroke.
    readonly property int borderSize: Math.max(0, colors.borderSize)
    readonly property int frameWidth: borderSize > 0 ? borderSize : 1
    readonly property color frameActive: borderSize > 0 ? colors.activeBorder : stroke
    readonly property color frameInactive: borderSize > 0 ? colors.inactiveBorder : stroke
    readonly property int panelPadding: 16
    readonly property int dialogPadding: 22
    // Widths of centred dialogs, each the most a dialog takes (narrower screens get less): narrow for a prompt or
    // a short list (power menu, calendar, displays, authentication), medium for a search over a list (launcher,
    // clipboard, emoji, radio, share picker), wide for two columns (hints, wallpaper picker), and Settings with
    // its sidebar. Side panels take Config.controlCenterWidth (components/SidePanelCard.qml).
    readonly property int dialogNarrow: 480
    readonly property int dialogMedium: 620
    readonly property int dialogWide: 860
    readonly property int dialogSettings: 1240
    // The height a side panel or dialog leaves free: the bar above it and a margin below.
    readonly property int panelClearance: 76
    // Motion shared with Hyprland's "out" and "accel" curves in appearance.lua.
    readonly property int motionFast: reduceMotion ? 0 : 120
    readonly property int motionNormal: reduceMotion ? 0 : 220
    readonly property int motionSlow: reduceMotion ? 0 : 320
    readonly property var easeOut: [0.16, 1, 0.3, 1, 1, 1]
    readonly property var easeIn: [0.3, 0, 0.8, 0.15, 1, 1]
    function corner(size) {
        return Math.round(size * cornerScale);
    }
    function hit(size) {
        return Math.round(size * touchScale);
    }
    function textSize(size) {
        return Math.round(size * textScale);
    }
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
            property color notice: "#e6202226"
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
            property string iconSource: "desktop"
            property string barStyle: "shade"
            property real textScale: 1
            property bool reduceEffects: false
            property real rounding: 16
            property real borderSize: 0
            property color activeBorder: "#d4d6dc"
            property color inactiveBorder: "#44474e"
        }
    }
}
