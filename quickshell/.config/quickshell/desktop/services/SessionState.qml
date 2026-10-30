pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io

// Shell toggles that outlive restarts and logins (Keep awake, Do Not Disturb, rotation lock, the on-screen
// keyboard form, Night shift), in one small state file. A missing or unreadable file leaves them off, as before they were saved.
Singleton {
    id: root
    readonly property string stateDir: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-shell"
    readonly property bool keepAwake: state.keepAwake === true
    readonly property bool quiet: state.quiet === true
    readonly property bool rotationLock: state.rotationLock === true
    readonly property bool oskFloating: state.oskFloating === true
    readonly property bool oskExtra: state.oskExtra === true
    readonly property string oskTouch: state.oskTouch
    readonly property string nightShiftMode: state.nightShiftMode
    readonly property int nightShiftTemperature: state.nightShiftTemperature
    readonly property real nightShiftOverrideUntil: state.nightShiftOverrideUntil
    readonly property bool nightShiftOverrideValue: state.nightShiftOverrideValue === true
    function set(key, value) {
        if (state[key] === value)
            return;
        state[key] = value;
        file.writeAdapter();
    }
    FileView {
        id: file
        path: root.stateDir + "/session.json"
        // Read at once: a write before the first read would save the defaults over the saved values.
        blockLoading: true
        // Only the shell writes this file: watching it made the echo of one write undo the next.
        atomicWrites: true
        printErrors: false
        adapter: JsonAdapter {
            id: state
            property bool keepAwake: false
            property bool quiet: false
            property bool rotationLock: false
            property bool oskFloating: false
            property bool oskExtra: false
            property string oskTouch: ""
            property string nightShiftMode: "off"
            property int nightShiftTemperature: 0
            property real nightShiftOverrideUntil: 0
            property bool nightShiftOverrideValue: false
        }
    }
}
