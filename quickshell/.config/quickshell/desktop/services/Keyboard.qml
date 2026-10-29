pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// The on-screen keyboard: what it shows (osk/layouts/<layout>.json) and what it types, through osk.py, a
// virtual keyboard with the keymap of the physical one. Docked or floating and the extra row are saved.
// With Config.oskAutoShow the helper runs from the start as the input method too: in tablet mode a text
// field taking the focus opens the keyboard on the page for its purpose, and losing it closes a keyboard
// that opened by itself. Otherwise the helper starts the first time the keyboard is shown.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/osk.py"
    property bool shown: false
    readonly property bool floating: SessionState.oskFloating
    readonly property bool extra: SessionState.oskExtra
    // Purpose of the focused text field ("" without one); a terminal also gets the extra row.
    property string purpose: ""
    readonly property bool extraShown: extra || purpose === "terminal"
    // Opened by a text field rather than by hand, so it closes with the field.
    property bool autoShown: false
    property bool inputMethod: false
    property string page: "letters"
    // 0 off, 1 for the next key, 2 locked (Caps).
    property int shift: 0
    property bool ctrl: false
    property bool alt: false
    // Accented variants offered after a long press, in the strip above the keys.
    property var accents: []
    property var layout: ({
            pages: {},
            accents: {},
            extra: []
        })
    readonly property var rows: layout.pages[page] ?? []
    property bool ready: false
    // IPC and the assist button: "show", "hide", "toggle"; "float" and "dock" also show it in that form.
    function request(action) {
        if (!["show", "hide", "toggle", "float", "dock"].includes(action))
            return false;
        if (action === "float" || action === "dock")
            setFloating(action === "float");
        setShown(action !== "hide" && (action !== "toggle" || !shown));
        return true;
    }
    function setShown(value) {
        shown = value;
        autoShown = false;
        accents = [];
        if (!value) {
            page = "letters";
            shift = 0;
            ctrl = false;
            alt = false;
        } else if (!process.running) {
            process.running = true;
        }
    }
    function setFloating(value) {
        SessionState.set("oskFloating", value);
    }
    function setExtra(value) {
        SessionState.set("oskExtra", value);
    }
    function send(code, mods) {
        if (process.running)
            process.write("key " + code + " " + mods + "\n");
    }
    // A key of the layout: shift and the one-shot modifiers apply to it, then reset.
    function type(key) {
        let mods = key.mods ?? 0;
        if (!key.mods && shift > 0 && (key.shift || /^[a-z]$/.test(key.label ?? "")))
            mods |= 1;
        if (ctrl)
            mods |= 4;
        if (alt)
            mods |= 8;
        send(key.code, mods);
        accents = [];
        if (shift === 1)
            shift = 0;
        ctrl = false;
        alt = false;
    }
    function shiftTapped() {
        // A second tap while shift is on for one key locks it; a tap on a lock releases it.
        shift = shift === 0 ? 1 : shift === 1 && shiftTimer.running ? 2 : 0;
        shiftTimer.restart();
    }
    function longPress(key) {
        accents = layout.accents[key.label] ?? [];
    }
    function labelOf(key) {
        if (key.action === "page")
            return key.page === "letters" ? I18n.tr("osk.keys.letters") : key.page === "symbols" ? I18n.tr("osk.keys.symbols") : I18n.tr("osk.keys.more");
        if (key.name === "esc")
            return I18n.tr("osk.keys.esc");
        if (key.name === "tab")
            return I18n.tr("osk.keys.tab");
        if (key.name === "ctrl")
            return I18n.tr("osk.keys.ctrl");
        if (key.name === "alt")
            return I18n.tr("osk.keys.alt");
        const label = key.label ?? "";
        return shift > 0 && /^[a-z]$/.test(label) ? label.toUpperCase() : label;
    }
    function focusIn(fieldPurpose) {
        hideTimer.stop();
        purpose = fieldPurpose;
        if (!Config.oskAutoShow || !Tablet.active)
            return;
        if (!shown) {
            setShown(true);
            autoShown = true;
        }
        if (autoShown)
            page = ["digits", "number", "phone", "pin"].includes(fieldPurpose) ? "symbols" : "letters";
    }
    function focusOut() {
        purpose = "";
        // Moving between fields deactivates one and activates the next: wait before closing.
        if (autoShown)
            hideTimer.restart();
    }
    Timer {
        id: hideTimer
        interval: 300
        onTriggered: {
            if (root.autoShown)
                root.setShown(false);
        }
    }
    Connections {
        target: Tablet
        function onActiveChanged() {
            if (!Tablet.active && root.autoShown)
                root.setShown(false);
        }
    }
    Component.onCompleted: {
        if (Config.oskAutoShow)
            process.running = true;
    }
    Timer {
        id: shiftTimer
        interval: 400
    }
    Process {
        id: process
        command: ["python3", root.helper, "run"].concat(Config.oskAutoShow ? ["--input-method"] : [])
        stdinEnabled: true
        stdout: SplitParser {
            onRead: data => {
                let message;
                try {
                    message = JSON.parse(data);
                } catch (failure) {
                    return;
                }
                if (message.status === "ready") {
                    root.ready = true;
                    root.inputMethod = Config.oskAutoShow;
                } else if (message.event === "activate") {
                    root.focusIn(message.purpose ?? "normal");
                } else if (message.event === "deactivate") {
                    root.focusOut();
                } else if (message.event === "unavailable") {
                    root.inputMethod = false;
                }
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "")
                    console.warn("osk:", text.trim());
            }
        }
        onExited: {
            root.ready = false;
            root.inputMethod = false;
        }
    }
    FileView {
        path: decodeURIComponent(Qt.resolvedUrl("../osk/layouts/" + Config.oskLayout + ".json").toString().replace(/^file:\/\//, ""))
        printErrors: false
        onLoaded: {
            try {
                root.layout = JSON.parse(text());
            } catch (failure) {
                console.warn("osk: layout", failure);
            }
        }
    }
}
