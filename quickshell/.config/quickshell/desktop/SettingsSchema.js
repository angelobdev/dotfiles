.pragma library

// The shell options Settings shows (panels/settings/OptionsSection.qml), by section and group. Each names a
// property of Config.qml and carries the same default (scripts/tests/test_settings.py checks they agree),
// the control it gets and its limits. Labels are settings.options.<key> and settings.groups.<group> in the
// catalogs; settings.hints.<key> adds a line under the label when it exists (hint: true), and
// settings.placeholders.<key> is the text of an empty text field (placeholder: true).
// type: bool (switch), number (slider: min, max, step, unit), choice (options; labels from the assist
// catalog with assist: true), text, time (HH:MM).
// Options left out are lists and maps (dock pins, Control Center modules, DNS presets, assist pages…),
// still set in ~/.config/desktop/shell.json by hand.
const options = [
    // Desktop
    { key: "barMedia", section: "desktop", group: "bar", type: "bool", fallback: true },
    { key: "workspaceScroll", section: "desktop", group: "bar", type: "bool", fallback: true, hint: true },
    { key: "minimumWorkspaces", section: "desktop", group: "bar", type: "number", fallback: 2, min: 1, max: 10, step: 1 },
    { key: "dockEnabled", section: "desktop", group: "dock", type: "bool", fallback: true },
    { key: "dockIconSize", section: "desktop", group: "dock", type: "number", fallback: 44, min: 32, max: 64, step: 2, unit: "px" },
    { key: "dockMagnification", section: "desktop", group: "dock", type: "number", fallback: 1.4, min: 1, max: 2, step: 0.1, unit: "×", hint: true },
    { key: "dockRevealDelay", section: "desktop", group: "dock", type: "number", fallback: 120, min: 0, max: 1000, step: 20, unit: "ms" },
    { key: "dockTriggerHeight", section: "desktop", group: "dock", type: "number", fallback: 3, min: 1, max: 12, step: 1, unit: "px", hint: true },
    { key: "launcherFiles", section: "desktop", group: "launcher", type: "bool", fallback: true, hint: true },
    { key: "controlCenterWidth", section: "desktop", group: "controlCenter", type: "number", fallback: 400, min: 340, max: 560, step: 20, unit: "px" },
    { key: "expandMonitors", section: "desktop", group: "controlCenter", type: "bool", fallback: false },
    { key: "expandAudioDevices", section: "desktop", group: "controlCenter", type: "bool", fallback: false },
    { key: "osdEnabled", section: "desktop", group: "osd", type: "bool", fallback: true },
    { key: "osdTimeout", section: "desktop", group: "osd", type: "number", fallback: 1700, min: 500, max: 5000, step: 100, unit: "ms" },
    { key: "osdWidth", section: "desktop", group: "osd", type: "number", fallback: 320, min: 240, max: 480, step: 20, unit: "px" },
    { key: "osdBottomMargin", section: "desktop", group: "osd", type: "number", fallback: 96, min: 24, max: 240, step: 8, unit: "px" },
    { key: "focusMinutes", section: "desktop", group: "focus", type: "number", fallback: 25, min: 5, max: 120, step: 5, unit: "min" },
    { key: "nightShiftTemperature", section: "desktop", group: "nightShift", type: "number", fallback: 4000, min: 2500, max: 5500, step: 100, unit: "K" },
    { key: "nightShiftStart", section: "desktop", group: "nightShift", type: "time", fallback: "20:00" },
    { key: "nightShiftEnd", section: "desktop", group: "nightShift", type: "time", fallback: "07:00" },
    { key: "weatherEnabled", section: "desktop", group: "weather", type: "bool", fallback: true },
    { key: "weatherCity", section: "desktop", group: "weather", type: "text", fallback: "", hint: true, placeholder: true },
    { key: "reduceMotion", section: "desktop", group: "motion", type: "bool", fallback: false, hint: true },
    // Power
    { key: "batteryLow", section: "power", group: "battery", type: "number", fallback: 20, min: 5, max: 50, step: 1, unit: "%", hint: true },
    { key: "batteryCritical", section: "power", group: "battery", type: "number", fallback: 10, min: 2, max: 30, step: 1, unit: "%" },
    { key: "peripheralLow", section: "power", group: "battery", type: "number", fallback: 15, min: 5, max: 50, step: 1, unit: "%", hint: true },
    // Keyboard
    { key: "oskAutoShow", section: "keyboard", group: "osk", type: "bool", fallback: true, hint: true },
    { key: "oskPrediction", section: "keyboard", group: "osk", type: "bool", fallback: true, hint: true },
    { key: "oskLearning", section: "keyboard", group: "osk", type: "bool", fallback: true, hint: true },
    { key: "oskTouchStats", section: "keyboard", group: "osk", type: "bool", fallback: true, hint: true },
    // Tablet and touch
    { key: "touchScale", section: "tablet", group: "touch", type: "number", fallback: 1.25, min: 1, max: 1.6, step: 0.05, unit: "×", hint: true },
    { key: "assistLongPress", section: "tablet", group: "touch", type: "choice", fallback: "keyboard", assist: true,
      options: ["keyboard", "assistant", "launcher", "overview", "controls", "notifications", "window"] },
    // Privacy
    { key: "clipboardEnabled", section: "privacy", group: "clipboard", type: "bool", fallback: true, hint: true },
    { key: "clipboardMaxItems", section: "privacy", group: "clipboard", type: "number", fallback: 200, min: 20, max: 1000, step: 20 },
    { key: "launcherHistory", section: "privacy", group: "launcher", type: "bool", fallback: true, hint: true },
    { key: "recordingFramerate", section: "privacy", group: "recording", type: "choice", fallback: 30, options: [24, 30, 60], unit: "fps" }
];

// Catalog keys of an option's label and hint and of a group's title (test_settings.py checks they exist).
function labelKey(option) {
    return "settings.options." + option.key;
}
function hintKey(option) {
    return "settings.hints." + option.key;
}
function placeholderKey(option) {
    return "settings.placeholders." + option.key;
}
function groupKey(group) {
    return "settings.groups." + group;
}

function forSection(section) {
    return options.filter(option => option.section === section);
}

// The groups of a section in the order their first option comes.
function groups(section) {
    const names = [];
    for (const option of forSection(section)) {
        if (!names.includes(option.group))
            names.push(option.group);
    }
    return names.map(group => ({ name: group, options: forSection(section).filter(option => option.group === group) }));
}

// A slider value on its step, without float residue (1.4000000000000001).
function snap(option, value) {
    const decimals = (String(option.step).split(".")[1] || "").length;
    const stepped = Math.round((value - option.min) / option.step) * option.step + option.min;
    return Number(Math.max(option.min, Math.min(option.max, stepped)).toFixed(decimals));
}
