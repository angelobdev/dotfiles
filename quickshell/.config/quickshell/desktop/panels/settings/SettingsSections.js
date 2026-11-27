.pragma library

// The sections of Settings, in sidebar order, each under a group label (settings.sidebar.<group>): its name, glyph,
// catalog key and, for one that needs a profile, its unit (services/Installed.qml). Read by panels/SettingsPanel.qml
// and by the commands of the launcher (services/Commands.qml), which search the same index as the Settings sidebar.
var sections = [
    {
        name: "network",
        icon: "wifi",
        labelKey: "settings.sections.network",
        group: "connections"
    },
    {
        name: "bluetooth",
        icon: "bluetooth",
        labelKey: "settings.sections.bluetooth",
        group: "connections"
    },
    {
        name: "displays",
        icon: "monitor",
        labelKey: "settings.sections.displays",
        group: "devices"
    },
    {
        name: "sound",
        icon: "volume-high",
        labelKey: "settings.sections.sound",
        group: "devices"
    },
    {
        name: "power",
        icon: "battery-75",
        labelKey: "settings.sections.power",
        group: "devices"
    },
    {
        name: "appearance",
        icon: "palette",
        labelKey: "settings.sections.appearance",
        group: "personalization"
    },
    {
        name: "desktop",
        icon: "apps",
        labelKey: "settings.sections.desktop",
        group: "personalization"
    },
    {
        name: "apps",
        icon: "window",
        labelKey: "settings.sections.apps",
        group: "personalization"
    },
    {
        name: "assistant",
        icon: "assistant",
        labelKey: "settings.sections.assistant",
        group: "personalization",
        // Only with the AI Assistant profile installed (services/Installed.qml).
        unit: "assistant"
    },
    {
        name: "keyboard",
        icon: "keyboard",
        labelKey: "settings.sections.keyboard",
        group: "input"
    },
    {
        name: "tablet",
        icon: "rotate",
        labelKey: "settings.sections.tablet",
        group: "input"
    },
    {
        name: "privacy",
        icon: "eye-off",
        labelKey: "settings.sections.privacy",
        group: "system"
    },
    {
        name: "system",
        icon: "controls",
        labelKey: "settings.sections.system",
        group: "system"
    }
]
