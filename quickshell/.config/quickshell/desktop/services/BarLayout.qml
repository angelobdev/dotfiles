pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import ".."
import "../bar/BarLayoutModel.js" as Model
import "../bar/widgets/Registry.js" as Registry

// Which widgets sit in which of the five sections of the bar (bar/BarLayoutModel.js), kept in shell.json as
// barLayout. The bar of one monitor is edited at a time, on a draft: finishing saves it, cancelling drops it.
// Holding Super over a bar edits it until Super is released (config/binds.lua sends the custom events);
// "latched" editing (the bar menu, desktop-shell bar edit, or opening the gallery) lasts until Done.
Singleton {
    id: root
    readonly property var saved: Model.normalize(Config.barLayout, Registry.known, Registry.repeats)
    property var draft: null
    property string editingScreen: ""
    property bool latched: false
    readonly property bool editing: editingScreen !== ""
    readonly property var current: draft ?? saved
    function layoutFor(screenName) {
        return screenName === editingScreen && draft ? draft : saved;
    }
    function available() {
        return Model.available(current, Registry.ids, Registry.repeats);
    }
    function isPreset(name) {
        return Model.equal(current, Model.presets[name]);
    }
    function begin(screenName, latch) {
        if (editing && editingScreen !== screenName)
            finish();
        if (!editing)
            draft = Model.copy(saved);
        editingScreen = screenName;
        latched = latched || latch;
    }
    function latch() {
        if (editing)
            latched = true;
    }
    function finish() {
        if (draft && !Model.equal(draft, saved))
            save(draft);
        clear();
    }
    function cancel() {
        clear();
    }
    function clear() {
        draft = null;
        editingScreen = "";
        latched = false;
    }
    function save(layout) {
        const placing = !holds(saved, "globalMenu") && holds(layout, "globalMenu");
        Config.set("barLayout", layout, Model.presets.classic);
        // The global menu just added by the user: its options and the apps to start under X11 (GlobalMenuPanel).
        if (placing)
            ShellState.open("globalmenu");
    }
    function holds(layout, id) {
        return Object.values(layout).some(ids => Array.isArray(ids) && ids.includes(id));
    }
    // Outside editing (the bar menu) a change is saved at once.
    function apply(layout) {
        if (draft)
            draft = layout;
        else
            save(layout);
    }
    function move(from, fromIndex, to, toIndex) {
        apply(Model.move(current, from, fromIndex, to, toIndex));
    }
    function add(id, section, index) {
        apply(Model.insert(current, id, section, index));
    }
    function removeAt(section, index) {
        apply(Model.removeAt(current, section, index));
    }
    function usePreset(name) {
        if (Model.presets[name])
            apply(Model.copy(Model.presets[name]));
    }
    // desktop-shell bar ACTION: edit (latched, on the focused monitor), done, cancel, reset.
    function request(action) {
        if (action === "edit")
            begin(Hyprland.focusedMonitor?.name ?? Quickshell.screens[0]?.name ?? "", true);
        else if (action === "done")
            finish();
        else if (action === "cancel")
            cancel();
        else if (action === "reset")
            usePreset("classic");
        else
            return false;
        return true;
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name !== "custom" || !event.data.startsWith("desktop-bar "))
                return;
            const words = event.data.split(" ");
            if (words[1] === "edit" && words[2])
                root.begin(words[2], false);
            else if (words[1] === "release" && !root.latched)
                root.finish();
            else if (words[1] === "cancel")
                root.cancel();
        }
    }
}
