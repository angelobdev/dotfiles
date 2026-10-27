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
    // DNS choices in the network details view; each preset lists IPv4 and IPv6 servers.
    readonly property var dnsPresets: [
        {
            name: "Cloudflare",
            servers: ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"]
        },
        {
            name: "Quad9",
            servers: ["9.9.9.9", "149.112.112.112", "2620:fe::fe", "2620:fe::9"]
        },
        {
            name: "Google",
            servers: ["8.8.8.8", "8.8.4.4", "2001:4860:4860::8888", "2001:4860:4860::8844"]
        },
        {
            name: "AdGuard",
            servers: ["94.140.14.14", "94.140.15.15", "2a10:50c0::ad1:ff", "2a10:50c0::ad2:ff"]
        }
    ]
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
