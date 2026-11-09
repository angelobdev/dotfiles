import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import "../.."
import "../../components"
import "../../services"

// Settings → System → Plugins: the bundle's state (plugins.py status), each plugin, the last rebuild with its log,
// and the build cache. Rebuild runs plugins.py rebuild in the background (services/Plugins.qml): one pkexec prompt,
// and only plugins that are not loaded are replaced.
ColumnLayout {
    id: root
    // On screen: the state is read again each time it shows.
    property bool shown: false
    property bool confirmClear: false
    readonly property var status: Plugins.status
    readonly property var plugins: Array.isArray(status.plugins) ? status.plugins : []
    readonly property var entries: Array.isArray(status.cache?.entries) ? status.cache.entries : []
    readonly property real usedBytes: entries.filter(entry => entry.current).reduce((sum, entry) => sum + (entry.bytes ?? 0), 0)
    readonly property real oldBytes: entries.filter(entry => !entry.current).reduce((sum, entry) => sum + (entry.bytes ?? 0), 0)
    readonly property var last: status.rebuild ?? ({})
    readonly property var log: Array.isArray(last.log) ? last.log : []
    readonly property bool anyLoaded: plugins.some(plugin => plugin.loaded)
    // A rebuild has something to do, and install-hypr-plugins.py can do it now: nothing of an older build is loaded.
    readonly property bool needed: ["incomplete", "packaging", "compositor"].includes(status.state) || plugins.some(plugin => plugin.selected && !plugin.loaded)
    readonly property bool atLogin: ["packaging", "compositor"].includes(status.state) && anyLoaded
    // bundle.status() → its words.
    readonly property var stateKeys: ({
            current: "settings.plugins.state.current",
            missing: "settings.plugins.state.missing",
            incomplete: "settings.plugins.state.incomplete",
            packaging: "settings.plugins.state.packaging",
            compositor: "settings.plugins.state.compositor",
            unverified: "settings.plugins.state.unverified",
            mismatched: "settings.plugins.state.mismatched"
        })
    spacing: 10
    onShownChanged: if (shown) {
        confirmClear = false;
        Plugins.refresh();
    }
    Component.onCompleted: if (shown)
        Plugins.refresh()
    // While a rebuild runs on screen: its log grows, read it again now and then.
    Timer {
        interval: 3000
        repeat: true
        running: root.shown && Plugins.running
        onTriggered: Plugins.refresh()
    }
    function size(bytes) {
        if (bytes >= 1e9)
            return (bytes / 1e9).toLocaleString(I18n.locale, "f", 1) + " GB";
        return (bytes / 1e6).toLocaleString(I18n.locale, "f", bytes >= 1e7 ? 0 : 1) + " MB";
    }
    function when(seconds) {
        return new Date(seconds * 1000).toLocaleString(I18n.locale, Locale.ShortFormat);
    }
    function pluginState(plugin) {
        if (!plugin.selected)
            return I18n.tr("settings.plugins.notSelected", [plugin.profile]);
        if (plugin.loaded)
            return I18n.tr("settings.plugins.loaded");
        return I18n.tr(plugin.built ? "settings.plugins.built" : "settings.plugins.notBuilt");
    }
    function lastText() {
        if (Plugins.running || last.finished === undefined)
            return last.status === -1 ? I18n.tr("settings.plugins.lastStopped") : "";
        if (last.status === 0)
            return I18n.tr("settings.plugins.lastDone", [when(last.finished)]);
        if (last.status === -1)
            return I18n.tr("settings.plugins.lastStopped");
        return I18n.tr("settings.plugins.lastFailed", [when(last.finished), last.status]);
    }
    component Line: Text {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        textFormat: Text.PlainText
        color: Theme.text
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
    ScrollView {
        Layout.fillWidth: true
        Layout.fillHeight: true
        contentWidth: availableWidth
        clip: true
        ColumnLayout {
            width: parent.width
            spacing: 10
            Line {
                text: I18n.tr("settings.plugins.intro")
            }
            Line {
                visible: Plugins.error !== ""
                text: Plugins.error
                color: Theme.danger
            }
            // The bundle and the plugins in it.
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: bundleRows.implicitHeight + 24
                radius: Theme.corner(12)
                color: Theme.tile
                visible: root.status.state !== undefined
                ColumnLayout {
                    id: bundleRows
                    anchors {
                        left: parent.left
                        right: parent.right
                        top: parent.top
                        margins: 12
                        leftMargin: 14
                        rightMargin: 14
                    }
                    spacing: 10
                    Line {
                        text: root.stateKeys[root.status.state] ? I18n.tr(root.stateKeys[root.status.state]) : ""
                        font.weight: Font.DemiBold
                        font.pixelSize: Theme.textSize(13)
                        color: root.status.state === "current" ? Theme.text : Theme.danger
                    }
                    Line {
                        text: I18n.tr("settings.plugins.hyprland", [root.status.hyprland || "—", (root.status.verified ?? []).join(", ")])
                        color: Theme.muted
                        font.pixelSize: Theme.textSize(11)
                    }
                    Line {
                        visible: root.atLogin
                        text: I18n.tr("settings.plugins.atLogin")
                    }
                    Repeater {
                        model: root.plugins
                        RowLayout {
                            id: pluginRow
                            required property var modelData
                            Layout.fillWidth: true
                            spacing: 12
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Line {
                                    text: pluginRow.modelData.name + " · " + I18n.tr("settings.plugins.profile", [pluginRow.modelData.profile])
                                    font.pixelSize: Theme.textSize(13)
                                    font.weight: Font.DemiBold
                                }
                                Line {
                                    text: pluginRow.modelData.repo + " @ " + String(pluginRow.modelData.revision).slice(0, 7)
                                    color: Theme.muted
                                    font.pixelSize: Theme.textSize(11)
                                }
                            }
                            Text {
                                text: root.pluginState(pluginRow.modelData)
                                textFormat: Text.PlainText
                                color: pluginRow.modelData.loaded ? Theme.text : Theme.muted
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(12)
                            }
                        }
                    }
                }
            }
            // The rebuild: its button, the last result and its log.
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                ActionButton {
                    text: Plugins.running ? I18n.tr("settings.plugins.rebuilding") : I18n.tr("settings.plugins.rebuild")
                    enabled: !Plugins.running && !Plugins.cleaning && root.needed && !root.atLogin && !["unverified", "mismatched"].includes(root.status.state)
                    onClicked: Plugins.startRebuild()
                }
                Line {
                    text: root.lastText()
                    color: root.last.status === 0 || Plugins.running ? Theme.muted : Theme.danger
                }
            }
            Line {
                visible: root.log.length > 0
                text: I18n.tr("settings.plugins.log")
                color: Theme.muted
                font.pixelSize: Theme.textSize(11)
            }
            Rectangle {
                Layout.fillWidth: true
                visible: root.log.length > 0
                implicitHeight: logText.implicitHeight + 20
                radius: Theme.corner(10)
                color: Theme.tile
                Text {
                    id: logText
                    anchors {
                        left: parent.left
                        right: parent.right
                        top: parent.top
                        margins: 10
                    }
                    text: root.log.join("\n")
                    textFormat: Text.PlainText
                    wrapMode: Text.WrapAnywhere
                    color: Theme.text
                    font.family: "monospace"
                    font.pixelSize: Theme.textSize(11)
                }
            }
            // The build cache.
            Line {
                text: I18n.tr("settings.plugins.cache") + " · " + root.size(root.status.cache?.bytes ?? 0)
                font.weight: Font.DemiBold
                font.pixelSize: Theme.textSize(13)
            }
            Line {
                text: I18n.tr("settings.plugins.cacheHint", [root.size(root.usedBytes), root.size(root.oldBytes)])
                color: Theme.muted
            }
            // Two steps for all of it: the first press asks, the second removes.
            RowLayout {
                spacing: 8
                ActionButton {
                    text: I18n.tr("settings.plugins.clearOld")
                    enabled: root.oldBytes > 0 && !Plugins.running && !Plugins.cleaning
                    onClicked: Plugins.clearCache("old")
                }
                ActionButton {
                    destructive: root.confirmClear
                    enabled: (root.status.cache?.bytes ?? 0) > 0 && !Plugins.running && !Plugins.cleaning
                    text: root.confirmClear ? I18n.tr("settings.plugins.clearAllConfirm") : I18n.tr("settings.plugins.clearAll")
                    onClicked: {
                        if (!root.confirmClear) {
                            root.confirmClear = true;
                            return;
                        }
                        Plugins.clearCache("all");
                        root.confirmClear = false;
                    }
                }
                ActionButton {
                    visible: root.confirmClear
                    text: I18n.tr("common.cancel")
                    onClicked: root.confirmClear = false
                }
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        ActionButton {
            text: I18n.tr("settings.system.checkAgain")
            enabled: !Plugins.reading
            onClicked: Plugins.refresh()
        }
    }
}
