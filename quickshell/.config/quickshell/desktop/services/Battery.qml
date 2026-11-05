pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.UPower
import ".."

// Warns once per discharge when the battery runs low, and again when it is critical. Plugging the charger in
// resets both; a level that wobbles around a threshold warns only once. With autoSaver (the battery panel, on
// by default) the low level also turns Power Saver on, once per discharge; the charger brings back the profile
// it replaced, unless another one was chosen meanwhile. A change of power source tells config/tablet.lua,
// which keeps a display refresh for each.
Singleton {
    id: root
    readonly property var device: UPower.displayDevice
    readonly property bool present: device?.isLaptopBattery ?? false
    readonly property int percent: Math.round((device?.percentage ?? 0) * 100)
    readonly property bool discharging: present && UPower.onBattery
    // 0 fine, 1 low, 2 critical.
    readonly property int level: !discharging ? 0 : percent <= Config.batteryCritical ? 2 : percent <= Config.batteryLow ? 1 : 0
    property int announced: 0
    readonly property bool autoSaver: settings.autoSaver
    function setAutoSaver(on) {
        settings.autoSaver = on;
        settingsFile.writeAdapter();
        if (on && discharging && level > 0)
            enableSaver();
    }
    // Power Saver on behalf of the user, remembering the profile it replaces.
    function enableSaver() {
        // Already switched in this discharge (before a shell restart): a profile chosen since then stays.
        if (PowerProfiles.profile === PowerProfile.PowerSaver || settings.restoreProfile >= 0)
            return false;
        settings.restoreProfile = PowerProfiles.profile;
        settingsFile.writeAdapter();
        PowerProfiles.profile = PowerProfile.PowerSaver;
        return true;
    }
    function restoreProfile() {
        if (settings.restoreProfile < 0)
            return;
        if (PowerProfiles.profile === PowerProfile.PowerSaver)
            PowerProfiles.profile = settings.restoreProfile;
        settings.restoreProfile = -1;
        settingsFile.writeAdapter();
    }
    // Devices with their own battery (the stylus, a mouse, a headset), while they report one.
    readonly property var peripherals: UPower.devices.values.filter(d => d.ready && d.isPresent && !d.powerSupply)
    // Native paths of peripherals already warned about, until they charge again.
    property var lowPeripherals: []

    function isStylus(device) {
        const path = device?.nativePath ?? "";
        return device?.type === UPowerDeviceType.Pen || Config.stylusBatteries.some(prefix => path.startsWith(prefix));
    }
    function peripheralName(device) {
        return isStylus(device) ? I18n.tr("battery.stylus") : (device?.model || I18n.tr("battery.device"));
    }
    function checkPeripherals() {
        // A stylus comes and goes with the pen near the screen: one away keeps its warning.
        const kept = lowPeripherals.filter(path => !peripherals.some(d => d.nativePath === path));
        for (const device of peripherals) {
            const percent = Math.round(device.percentage * 100);
            const path = device.nativePath;
            if (percent > Config.peripheralLow + 10 || !lowPeripherals.includes(path) && percent > Config.peripheralLow)
                continue;
            kept.push(path);
            if (lowPeripherals.includes(path) || percent <= 0)
                continue;
            Quickshell.execDetached(["notify-send", "--app-name=" + I18n.tr("battery.title"), "--app-icon=battery-low", I18n.tr("battery.alert.peripheralTitle", [peripheralName(device), percent]), I18n.tr("battery.alert.peripheralBody")]);
        }
        lowPeripherals = kept;
    }

    function duration(seconds) {
        if (!Number.isFinite(seconds) || seconds <= 0)
            return "";
        const minutes = Math.max(1, Math.round(seconds / 60));
        return minutes >= 60 ? I18n.tr("battery.durationHours", [Math.floor(minutes / 60), minutes % 60]) : I18n.tr("battery.durationMinutes", [minutes]);
    }
    function check() {
        if (!discharging) {
            announced = 0;
            // Only on the charger: a battery not yet read is not a charger.
            if (present && !UPower.onBattery)
                restoreProfile();
            return;
        }
        if (level <= announced)
            return;
        // Once per discharge: a profile chosen after the switch stays.
        const switched = announced === 0 && autoSaver && enableSaver();
        announced = level;
        const left = duration(device?.timeToEmpty ?? 0);
        const critical = level === 2;
        const body = left ? I18n.tr(critical ? "battery.alert.criticalBodyTime" : "battery.alert.lowBodyTime", [left]) : I18n.tr(critical ? "battery.alert.criticalBody" : "battery.alert.lowBody");
        notifier.command = ["notify-send", "--wait", "--app-name=" + I18n.tr("battery.title"), "--app-icon=" + (critical ? "battery-caution" : "battery-low"), "--urgency=" + (critical ? "critical" : "normal")].concat(!critical && !switched && PowerProfiles.profile !== PowerProfile.PowerSaver ? ["--action=saver=" + I18n.tr("battery.profiles.powerSaver")] : []).concat([I18n.tr(critical ? "battery.alert.criticalTitle" : "battery.alert.lowTitle", [percent]), switched ? body + " " + I18n.tr("battery.alert.saverOn") : body]);
        notifier.running = false;
        notifier.running = true;
    }
    onLevelChanged: check()
    onDischargingChanged: check()
    Connections {
        target: UPower
        function onOnBatteryChanged() {
            Quickshell.execDetached(["hyprctl", "eval", "desktop_refresh_power()"]);
        }
    }
    FileView {
        id: settingsFile
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell/battery.json"
        // Read at once: a write before the first read would save the defaults over the saved values.
        blockLoading: true
        atomicWrites: true
        printErrors: false
        adapter: JsonAdapter {
            id: settings
            property bool autoSaver: true
            // The profile Power Saver replaced, until the charger brings it back (-1: none).
            property int restoreProfile: -1
        }
    }
    Component.onCompleted: Qt.callLater(check)
    // UPower reports peripheral levels in steps and only while the device is near: a slow poll is enough.
    Timer {
        interval: 60000
        running: root.peripherals.length > 0
        repeat: true
        triggeredOnStart: true
        onTriggered: root.checkPeripherals()
    }
    Process {
        id: notifier
        stdout: StdioCollector {
            onStreamFinished: {
                if (text.trim() === "saver")
                    PowerProfiles.profile = PowerProfile.PowerSaver;
            }
        }
    }
}
