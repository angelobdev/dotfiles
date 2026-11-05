pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.UPower
import ".."

// Warns once per discharge when the battery runs low, and again when it is critical. Plugging the charger in
// resets both; a level that wobbles around a threshold warns only once.
Singleton {
    id: root
    readonly property var device: UPower.displayDevice
    readonly property bool present: device?.isLaptopBattery ?? false
    readonly property int percent: Math.round((device?.percentage ?? 0) * 100)
    readonly property bool discharging: present && UPower.onBattery
    // 0 fine, 1 low, 2 critical.
    readonly property int level: !discharging ? 0 : percent <= Config.batteryCritical ? 2 : percent <= Config.batteryLow ? 1 : 0
    property int announced: 0
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
            return;
        }
        if (level <= announced)
            return;
        announced = level;
        const left = duration(device?.timeToEmpty ?? 0);
        const critical = level === 2;
        notifier.command = ["notify-send", "--wait", "--app-name=" + I18n.tr("battery.title"), "--app-icon=" + (critical ? "battery-caution" : "battery-low"), "--urgency=" + (critical ? "critical" : "normal")].concat(!critical && PowerProfiles.profile !== PowerProfile.PowerSaver ? ["--action=saver=" + I18n.tr("battery.profiles.powerSaver")] : []).concat([I18n.tr(critical ? "battery.alert.criticalTitle" : "battery.alert.lowTitle", [percent]), left ? I18n.tr(critical ? "battery.alert.criticalBodyTime" : "battery.alert.lowBodyTime", [left]) : I18n.tr(critical ? "battery.alert.criticalBody" : "battery.alert.lowBody")]);
        notifier.running = false;
        notifier.running = true;
    }
    onLevelChanged: check()
    onDischargingChanged: check()
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
