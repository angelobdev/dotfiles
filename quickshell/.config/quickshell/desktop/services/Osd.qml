pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Services.UPower
import ".."

Singleton {
    id: root
    property bool visible: false
    property string kind: ""
    property string title: ""
    property string detail: ""
    property string iconName: "volume-high"
    property int percent: 0
    property bool muted: false
    property var targetScreen: null
    property bool armed: false
    property var outputState: null
    property var inputState: null

    function audioState(input) {
        const node = input ? Audio.source : Audio.sink;
        return node?.ready && node.audio ? {
            node: node,
            percent: input ? Audio.inputVolume : Audio.volume,
            muted: input ? Audio.inputMuted : Audio.muted
        } : null;
    }
    function suppressed(type) {
        return ShellState.panel === "controls" || (type !== "brightness" && ShellState.panel === "audio");
    }
    function dismiss() {
        visible = false;
        expiry.stop();
    }
    function show(type, level, isMuted, description, monitorName) {
        if (!Config.osdEnabled || suppressed(type) || !Number.isFinite(level))
            return;
        const screen = ShellState.screenNamed(monitorName || Hyprland.focusedMonitor?.name);
        if (!screen)
            return;
        targetScreen = screen;
        kind = type;
        percent = Math.max(0, Math.round(level));
        muted = isMuted;
        detail = description;
        title = type === "brightness" ? I18n.tr("brightness.title") : type === "microphone" ? I18n.tr("audio.microphone") : I18n.tr("audio.volume");
        iconName = type === "brightness" ? "sun" : type === "microphone" ? (isMuted ? "microphone-muted" : "microphone") : (isMuted || percent === 0) ? "volume-muted" : percent < 35 ? "volume-low" : "volume-high";
        visible = true;
        expiry.restart();
    }
    // Feedback for a toggle (Do Not Disturb, Keep awake): an icon, a title and its new state, no level.
    // Shown even with notifications silenced: it is the shell answering a key, not a notification.
    function showState(icon, heading, state) {
        showMessage(icon, heading, state, -1);
    }
    // Any action that wants to confirm itself (desktop-shell osd): an icon of assets/icons, a title, a line under
    // it, and a level from 0 to 100 drawn as the bar of the volume (-1 for none).
    function layoutKey(mode) {
        return "workspaces.layouts." + (["scrolling", "floating"].includes(mode) ? mode : "dwindle");
    }
    function showMessage(icon, heading, line, progress) {
        if (!Config.osdEnabled)
            return false;
        const screen = ShellState.screenNamed(Hyprland.focusedMonitor?.name);
        if (!screen)
            return false;
        targetScreen = screen;
        kind = progress >= 0 ? "progress" : "state";
        percent = progress >= 0 ? Math.min(100, Math.round(progress)) : 0;
        muted = false;
        iconName = icon;
        title = heading;
        detail = line;
        visible = true;
        expiry.restart();
        return true;
    }
    // What config/binds.lua confirms through "desktop-osd NAME on|off" custom events: its window tricks, by the
    // names of their binds (the Hints labels).
    readonly property var tricks: ({
            popOut: {
                icon: "pin",
                title: "bindings.popOut"
            },
            transparency: {
                icon: "eye",
                title: "bindings.transparency"
            },
            workspaceGaps: {
                icon: "split",
                title: "bindings.workspaceGaps"
            },
            tiledFullscreen: {
                icon: "fullscreen",
                title: "bindings.tiledFullscreen"
            },
            fullscreenDesktop: {
                icon: "fullscreen",
                title: "bindings.fullscreenDesktop"
            }
        })
    // The keyboard layout and the power profile last seen, so only a change is shown (not the first reading).
    property string layout: ""
    property int profile: -1
    function observeAudio(input) {
        const next = audioState(input);
        const previous = input ? inputState : outputState;
        if (input)
            inputState = next;
        else
            outputState = next;
        // Seed on startup/reconnect; only changes on the same ready node are events.
        if (!armed || !next || !previous || next.node !== previous.node)
            return;
        if (next.percent !== previous.percent || next.muted !== previous.muted)
            show(input ? "microphone" : "volume", next.percent, next.muted, Audio.deviceName(next.node), "");
    }
    Connections {
        target: Audio
        function onSinkChanged() {
            root.observeAudio(false);
        }
        function onSourceChanged() {
            root.observeAudio(true);
        }
        function onVolumeChanged() {
            root.observeAudio(false);
        }
        function onMutedChanged() {
            root.observeAudio(false);
        }
        function onInputVolumeChanged() {
            root.observeAudio(true);
        }
        function onInputMutedChanged() {
            root.observeAudio(true);
        }
    }
    Connections {
        target: Audio.sink
        function onReadyChanged() {
            root.observeAudio(false);
        }
    }
    Connections {
        target: Audio.source
        function onReadyChanged() {
            root.observeAudio(true);
        }
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "custom" && event.data.startsWith("desktop-osd ")) {
                const words = event.data.split(" ");
                const trick = root.tricks[words[1]];
                // The layout of a workspace (config/workspace_layouts.lua) says which one it is now.
                if (words[1] === "workspaceLayout")
                    root.showState(words[2] === "scrolling" ? "split" : words[2] === "floating" ? "window" : "overview", I18n.tr("bindings.workspaceLayout"), I18n.tr(root.layoutKey(words[2])));
                else if (trick)
                    root.showState(trick.icon, I18n.tr(trick.title), I18n.tr(words[2] === "on" ? "common.on" : "common.off"));
            } else if (event.name === "activelayout") {
                // "keyboard,Layout name" for every keyboard that switches: one OSD for the layout.
                const name = event.data.slice(event.data.indexOf(",") + 1);
                if (root.layout !== "" && name !== root.layout)
                    root.showState("keyboard", I18n.tr("bar.widgets.keyboardLayout.name"), name);
                root.layout = name;
            }
        }
    }
    Connections {
        target: PowerProfiles
        function onProfileChanged() {
            const next = PowerProfiles.profile;
            if (root.profile >= 0 && next !== root.profile)
                root.showState(next === PowerProfile.PowerSaver ? "leaf" : next === PowerProfile.Performance ? "performance" : "balanced", I18n.tr("battery.profile"), next === PowerProfile.PowerSaver ? I18n.tr("battery.profiles.powerSaver") : next === PowerProfile.Performance ? I18n.tr("battery.profiles.performance") : I18n.tr("battery.profiles.balanced"));
            root.profile = next;
        }
    }
    Connections {
        target: Brightness
        function onBrightnessChanged(monitorName, percent) {
            root.show("brightness", percent, false, HyprSettings.displayName(monitorName), monitorName);
        }
    }
    Connections {
        target: ShellState
        function onPanelChanged() {
            if (root.suppressed(root.kind))
                root.dismiss();
        }
    }
    Connections {
        target: Quickshell
        function onScreensChanged() {
            if (!Quickshell.screens.includes(root.targetScreen))
                root.dismiss();
        }
    }
    Timer {
        interval: 700
        running: true
        onTriggered: {
            root.outputState = root.audioState(false);
            root.inputState = root.audioState(true);
            root.armed = true;
            // Read now, so the first change after start-up is shown and the start-up value is not.
            root.profile = PowerProfiles.profile;
        }
    }
    Timer {
        id: expiry
        interval: Math.max(250, Config.osdTimeout)
        onTriggered: root.visible = false
    }
}
