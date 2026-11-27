.pragma library

// Every widget the bar can hold, in the order the gallery lists them: its file in this folder, the glyph the
// gallery and the edit menu show, and whether it may appear more than once. Its name and description are
// bar.widgets.<id>.name and .description in the catalogs.
var widgets = [
    {
        id: "launcher",
        source: "LauncherWidget.qml",
        glyph: "apps"
    },
    {
        id: "workspaces",
        source: "WorkspacesWidget.qml",
        glyph: "overview"
    },
    {
        id: "title",
        source: "TitleWidget.qml",
        glyph: "window"
    },
    {
        id: "tray",
        source: "TrayWidget.qml",
        glyph: "dock"
    },
    {
        id: "media",
        source: "MediaWidget.qml",
        glyph: "play"
    },
    {
        id: "privacy",
        source: "PrivacyWidget.qml",
        glyph: "microphone"
    },
    {
        id: "recording",
        source: "RecordingWidget.qml",
        glyph: "record"
    },
    {
        id: "reminders",
        source: "RemindersWidget.qml",
        glyph: "clock"
    },
    {
        id: "battery",
        source: "BatteryWidget.qml",
        glyph: "battery-75"
    },
    {
        id: "updates",
        source: "UpdatesWidget.qml",
        glyph: "update"
    },
    {
        id: "assistant",
        source: "AssistantWidget.qml",
        glyph: "assistant"
    },
    {
        id: "hints",
        source: "HintsWidget.qml",
        glyph: "keyboard"
    },
    {
        id: "notifications",
        source: "NotificationsWidget.qml",
        glyph: "bell"
    },
    {
        id: "controls",
        source: "ControlsWidget.qml",
        glyph: "controls"
    },
    {
        id: "clock",
        source: "ClockWidget.qml",
        glyph: "clock"
    },
    {
        id: "power",
        source: "PowerWidget.qml",
        glyph: "power"
    },
    {
        id: "weather",
        source: "WeatherWidget.qml",
        glyph: "cloud-sun"
    },
    {
        id: "volume",
        source: "VolumeWidget.qml",
        glyph: "volume-high"
    },
    {
        id: "network",
        source: "NetworkWidget.qml",
        glyph: "wifi"
    },
    {
        id: "keyboardLayout",
        source: "KeyboardLayoutWidget.qml",
        glyph: "keyboard"
    },
    {
        id: "separator",
        source: "SeparatorWidget.qml",
        glyph: "split",
        repeats: true
    },
    {
        id: "spacer",
        source: "SpacerWidget.qml",
        glyph: "fullscreen",
        repeats: true
    }
];

var ids = widgets.map(widget => widget.id);

function find(id) {
    return widgets.find(widget => widget.id === id) ?? null;
}

function known(id) {
    return find(id) !== null;
}

function repeats(id) {
    return find(id)?.repeats === true;
}

// Catalog keys of a widget's name and description.
function nameKey(id) {
    return "bar.widgets." + id + ".name";
}

function descriptionKey(id) {
    return "bar.widgets." + id + ".description";
}
