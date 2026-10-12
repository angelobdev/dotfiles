pragma Singleton
import QtQuick
QtObject {
    // Order and presence of modules. Unknown names are ignored.
    readonly property var controlCenterModules: ["network", "bluetooth", "brightness", "audio", "doNotDisturb"]
    readonly property int controlCenterWidth: 400
    readonly property bool expandMonitors: false
    readonly property bool expandAudioDevices: false
    // If disconnected, use the first connected screen.
    readonly property string primaryMonitor: "eDP-1"
    // Internal panels are detected automatically when there is one backlight.
    // External example: ({ "DP-1": { "type": "ddc", "bus": 6 } })
    // Explicit backlight: { "type": "backlight", "device": "intel_backlight" }
    readonly property var brightnessDevices: ({})
}
