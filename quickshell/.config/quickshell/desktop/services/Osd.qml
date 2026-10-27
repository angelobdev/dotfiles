pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
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
            show(input ? "microphone" : "volume", next.percent, next.muted, next.node.description, "");
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
        target: Brightness
        function onBrightnessChanged(monitorName, percent) {
            root.show("brightness", percent, false, monitorName, monitorName);
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
        }
    }
    Timer {
        id: expiry
        interval: Math.max(250, Config.osdTimeout)
        onTriggered: root.visible = false
    }
}
