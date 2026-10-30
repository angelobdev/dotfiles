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
    // The session is locked (desktop-power around hyprlock); in tablet mode the docked keyboard shows over
    // the lock for the password.
    property bool locked: false
    property bool lockShown: false
    // Where the keyboard is, in the coordinates of its screen (set by KeyboardWindow); panels leave this
    // rectangle out of their input region, so a touch there always reaches the keyboard.
    property string screenName: ""
    property bool areaVisible: false
    property rect area: Qt.rect(0, 0, 0, 0)
    // Height the docked keyboard reserves at the bottom of its screen (0 when hidden or floating): layers
    // anchored to the bottom, like the dock, sit that much higher.
    property real reserved: 0
    function reservedOn(name) {
        return name === screenName ? reserved : 0;
    }
    property string page: "letters"
    // 0 off, 1 for the next key, 2 locked (Caps).
    property int shift: 0
    property bool ctrl: false
    property bool alt: false
    // Accented variants offered after a long press, in the strip above the keys.
    property var accents: []
    // The word being typed through these keys. It starts again at anything but a letter and in every field;
    // an app can move its caret without saying so, but a stale word only leans on the keys a little.
    property string word: ""
    // Letters likely next, from osk.py: empty until it answers, and in fields the prediction stays out of.
    property var letters: ({})
    readonly property bool predicting: Config.oskPrediction && shown && !locked && page === "letters" && ["", "normal", "alpha", "name"].includes(purpose)
    // Offsets of touches from the centre of their letter, as running totals.
    property var touchTotals: {
        try {
            return JSON.parse(SessionState.oskTouch);
        } catch (failure) {
            return {
                count: 0,
                x: 0,
                y: 0,
                xx: 0,
                yy: 0
            };
        }
    }
    property var layout: ({
            pages: {},
            accents: {},
            extra: []
        })
    readonly property var rows: layout.pages[page] ?? []
    property bool ready: false
    // A full-screen layer that maps over a shown keyboard (a panel, a password prompt) asks for it to be
    // mapped again on top (KeyboardWindow).
    signal raiseRequested
    function raise() {
        if (shown)
            raiseRequested();
    }
    // IPC and the assist button: "show", "hide", "toggle"; "float" and "dock" also show it in that form.
    function request(action) {
        if (action === "locked" || action === "unlocked") {
            setLocked(action === "locked");
            return true;
        }
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
    // Locking moves the focus from the text field to the lock, which would close a keyboard that the field
    // opened by itself, right when it is needed for the password: while locked it does not close by itself.
    function setLocked(value) {
        locked = value;
        if (value) {
            hideTimer.stop();
            if (Tablet.active && !shown) {
                setShown(true);
                lockShown = true;
            }
        } else if (lockShown) {
            setShown(false);
        } else if (autoShown && purpose === "") {
            // Opened by a field that did not get the focus back after the unlock.
            hideTimer.restart();
        }
        if (!value)
            lockShown = false;
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
    function setWord(value) {
        word = value;
        letters = ({});
        if (predicting && ready)
            process.write("predict " + value + "\n");
    }
    function noteTouch(dx, dy) {
        if (!Config.oskTouchStats || !predicting)
            return;
        const totals = touchTotals;
        touchTotals = {
            count: totals.count + 1,
            x: totals.x + dx,
            y: totals.y + dy,
            xx: totals.xx + dx * dx,
            yy: totals.yy + dy * dy
        };
        saveTouch.start();
    }
    // Pixels: the mean offset of a touch and how far touches spread around it.
    function touchSpread() {
        const t = touchTotals;
        if (t.count === 0)
            return {
                count: 0
            };
        const spread = (sum, squares) => Math.sqrt(Math.max(0, squares / t.count - (sum / t.count) ** 2));
        return {
            count: t.count,
            meanX: t.x / t.count,
            meanY: t.y / t.count,
            spreadX: spread(t.x, t.xx),
            spreadY: spread(t.y, t.yy)
        };
    }
    // Space goes down with the finger and up with it, like a physical key: held, the app sees it repeat,
    // which is how Claude Code tells its hold-to-talk Space from a typed one.
    function hold(key, down) {
        if (!process.running)
            return;
        process.write((down ? "press " : "release ") + key.code + "\n");
        if (down)
            setWord("");
        if (!down) {
            accents = [];
            if (shift === 1)
                shift = 0;
        }
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
        if (key.action === "backspace")
            setWord(word.slice(0, -1));
        else
            setWord(!ctrl && !alt && /^[a-zàèéìòù]$/.test(key.label ?? "") ? word + key.label : "");
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
        setWord("");
        // A field of a panel (the launcher search) keeps a keyboard that the panel would have closed, and
        // brings it back over the panel.
        if (shown && ShellState.panel !== "")
            raise();
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
        setWord("");
        if (locked)
            return;
        // Moving between fields deactivates one and activates the next: wait before closing.
        if (autoShown)
            hideTimer.restart();
    }
    Timer {
        id: hideTimer
        interval: 300
        onTriggered: {
            if (root.autoShown && !root.locked)
                root.setShown(false);
        }
    }
    // A panel opening over a keyboard that a field opened (the terminal behind it) closes it unless the panel
    // focuses a field of its own; a keyboard opened by hand stays and comes back on top.
    Connections {
        target: ShellState
        function onPanelChanged() {
            if (ShellState.panel === "" || !root.shown)
                return;
            if (root.autoShown)
                hideTimer.restart();
            else
                root.raise();
        }
    }
    Connections {
        target: Tablet
        function onActiveChanged() {
            if (!Tablet.active && root.autoShown)
                root.setShown(false);
        }
    }
    // The assistant console keeps the focus of its terminal while hidden when no other window takes it
    // (an empty workspace), so showing and hiding it bring no activate or deactivate: follow the console.
    Connections {
        target: Agent
        function onConsoleOpenChanged() {
            if (Agent.consoleOpen && root.purpose !== "")
                root.focusIn(root.purpose);
            else if (!Agent.consoleOpen && root.autoShown)
                hideTimer.restart();
        }
    }
    onPredictingChanged: setWord(word)
    onReadyChanged: setWord(word)
    Component.onCompleted: {
        if (Config.oskAutoShow)
            process.running = true;
    }
    Timer {
        id: saveTouch
        interval: 30000
        onTriggered: SessionState.set("oskTouch", JSON.stringify(root.touchTotals))
    }
    Timer {
        id: shiftTimer
        interval: 400
    }
    // The helper restarts if it exits while needed (always with automatic opening, else while shown): a dead
    // helper would drop every key, the password on the lock screen included.
    Timer {
        interval: 3000
        repeat: true
        running: (Config.oskAutoShow || root.shown) && !process.running
        onTriggered: process.running = true
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
                } else if (message.event === "letters") {
                    if (message.word === root.word && root.predicting)
                        root.letters = message.letters;
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
