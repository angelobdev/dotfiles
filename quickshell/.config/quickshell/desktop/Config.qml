pragma Singleton
import QtQuick

QtObject {
    readonly property int minimumWorkspaces: 2
    readonly property bool workspaceScroll: true
    readonly property bool clipboardEnabled: true
    readonly property int clipboardMaxItems: 200
    readonly property int recordingFramerate: 30
    readonly property string recordingCodec: "libvpx-vp9"
    // Order and presence of modules. Unknown names are ignored.
    readonly property var controlCenterModules: ["network", "bluetooth", "brightness", "audio", "media", "doNotDisturb", "idle"]
    readonly property int controlCenterWidth: 400
    readonly property bool expandMonitors: false
    readonly property bool expandAudioDevices: false
    // If disconnected, use the first connected screen.
    readonly property string primaryMonitor: "eDP-1"
    // OSD: logical pixels and timeout in milliseconds.
    readonly property bool osdEnabled: true
    readonly property int osdTimeout: 1700
    readonly property int osdWidth: 320
    readonly property int osdBottomMargin: 96
    // Empty list includes all enabled GNOME/Online Accounts calendars; otherwise use EDS source UIDs.
    readonly property var calendarSources: []
    // Internal panels are detected automatically when there is one backlight.
    // External example: ({ "DP-1": { "type": "ddc", "bus": 6 } })
    // Explicit backlight: { "type": "backlight", "device": "intel_backlight" }
    readonly property var brightnessDevices: ({})
}
