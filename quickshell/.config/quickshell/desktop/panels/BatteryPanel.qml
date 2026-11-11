import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Services.UPower
import ".."
import "../components"
import "../services"
import "power"

Overlay {
    id: root
    panelName: "battery"
    readonly property var battery: UPower.displayDevice
    readonly property bool available: (battery?.ready ?? false) && (battery?.isLaptopBattery ?? false)
    readonly property bool charging: battery?.state === UPowerDeviceState.Charging
    readonly property bool discharging: battery?.state === UPowerDeviceState.Discharging
    readonly property string stateLabel: {
        switch (battery?.state) {
        case UPowerDeviceState.Charging:
            return I18n.tr("battery.charging");
        case UPowerDeviceState.Discharging:
            return I18n.tr("battery.onBattery");
        case UPowerDeviceState.FullyCharged:
            return I18n.tr("battery.fullyCharged");
        case UPowerDeviceState.Empty:
            return I18n.tr("battery.empty");
        case UPowerDeviceState.PendingCharge:
            return I18n.tr("battery.pendingCharge");
        case UPowerDeviceState.PendingDischarge:
            return I18n.tr("battery.pendingDischarge");
        default:
            return I18n.tr("battery.statusUnavailable");
        }
    }
    // The internal display (config/displays.lua keeps its refresh, one for battery and one for mains power): VRR
    // when it can, or one of its fixed rates; "" is its preferred mode.
    // Only the monitors in use, as hyprctl monitors lists them: a panel switched off (lid closed) has no refresh to choose.
    readonly property var monitors: HyprSettings.monitorList.filter(m => !m.disabled)
    property var refreshChoices: ({
            battery: "",
            ac: ""
        })
    readonly property var panelMonitor: monitors.find(m => HyprSettings.isPanel(m.name)) ?? null
    readonly property var refreshOptions: {
        const monitor = panelMonitor;
        if (!monitor)
            return [];
        const size = monitor.width + "x" + monitor.height + "@";
        const options = monitor.hardwareDetails?.vrrCapable ? [{
                value: "vrr",
                label: I18n.tr("battery.display.vrr"),
                tooltip: I18n.tr("battery.display.vrrHint")
            }] : [];
        const rates = [];
        for (const mode of (monitor.availableModes ?? []).map(m => m.replace(/Hz$/, "")).filter(m => m.startsWith(size))) {
            const rate = Math.round(parseFloat(mode.slice(size.length)));
            if (rate > 0 && !rates.some(r => r.rate === rate))
                rates.push({
                    value: mode,
                    rate: rate,
                    label: I18n.tr("battery.display.rate", [rate]),
                    tooltip: I18n.tr("battery.display.fixedHint", [rate])
                });
        }
        rates.sort((a, b) => b.rate - a.rate);
        const all = options.concat(rates);
        return all.length > 1 ? all : [];
    }
    // The display lists its preferred mode first.
    readonly property int preferredRate: Math.round(parseFloat(((panelMonitor?.availableModes ?? [])[0] ?? "").split("@")[1] ?? "0"))
    function refreshSelected(source, option) {
        const choice = refreshChoices[source] ?? "";
        if (choice === "vrr" || option.value === "vrr")
            return choice === option.value;
        return option.rate === (choice ? Math.round(parseFloat(choice.split("@")[1])) : preferredRate);
    }
    function chooseRefresh(source, value) {
        const choices = Object.assign({}, refreshChoices);
        choices[source] = value;
        refreshChoices = choices;
        Quickshell.execDetached(["hyprctl", "eval", "desktop_refresh(\"" + source + "\", \"" + value + "\")"]);
        relist.restart();
    }
    function readChoices(text) {
        // `refresh` is the single choice saved before there was one per power source.
        const single = (text.match(/refresh\s*=\s*"([\w@.]+)"/) ?? [])[1] ?? "";
        refreshChoices = {
            battery: (text.match(/battery\s*=\s*"([\w@.]+)"/) ?? [])[1] ?? single,
            ac: (text.match(/ac\s*=\s*"([\w@.]+)"/) ?? [])[1] ?? single
        };
    }
    onOpened: {
        HyprSettings.listMonitors();
        refreshState.reload();
    }
    Timer {
        id: relist
        interval: 600
        onTriggered: HyprSettings.listMonitors()
    }
    FileView {
        id: refreshState
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session/refresh.lua"
        printErrors: false
        onLoaded: root.readChoices(text())
        onLoadFailed: root.readChoices("")
    }
    function duration(seconds) {
        if (!Number.isFinite(seconds) || seconds <= 0)
            return I18n.tr("battery.estimateUnavailable");
        const minutes = Math.max(1, Math.round(seconds / 60));
        return minutes >= 60 ? I18n.tr("battery.durationHours", [Math.floor(minutes / 60), minutes % 60]) : I18n.tr("battery.durationMinutes", [minutes]);
    }

    SidePanelCard {
        // As tall as its content, up to the screen.
        height: Math.min(content.implicitHeight + 2 * Theme.panelPadding, parent.height - Theme.panelClearance)
        ColumnLayout {
            id: content
            anchors {
                fill: parent
                margins: Theme.panelPadding
            }
            spacing: 14
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("battery.title")
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: availableWidth
                clip: true
                ColumnLayout {
                    width: parent.width
                    spacing: 12
                    RowLayout {
                        Icon {
                            name: root.charging ? "battery-charging" : "battery-" + Math.round((root.battery?.percentage ?? 0) * 4) * 25
                            Layout.preferredWidth: 30
                            Layout.preferredHeight: 30
                        }
                        Text {
                            text: root.available ? Math.round(root.battery.percentage * 100) + "%" : I18n.tr("battery.unavailable")
                            font.pixelSize: Theme.textSize(36)
                            font.family: Theme.font
                            color: Theme.text
                        }
                    }
                    Text {
                        visible: root.available
                        text: root.stateLabel
                        color: Theme.muted
                    }
                    ProgressBar {
                        id: level
                        Layout.fillWidth: true
                        visible: root.available
                        from: 0
                        to: 1
                        value: root.battery?.percentage ?? 0
                        background: Rectangle {
                            implicitHeight: 7
                            radius: 4
                            color: Theme.track
                        }
                        contentItem: Item {
                            implicitHeight: 7
                            Rectangle {
                                width: level.visualPosition * parent.width
                                height: parent.height
                                radius: 4
                                color: Theme.accent
                            }
                        }
                    }
                    GridLayout {
                        visible: root.available
                        Layout.fillWidth: true
                        columns: 2
                        columnSpacing: 12
                        rowSpacing: 12
                        Text {
                            text: root.charging ? I18n.tr("battery.chargingPower") : root.discharging ? I18n.tr("battery.powerDraw") : I18n.tr("battery.powerFlow")
                            color: Theme.muted
                            font.pixelSize: Theme.textSize(12)
                        }
                        Text {
                            text: Math.abs(root.battery?.changeRate ?? 0).toLocaleString(I18n.locale, "f", 1) + " W"
                            color: Theme.text
                            font.pixelSize: Theme.textSize(12)
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignRight
                        }
                        Text {
                            text: root.charging ? I18n.tr("battery.timeUntilFull") : I18n.tr("battery.timeRemaining")
                            color: Theme.muted
                            font.pixelSize: Theme.textSize(12)
                        }
                        Text {
                            text: root.charging ? root.duration(root.battery?.timeToFull) : root.discharging ? root.duration(root.battery?.timeToEmpty) : root.stateLabel
                            color: Theme.text
                            font.pixelSize: Theme.textSize(12)
                            Layout.fillWidth: true
                            wrapMode: Text.Wrap
                            horizontalAlignment: Text.AlignRight
                        }
                        Text {
                            text: I18n.tr("battery.availableEnergy")
                            color: Theme.muted
                            font.pixelSize: Theme.textSize(12)
                        }
                        Text {
                            text: (root.battery?.energy ?? 0).toLocaleString(I18n.locale, "f", 1) + " / " + (root.battery?.energyCapacity ?? 0).toLocaleString(I18n.locale, "f", 1) + " Wh"
                            color: Theme.text
                            font.pixelSize: Theme.textSize(12)
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignRight
                        }
                    }
                    Heading {
                        visible: Battery.peripherals.length > 0
                        text: I18n.tr("battery.devices")
                        font.pixelSize: Theme.textSize(14)
                        Layout.topMargin: 6
                    }
                    Repeater {
                        model: Battery.peripherals
                        RowLayout {
                            id: peripheral
                            required property var modelData
                            readonly property int percent: Math.round(modelData.percentage * 100)
                            Layout.fillWidth: true
                            spacing: 10
                            Icon {
                                name: "battery-" + Math.round(peripheral.modelData.percentage * 4) * 25
                                color: peripheral.percent <= Config.peripheralLow ? Theme.danger : Theme.text
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 20
                            }
                            Text {
                                Layout.fillWidth: true
                                text: Battery.peripheralName(peripheral.modelData)
                                textFormat: Text.PlainText
                                color: Theme.text
                                elide: Text.ElideRight
                            }
                            Text {
                                text: peripheral.percent + "%"
                                color: Theme.muted
                            }
                        }
                    }
                    Heading {
                        text: I18n.tr("battery.profile")
                        font.pixelSize: Theme.textSize(14)
                        Layout.topMargin: 6
                    }
                    PowerProfileView {
                        Layout.fillWidth: true
                        laptop: root.available
                    }
                    Heading {
                        visible: root.refreshOptions.length > 0
                        text: I18n.tr("battery.display.title")
                        font.pixelSize: Theme.textSize(14)
                        Layout.topMargin: 6
                    }
                    Repeater {
                        model: root.refreshOptions.length > 0 ? [
                            {
                                source: "battery",
                                label: I18n.tr("battery.display.onBattery")
                            },
                            {
                                source: "ac",
                                label: I18n.tr("battery.display.onMains")
                            }
                        ] : []
                        ColumnLayout {
                            id: refreshRow
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: 6
                            Text {
                                text: refreshRow.modelData.label
                                color: Theme.muted
                                font.pixelSize: Theme.textSize(12)
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8
                                Repeater {
                                    model: root.refreshOptions
                                    ActionButton {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        text: modelData.label
                                        tooltip: modelData.tooltip
                                        highlighted: root.refreshSelected(refreshRow.modelData.source, modelData)
                                        tone: "state"
                                        onClicked: root.chooseRefresh(refreshRow.modelData.source, modelData.value)
                                    }
                                }
                            }
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        wrapMode: Text.Wrap
                        font.pixelSize: Theme.textSize(11)
                        color: Theme.muted
                        text: I18n.tr("battery.estimatesHint")
                    }
                }
            }
        }
    }
}
