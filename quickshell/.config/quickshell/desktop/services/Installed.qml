pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// What the installer installed: its units (profiles, and parts as profile.part), one per line in
// $XDG_STATE_HOME/dotfiles/units, which install-desktop.py writes with its record. What needs a unit shows only with
// it: has("plugins", "hyprspace") for the part plugins.hyprspace, has("assistant") for a profile. Hyprland reads the same file (hypr/config/installed.lua). Without
// it (an install from before it, or none by the installer), every unit counts as installed.
Singleton {
    id: root
    readonly property string path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/dotfiles/units"
    // null: no file, so everything.
    property var units: null
    // profile, and part for a part of it (profile.part).
    function has(profile, part) {
        return units === null || units.includes(part ? profile + "." + part : profile);
    }
    FileView {
        path: root.path
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: root.units = text().split("\n").map(line => line.trim()).filter(line => line !== "")
        onLoadFailed: root.units = null
    }
}
