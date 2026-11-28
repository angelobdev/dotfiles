pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import ".."
import "../components"
import "../services"

// The global menu: its options and its apps (opened when the globalMenu widget comes onto a bar, by a right click on
// it, from its menu in the edit mode, and by desktop-shell toggle globalmenu). The options are saved at once; the
// installed Electron apps each have a switch to start under X11, where they hand their menu to the bar, and Apply
// writes that choice (globalmenu.py choose) and their launchers; an app already open keeps running as it is until
// it is restarted.
Overlay {
    id: root
    panelName: "globalmenu"
    dialog: true
    property var apps: []
    property var picked: ({})
    property bool loaded: false
    property bool applied: false
    readonly property bool changed: apps.some(app => !!picked[app.id] !== app.chosen)
    onOpened: {
        loaded = false;
        applied = false;
        lister.running = true;
    }
    function toggle(id) {
        const next = Object.assign({}, picked);
        next[id] = !next[id];
        picked = next;
    }
    function apply() {
        chooser.command = ["python3", GlobalMenu.helper, "choose"].concat(apps.filter(app => picked[app.id]).map(app => app.id));
        chooser.running = true;
    }
    Process {
        id: lister
        command: ["python3", GlobalMenu.helper, "apps"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.apps = JSON.parse(text).apps ?? [];
                } catch (failure) {
                    root.apps = [];
                }
                const next = {};
                for (const app of root.apps)
                    next[app.id] = app.chosen;
                root.picked = next;
                root.loaded = true;
            }
        }
    }
    Process {
        id: chooser
        onExited: (code, status) => {
            root.applied = code === 0;
            lister.running = true;
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(Theme.dialogNarrow, parent.width - 48)
        height: Math.min(layout.implicitHeight + 2 * Theme.dialogPadding, parent.height - Theme.panelClearance)
        ColumnLayout {
            id: layout
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 12
            PanelHeader {
                Layout.fillWidth: true
                title: I18n.tr("globalMenu.title")
            }
            Text {
                Layout.fillWidth: true
                text: I18n.tr("globalMenu.intro")
                wrapMode: Text.WordWrap
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
            }
            // The options of the widget, saved in shell.json at once (Config.globalMenu*).
            Heading {
                text: I18n.tr("globalMenu.focus")
                section: true
            }
            ChoiceChips {
                options: [["system", "globalMenu.focusSystem"], ["hover", "globalMenu.focusHover"], ["click", "globalMenu.focusClick"], ["off", "globalMenu.focusOff"]].map(option => ({
                            name: option[0],
                            label: I18n.tr(option[1])
                        }))
                current: Config.globalMenuFocus
                onChosen: name => Config.set("globalMenuFocus", name, "system")
            }
            Text {
                Layout.fillWidth: true
                text: I18n.tr("globalMenu.focusHint")
                wrapMode: Text.WordWrap
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
            Heading {
                text: I18n.tr("globalMenu.fallback")
                section: true
            }
            ChoiceChips {
                options: [
                    {
                        name: "generic",
                        label: I18n.tr("globalMenu.fallbackGeneric")
                    },
                    {
                        name: "nothing",
                        label: I18n.tr("globalMenu.fallbackNothing")
                    }
                ]
                current: Config.globalMenuFallback
                onChosen: name => Config.set("globalMenuFallback", name, "generic")
            }
            Heading {
                text: I18n.tr("globalMenu.icon")
                section: true
            }
            ChoiceChips {
                options: [
                    {
                        name: "shown",
                        label: I18n.tr("globalMenu.iconShown")
                    },
                    {
                        name: "hidden",
                        label: I18n.tr("globalMenu.iconHidden")
                    }
                ]
                current: Config.globalMenuIcon ? "shown" : "hidden"
                onChosen: name => Config.set("globalMenuIcon", name === "shown", true)
            }
            Heading {
                text: I18n.tr("globalMenu.x11Apps")
                section: true
            }
            Text {
                Layout.fillWidth: true
                text: I18n.tr("globalMenu.accessibility")
                wrapMode: Text.WordWrap
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(11)
            }
            Repeater {
                model: root.apps
                RowLayout {
                    id: appRow
                    required property var modelData
                    Layout.fillWidth: true
                    spacing: 10
                    Text {
                        Layout.fillWidth: true
                        text: appRow.modelData.name
                        elide: Text.ElideRight
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(14)
                    }
                    ControlSwitch {
                        checked: !!root.picked[appRow.modelData.id]
                        onToggled: root.toggle(appRow.modelData.id)
                    }
                }
            }
            Text {
                visible: root.loaded && root.apps.length === 0
                Layout.fillWidth: true
                text: I18n.tr("globalMenu.noApps")
                wrapMode: Text.WordWrap
                color: Theme.muted
                font.family: Theme.font
            }
            Text {
                visible: root.applied
                Layout.fillWidth: true
                text: I18n.tr("globalMenu.restartApps")
                wrapMode: Text.WordWrap
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
            }
            RowLayout {
                Layout.fillWidth: true
                Item {
                    Layout.fillWidth: true
                }
                ActionButton {
                    outlined: true
                    text: I18n.tr("common.close")
                    onClicked: ShellState.close()
                }
                ActionButton {
                    outlined: true
                    text: I18n.tr("globalMenu.apply")
                    enabled: root.changed && !chooser.running
                    onClicked: root.apply()
                }
            }
        }
    }
}
