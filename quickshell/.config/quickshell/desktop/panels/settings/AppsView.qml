import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import "../.."
import "../../components"
import "../../services/BindKeys.js" as BindKeys

// Settings → Apps: the app each shortcut opens (desktop-app, apps.py): the terminal (Super + Return), the browser
// (Super + Shift + Return), the password manager (Super + Shift + Space) and the file manager (Super + Shift + F).
// Each is one of the installed apps of its kind, the default, or a command typed by hand; kept under "defaultApps"
// in shell.json and read at every press, so a change applies at once.
ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 6
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/apps.py"
    readonly property var roles: [
        {
            name: "terminal",
            modifiers: ["super"],
            key: "Return"
        },
        {
            name: "browser",
            modifiers: ["super", "shift"],
            key: "Return"
        },
        {
            name: "passwords",
            modifiers: ["super", "shift"],
            key: "space"
        },
        {
            name: "files",
            modifiers: ["super", "shift"],
            key: "F"
        }
    ]
    // The keys as Hints names them.
    function keys(role) {
        const names = {
            super: I18n.tr("hints.keys.super"),
            shift: I18n.tr("hints.keys.shift")
        };
        return role.modifiers.map(modifier => names[modifier]).concat([BindKeys.keyName(role.key, (key, args) => I18n.tr(key, args))]).join(" + ");
    }
    function title(role) {
        return ({
                terminal: I18n.tr("apps.roles.terminalTitle"),
                browser: I18n.tr("apps.roles.browserTitle"),
                passwords: I18n.tr("apps.roles.passwordsTitle"),
                files: I18n.tr("apps.roles.filesTitle")
            })[role] ?? role;
    }
    // Per role, as apps.py list gives it: {choice, default, resolved, apps: [{id, name}], names}.
    property var listing: ({})
    readonly property var chosen: (Config.user.defaultApps && typeof Config.user.defaultApps === "object" && !Array.isArray(Config.user.defaultApps)) ? Config.user.defaultApps : ({})
    // The value a role had before "Other command" was picked for it, until a command is typed.
    property var typing: ({})
    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function set(role, value) {
        const next = Object.assign({}, chosen);
        if (value === "" || value === listing[role]?.default)
            delete next[role];
        else
            next[role] = value;
        Config.set("defaultApps", next, {});
        refresh();
    }
    function label(role, id) {
        const entry = listing[role];
        // The one default that is a command: Quick Access of 1Password.
        if (id !== "" && id === entry?.default && !id.endsWith(".desktop"))
            return role === "passwords" ? I18n.tr("apps.roles.passwordsDefault") : id;
        return entry?.names?.[id] ?? entry?.apps?.find(app => app.id === id)?.name ?? id.replace(/\.desktop$/, "");
    }
    // A desktop entry it does not find is not installed.
    function installed(role, id) {
        const entry = listing[role];
        return !id.endsWith(".desktop") || entry?.names?.[id] !== undefined || (entry?.apps ?? []).some(app => app.id === id);
    }
    function options(role) {
        const entry = listing[role] ?? {};
        const list = [
            {
                name: "",
                label: I18n.tr(installed(role, entry.default ?? "") ? "apps.default" : "apps.defaultMissing", [label(role, entry.default ?? "")])
            }
        ];
        for (const app of entry.apps ?? [])
            if (app.id !== entry.default)
                list.push({
                    name: app.id,
                    label: app.name
                });
        list.push({
            name: "command",
            label: I18n.tr("apps.otherCommand")
        });
        return list;
    }
    // What the drop-down shows: the default, an installed app, or "Other command" for anything else.
    function current(role) {
        if (typing[role])
            return "command";
        const value = chosen[role] ?? "";
        if (value === "" || value === listing[role]?.default)
            return "";
        return (listing[role]?.apps ?? []).some(app => app.id === value) ? value : "command";
    }
    Component.onCompleted: refresh()
    Process {
        id: reader
        command: ["python3", root.helper, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.listing = JSON.parse(text);
                } catch (failure) {
                    root.listing = {};
                }
            }
        }
    }
    Text {
        text: I18n.tr("apps.group")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        font.weight: Font.DemiBold
    }
    GroupCard {
        Layout.fillWidth: true
        verticalPadding: 10
        spacing: 12
        Repeater {
            model: root.roles
            ColumnLayout {
                id: row
                required property var modelData
                readonly property string role: modelData.name
                readonly property var entry: root.listing[role] ?? {}
                readonly property bool commandShown: root.current(role) === "command"
                Layout.fillWidth: true
                spacing: 6
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: root.title(row.role)
                            color: Theme.text
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(13)
                        }
                        Text {
                            Layout.fillWidth: true
                            // The app a press opens now: the choice, or what stands in for it when it is missing.
                            text: row.entry.resolved === undefined ? root.keys(row.modelData) : row.entry.resolved === "" ? I18n.tr("apps.none", [root.keys(row.modelData)]) : I18n.tr("apps.opens", [root.keys(row.modelData), root.label(row.role, row.entry.resolved)])
                            wrapMode: Text.WordWrap
                            textFormat: Text.PlainText
                            color: row.entry.resolved === "" ? Theme.danger : Theme.muted
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                        }
                    }
                    ChoiceCombo {
                        options: root.options(row.role)
                        current: root.current(row.role)
                        Accessible.name: root.title(row.role)
                        onChosen: name => {
                            if (name === "command") {
                                root.typing = Object.assign({}, root.typing, {
                                    [row.role]: true
                                });
                                commandField.forceActiveFocus();
                                return;
                            }
                            root.typing = Object.assign({}, root.typing, {
                                [row.role]: false
                            });
                            root.set(row.role, name);
                        }
                    }
                }
                InputField {
                    id: commandField
                    Layout.fillWidth: true
                    visible: row.commandShown
                    text: row.commandShown && !(root.chosen[row.role] ?? "").endsWith(".desktop") ? (root.chosen[row.role] ?? "") : ""
                    placeholderText: I18n.tr("apps.commandPlaceholder")
                    Accessible.name: I18n.tr("apps.otherCommand")
                    onEditingFinished: if (text.trim() !== "") {
                        root.typing = Object.assign({}, root.typing, {
                            [row.role]: false
                        });
                        root.set(row.role, text.trim());
                    }
                }
            }
        }
    }
    Text {
        Layout.fillWidth: true
        text: I18n.tr("apps.hint")
        wrapMode: Text.WordWrap
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
}
