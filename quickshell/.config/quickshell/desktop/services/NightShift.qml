pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."
import "NightShiftSchedule.js" as NightShiftSchedule

// Night shift through hyprsunset, which warms the colours while it is running; when it exits the compositor drops
// its gamma ramp, so the colours return. Off, on, or automatic between Config.nightShiftStart and
// Config.nightShiftEnd; in automatic mode a tap turns it the other way until the next of those times. The
// mode and the temperature are saved like Keep awake.
Singleton {
    id: root
    readonly property string mode: ["off", "on", "auto"].includes(SessionState.nightShiftMode) ? SessionState.nightShiftMode : "off"
    readonly property int temperature: Math.max(minimum, Math.min(maximum, SessionState.nightShiftTemperature || Config.nightShiftTemperature))
    readonly property int minimum: 2500
    readonly property int maximum: 5500
    property bool available: false
    // A tap in automatic mode: the opposite of the schedule until this time (ms since epoch), saved so a
    // reload keeps it.
    readonly property real overrideUntil: SessionState.nightShiftOverrideUntil
    readonly property bool overrideValue: SessionState.nightShiftOverrideValue
    readonly property bool scheduled: inWindow(clock.date)
    readonly property bool overridden: mode === "auto" && overrideUntil > clock.date.getTime()
    readonly property bool active: available && (mode === "on" || mode === "auto" && (overridden ? overrideValue : scheduled))
    function inWindow(date) {
        return NightShiftSchedule.inWindow(date, Config.nightShiftStart, Config.nightShiftEnd);
    }
    function nextBoundary(date) {
        return NightShiftSchedule.nextBoundary(date, Config.nightShiftStart, Config.nightShiftEnd);
    }
    function setMode(value) {
        SessionState.set("nightShiftOverrideUntil", 0);
        SessionState.set("nightShiftMode", value);
    }
    function setTemperature(value) {
        SessionState.set("nightShiftTemperature", Math.round(value / 100) * 100);
    }
    // The tile: off and on swap; automatic keeps its schedule and turns the other way until the next mark.
    function toggle() {
        if (mode !== "auto") {
            setMode(mode === "on" ? "off" : "on");
            return;
        }
        SessionState.set("nightShiftOverrideValue", !active);
        SessionState.set("nightShiftOverrideUntil", nextBoundary(clock.date));
    }
    // IPC: "toggle", "on", "off" or "auto", with an OSD of the new state.
    function request(action) {
        if (!["toggle", "on", "off", "auto"].includes(action))
            return false;
        if (action === "toggle")
            toggle();
        else
            setMode(action);
        Osd.showState("night", I18n.tr("nightShift.title"), I18n.tr(active ? "common.on" : "common.off"));
        return true;
    }
    SystemClock {
        id: clock
        precision: SystemClock.Minutes
    }
    // Checked at start and each time the Control Center opens, so an install made later shows up.
    Process {
        id: probe
        running: true
        command: ["sh", "-c", "command -v hyprsunset"]
        onExited: code => root.available = code === 0
    }
    Connections {
        target: ShellState
        function onPanelChanged() {
            if (ShellState.panel === "controls" && !probe.running)
                probe.running = true;
        }
    }
    // Started and stopped with active, and restarted if it exits while still on.
    onActiveChanged: sunset.running = active
    Timer {
        interval: 3000
        repeat: true
        running: root.active && !sunset.running
        onTriggered: sunset.running = true
    }
    Process {
        id: sunset
        command: ["hyprsunset", "-t", String(root.temperature)]
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "" && root.active)
                    console.warn("hyprsunset:", text.trim());
            }
        }
    }
    // A new temperature goes to the running hyprsunset over its IPC; a restart would flash the colours.
    onTemperatureChanged: {
        if (sunset.running)
            Quickshell.execDetached(["hyprctl", "hyprsunset", "temperature", String(temperature)]);
    }
}
