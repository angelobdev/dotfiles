import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."
import "../../components"
import "../../services"
import "../theming"

// Settings → Displays, below the monitors and their mode: resolution and refresh of one monitor (only the modes
// it reports: custom ones crashed Hyprland 0.57.1), position and scale. Nothing changes until Apply, and then
// only for 15 seconds unless kept: without Keep, or with Revert, the previous settings come back (a screen
// left black can still be recovered). On the laptop panel only scale and position count: its refresh is the
// one chosen per power source in the battery panel (config/displays.lua).
ColumnLayout {
    id: root
    Layout.fillWidth: true
    // On screen: the monitors are read again each time it shows.
    property bool shown: false
    spacing: 6
    readonly property var monitors: HyprSettings.monitorList.filter(entry => entry.name !== "FALLBACK")
    property string selected: ""
    readonly property var monitor: monitors.find(entry => entry.name === selected) ?? null
    readonly property bool panel: HyprSettings.isPanel(selected)
    readonly property var saved: HyprSettings.monitors[selected] ?? null
    // The form, from the saved settings or what the monitor runs now.
    property string resolution: ""
    property string rate: ""
    property real chosenScale: 1
    property string position: "auto"
    readonly property var scales: [1, 1.25, 1.333, 1.5, 1.667, 1.75, 2, 2.5, 3]
    readonly property var positions: ["auto", "auto-left", "auto-right", "auto-up", "auto-down"]
    // "2560x1440@59.95Hz" → { resolution: "2560x1440", rate: "59.95" }, each listed once.
    readonly property var modes: {
        const seen = {};
        const list = [];
        for (const text of monitor?.availableModes ?? []) {
            const match = String(text).match(/^(\d+x\d+)@([\d.]+)Hz$/);
            if (match && !seen[match[0]]) {
                seen[match[0]] = true;
                list.push({
                    resolution: match[1],
                    rate: match[2]
                });
            }
        }
        return list;
    }
    readonly property var resolutions: modes.map(mode => mode.resolution).filter((value, index, all) => all.indexOf(value) === index)
    readonly property var rates: modes.filter(mode => mode.resolution === resolution).map(mode => mode.rate)
    function load() {
        HyprSettings.listMonitors();
    }
    onShownChanged: if (shown)
        load()
    Component.onCompleted: if (shown)
        load()
    onSelectedChanged: fill()
    // The form from the saved settings, else from the monitor as it runs. Both looked up here, not through the
    // monitor and saved bindings: on a change of selected this runs before they follow it.
    function fill() {
        const current = monitors.find(entry => entry.name === selected) ?? null;
        const chosen = HyprSettings.monitors[selected] ?? null;
        const match = String(chosen?.mode ?? "").match(/^(\d+x\d+)@([\d.]+)$/);
        if (match) {
            resolution = match[1];
            rate = match[2];
        } else if (current) {
            resolution = current.width + "x" + current.height;
            rate = Number(current.refreshRate).toFixed(2);
        }
        chosenScale = chosen?.scale ?? current?.scale ?? 1;
        position = chosen?.position ?? "auto";
    }
    function nearestScale(value) {
        return scales.reduce((best, entry) => Math.abs(entry - value) < Math.abs(best - value) ? entry : best, scales[0]);
    }
    function apply() {
        const fields = {
            scale: chosenScale,
            position: position
        };
        // A listed mode only, and never on the panel.
        if (!panel && modes.some(mode => mode.resolution === resolution && mode.rate === rate))
            fields.mode = resolution + "@" + rate;
        HyprSettings.tryMonitor(selected, fields);
        relist.restart();
    }
    function reset() {
        HyprSettings.setMonitor(selected, null);
        relist.restart();
    }
    // The countdown lives in HyprSettings, so it reverts even if this window is gone by then.
    Connections {
        target: HyprSettings
        function onMonitorsReverted() {
            relist.restart();
        }
    }
    // After a change the monitors are listed again, once Hyprland has reloaded.
    Timer {
        id: relist
        interval: 1500
        onTriggered: root.load()
    }
    // The shared listing (HyprSettings), whichever view asked for it: the form follows it while on screen.
    Connections {
        target: HyprSettings
        function onMonitorsListed() {
            if (!root.monitors.some(entry => entry.name === root.selected))
                root.selected = root.monitors[0]?.name ?? "";
            else if (root.shown && !HyprSettings.trying)
                root.fill();
        }
    }
    Text {
        text: I18n.tr("settings.monitors.title")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        font.weight: Font.DemiBold
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: form.implicitHeight + 24
        radius: Theme.corner(12)
        color: Theme.tile
        ColumnLayout {
            id: form
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 12
                leftMargin: 14
                rightMargin: 14
            }
            spacing: 10
            ChoiceChips {
                visible: root.monitors.length > 1
                enabled: !HyprSettings.trying
                options: root.monitors.map(entry => ({
                            name: entry.name,
                            label: entry.name
                        }))
                current: root.selected
                onChosen: name => root.selected = name
            }
            Setting {
                visible: !root.panel && root.resolutions.length > 0
                label: I18n.tr("settings.monitors.resolution")
                options: root.resolutions.map(value => ({
                            name: value,
                            label: value.replace("x", " × ")
                        }))
                current: root.resolution
                onChosen: name => {
                    root.resolution = name;
                    if (!root.rates.includes(root.rate))
                        root.rate = root.rates[0] ?? "";
                }
            }
            Setting {
                visible: !root.panel && root.rates.length > 0
                label: I18n.tr("settings.monitors.refresh")
                options: root.rates.map(value => ({
                            name: value,
                            label: I18n.tr("settings.monitors.hertz", [value])
                        }))
                current: root.rate
                onChosen: name => root.rate = name
            }
            Text {
                Layout.fillWidth: true
                visible: root.panel
                text: I18n.tr("settings.monitors.panelHint")
                wrapMode: Text.WordWrap
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
            Setting {
                label: I18n.tr("settings.monitors.scale")
                options: root.scales.map(value => ({
                            name: String(value),
                            label: Math.round(value * 100) + "%"
                        }))
                current: String(root.nearestScale(root.chosenScale))
                onChosen: name => root.chosenScale = Number(name)
            }
            Setting {
                label: I18n.tr("settings.monitors.position")
                options: root.positions.map(value => ({
                            name: value,
                            label: I18n.tr({
                                "auto": "settings.monitors.positions.auto",
                                "auto-left": "settings.monitors.positions.left",
                                "auto-right": "settings.monitors.positions.right",
                                "auto-up": "settings.monitors.positions.up",
                                "auto-down": "settings.monitors.positions.down"
                            }[value])
                        }))
                current: root.position
                onChosen: name => root.position = name
            }
            RowLayout {
                visible: !HyprSettings.trying
                spacing: 8
                ActionButton {
                    highlighted: true
                    text: I18n.tr("settings.monitors.apply")
                    enabled: root.selected !== "" && !Config.unreadable
                    onClicked: root.apply()
                }
                ActionButton {
                    visible: root.saved !== null
                    text: I18n.tr("settings.monitors.reset")
                    onClicked: root.reset()
                }
            }
            // The countdown: keep, or go back now; at zero it goes back by itself.
            RowLayout {
                visible: HyprSettings.trying
                Layout.fillWidth: true
                spacing: 8
                Text {
                    Layout.fillWidth: true
                    text: I18n.tr("settings.monitors.confirm", [HyprSettings.secondsLeft])
                    wrapMode: Text.WordWrap
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(13)
                }
                ActionButton {
                    highlighted: true
                    text: I18n.tr("settings.monitors.keep")
                    onClicked: HyprSettings.keepMonitors()
                }
                ActionButton {
                    text: I18n.tr("settings.monitors.revert")
                    onClicked: HyprSettings.revertMonitors()
                }
            }
            Text {
                Layout.fillWidth: true
                visible: HyprSettings.skipped.some(name => name.startsWith("monitors."))
                text: I18n.tr("settings.hypr.skipped", [HyprSettings.skipped.filter(name => name.startsWith("monitors.")).join(", ")])
                wrapMode: Text.WordWrap
                color: Theme.danger
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
        }
    }
}
