pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Services.UPower
import ".."
import "CommandModel.js" as Model
import "BindKeys.js" as BindKeys
import "../panels/settings/SettingsSearch.js" as SettingsSearch
import "../panels/settings/SettingsSections.js" as SettingsSections

// The commands of the launcher (">", Super + Alt + Space, desktop-shell commands): the tree of commands.json (beside
// shell.qml) read through CommandModel.js, the states its conditions name, the rows of the provider categories,
// and running a command. Nothing here starts a process to check a condition: each state is a property of a service.
Singleton {
    id: root
    // The commands of the desktop and those of the user (~/.config/desktop/commands.json), laid over them by id.
    property var shipped: ({})
    property var own: ({})
    readonly property var model: Model.parse(Model.merge(shipped, own))
    // "requires:NAME" for each program a command requires that is installed (checked when the commands change).
    property var programs: ({})
    onModelChanged: requireCheck.check()
    // The states the conditions of commands.json name ("when", "enabled", "state").
    readonly property var facts: Object.assign({
            keepAwake: Idle.keepAwake,
            quiet: Notices.quiet,
            focus: Focus.active,
            nightShift: NightShift.active,
            nightShiftAvailable: NightShift.available,
            bar: !BarVisibility.userHidden,
            zoom: Zoom.factor > 1,
            rotation: Tablet.available,
            rotationLock: Tablet.locked,
            touchscreen: Tablet.touchscreen,
            onScreenKeyboard: Keyboard.shown,
            battery: Battery.present,
            efi: efiCheck.found,
            powerProfiles: true,
            numberedWorkspace: (Hyprland.focusedWorkspace?.id ?? 0) > 0,
            restartNeeded: Updates.restartNeeded,
            assistant: Installed.has("assistant"),
            radio: Installed.has("radio")
        }, programs)
    // The calls a command can make ("call": [name, argument]): the services the IPC of shell.qml reaches.
    readonly property var calls: ({
            keepAwake: action => Idle.request(action),
            quiet: action => Notices.request(action),
            focus: action => Focus.request(action, 0),
            nightShift: action => NightShift.request(action),
            bar: action => BarVisibility.request(action) || BarLayout.request(action),
            zoom: action => Zoom.request(action),
            rotationLock: action => Tablet.requestLock(action),
            keyboard: action => Keyboard.request(action)
        })

    // The keys of each Hyprland bind by its description (as config/binds.lua writes it, the English text Hints
    // translates): a list of keycap labels, "Super", "Ctrl", "L". A command names its bind with "bind".
    property var shortcuts: ({})
    // The described binds in the order of the Hyprland config, for the Shortcuts category.
    property var bindNames: []
    function keysOf(entry) {
        return entry && entry.bind ? shortcuts[entry.bind] ?? [] : [];
    }
    // Binds that make no sense run from the launcher: the launcher itself, and the window switcher, which needs Alt
    // held.
    readonly property var unlisted: ["Applications", "Switch windows", "Switch windows backwards"]
    // The Shortcuts category: every described bind that no command of commands.json already stands for.
    readonly property var shortcutRows: {
        const linked = {};
        for (const id of model.order)
            if (model.items[id].bind)
                linked[model.items[id].bind] = true;
        return bindNames.filter(name => !linked[name] && !unlisted.includes(name)).map(name => ({
                    name: name,
                    label: I18n.bindDescription(name)
                }));
    }
    // The Settings category: the index of the Settings search (its sections, tabs and options), in the language shown.
    readonly property var settingsIndex: SettingsSearch.entries(key => I18n.tr(key), SettingsSections.sections.filter(section => !section.unit || Installed.has(section.unit)))
    // Modifiers first, in the order of Hints.
    function keycaps(bind) {
        const caps = [];
        for (const [mask, key] of [[64, "hints.keys.super"], [4, "hints.keys.ctrl"], [1, "hints.keys.shift"], [8, "hints.keys.alt"], [128, "hints.keys.altgr"]])
            if ((bind.modmask & mask) !== 0)
                caps.push(I18n.tr(key));
        caps.push(BindKeys.keyName(bind.key, (key, args) => I18n.tr(key, args)));
        return caps;
    }
    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (event.name === "configreloaded")
                bindReader.running = true;
        }
    }
    Connections {
        target: I18n
        function onLanguageChanged() {
            bindReader.running = true;
        }
    }
    Process {
        id: bindReader
        running: true
        command: ["hyprctl", "-j", "binds"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const found = {};
                    const names = [];
                    // A key with a modifier wins over a bare one (Super + Shift + S over Print), the first over later ones.
                    for (const bind of JSON.parse(text)) {
                        if (!bind.description || bind.submap || bind.release || !bind.key || bind.key.startsWith("switch:") || bind.key.startsWith("mouse:"))
                            continue;
                        const before = found[bind.description];
                        if (!before)
                            names.push(bind.description);
                        if (!before || before.modmask === 0 && bind.modmask !== 0)
                            found[bind.description] = bind;
                    }
                    const result = {};
                    for (const name in found)
                        result[name] = root.keycaps(found[name]);
                    root.shortcuts = result;
                    root.bindNames = names;
                } catch (failure) {
                    root.shortcuts = {};
                    root.bindNames = [];
                }
            }
        }
    }
    function label(entry) {
        if (!entry)
            return "";
        return entry.row || entry.literal ? entry.label : I18n.tr(entry.label);
    }
    function entriesOf(parent) {
        return Model.children(model, parent, facts);
    }
    function find(id) {
        return model.items[id] ?? null;
    }
    // The entry Alt puts in its place.
    function variant(entry, alt) {
        return entry && !entry.row ? Model.variant(model, entry, facts, alt) : entry;
    }
    function switchState(entry) {
        return entry && !entry.row ? Model.switchState(entry, facts) : "";
    }
    function enabled(entry) {
        return !entry || entry.row || Model.enabled(entry, facts);
    }
    function opens(entry) {
        return !!entry && !entry.row && Model.opens(entry);
    }
    // The labels of the categories above an entry, for a search result.
    function path(entry) {
        return Model.above(model, entry).map(id => label(model.items[id])).join(" › ");
    }
    // The commands matching the query under a category, the rows of every provider category included, each with
    // its LauncherRank tier ({entry, tier}).
    function matches(query, under) {
        const rowsOf = {};
        for (const id of model.order) {
            const entry = model.items[id];
            if (Model.hasRows(entry) && (under === "" || id === under || id.startsWith(under + ".")))
                rowsOf[id] = rows(entry);
        }
        return Model.matches(model, query, facts, label, under, rowsOf);
    }

    // Rows that run something and close the launcher, rather than choices it stays open on.
    readonly property var actionRows: ["shortcuts", "settings"]
    // The rows of a provider category, as entries: {id, parent, label, current, row, value}; a shortcut also has its
    // bind (keysOf), a setting its path as words to find it by (terms).
    function rows(category) {
        const make = (value, text, current, extra) => Object.assign({
                    id: category.id + "." + String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-"),
                    parent: category.id,
                    label: text,
                    icon: category.icon,
                    current: current,
                    row: category.rows,
                    value: value
                }, extra ?? {});
        switch (category.rows) {
        case "themes":
            return Theming.themeItems.filter(theme => !(theme.dynamic && !Theming.dynamic.available)).map(theme => make(theme.id, theme.dynamic ? I18n.tr("theming.dynamic") : theme.name, theme.id === Theming.current));
        case "barStyles":
            return [["shade", "theming.barShaded"], ["floating", "theming.barFloating"], ["pills", "theming.barPills"], ["transparent", "theming.barTransparent"]].map(style => make(style[0], I18n.tr(style[1]), Theme.barStyle === style[0]));
        case "workspaceLayouts":
            {
                const mode = layoutsFile.modes[String(Hyprland.focusedWorkspace?.id ?? "")] ?? "dwindle";
                return [["dwindle", "workspaces.layouts.dwindle"], ["scrolling", "workspaces.layouts.scrolling"], ["floating", "workspaces.layouts.floating"]].map(layout => make(layout[0], I18n.tr(layout[1]), mode === layout[0]));
            }
        case "powerProfiles":
            return [[PowerProfile.PowerSaver, "battery.profiles.powerSaver"], [PowerProfile.Balanced, "battery.profiles.balanced"], [PowerProfile.Performance, "battery.profiles.performance"]].filter(profile => profile[0] !== PowerProfile.Performance || PowerProfiles.hasPerformanceProfile).map(profile => make(profile[0], I18n.tr(profile[1]), PowerProfiles.profile === profile[0]));
        case "audioOutputs":
            return Audio.outputs.map(node => make(node.name, Audio.deviceName(node), node === Audio.sink));
        case "shortcuts":
            return shortcutRows.map(shortcut => make(shortcut.name, shortcut.label, false, {
                        bind: shortcut.name
                    }));
        case "settings":
            return settingsIndex.map(entry => make(entry.id, entry.path.join(" › "), false, {
                        setting: entry,
                        terms: entry.fields.text
                    }));
        }
        return [];
    }
    // A provider category is about to show: what it lists is read if it was not yet.
    function prepare(category) {
        if (category?.rows === "themes" && Theming.themes.length === 0)
            Theming.query(["listing"]);
    }
    function select(row) {
        switch (row.row) {
        case "themes":
            Theming.setTheme(row.value);
            break;
        case "barStyles":
            Theming.setBarStyle(row.value);
            break;
        case "workspaceLayouts":
            Quickshell.execDetached(["hyprctl", "eval", "if desktop_workspace_layout_set then desktop_workspace_layout_set(\"" + row.value + "\") end"]);
            break;
        case "powerProfiles":
            PowerProfiles.profile = row.value;
            break;
        case "audioOutputs":
            {
                const node = Audio.outputs.find(output => output.name === row.value);
                if (node)
                    Audio.selectOutput(node);
                break;
            }
        case "shortcuts":
            // The launcher goes first: a window shortcut acts on the window below it.
            ShellState.close();
            Quickshell.execDetached(["hyprctl", "eval", "if desktop_run_bind then desktop_run_bind(" + JSON.stringify(row.value) + ") end"]);
            break;
        case "settings":
            {
                // Settings opens on the section and tab, the option scrolled to and selected (SettingsPanel).
                const setting = row.setting;
                ShellState.remember("settings/reveal", setting.key);
                ShellState.openSection("settings", setting.tab !== "" ? setting.section + "/" + setting.tab : setting.section, null, false);
                break;
            }
        }
    }

    // Runs a command or picks a row. The launcher stays open after a switch or a row, to change more than one;
    // otherwise the command closes it, or opens its panel in its place. True when it stays.
    function run(entry) {
        if (!entry || !enabled(entry))
            return true;
        if (entry.row) {
            select(entry);
            return !actionRows.includes(entry.row);
        }
        if (Model.opens(entry))
            return true;
        const stays = entry.state !== undefined;
        if (entry.panel !== undefined) {
            ShellState.close();
            ShellState.toggle(entry.panel);
        } else if (entry.settings !== undefined) {
            ShellState.openSection("settings", entry.settings, null, false);
        } else if (entry.session !== undefined) {
            session(entry.session);
        } else {
            // The launcher goes first: a window command acts on the window below it.
            if (!stays && ShellState.panel === "launcher")
                ShellState.close();
            if (Array.isArray(entry.call)) {
                const call = calls[entry.call[0]];
                if (call)
                    call(String(entry.call[1] ?? ""));
            } else if (Array.isArray(entry.run) && entry.run.length > 0) {
                Quickshell.execDetached(argv(entry.run));
            }
        }
        return stays;
    }
    // Lock at once; the others ask in the session menu first.
    function session(action) {
        if (action === "lock") {
            ShellState.close();
            Quickshell.execDetached([Quickshell.env("HOME") + "/.local/bin/desktop-power", "lock"]);
            return;
        }
        ShellState.remember("power/ask", action);
        ShellState.close();
        ShellState.open("power");
    }
    // The commands of the desktop live in ~/.local/bin, which the PATH of the shell may lack; "~/" is the home folder.
    function argv(list) {
        return list.map((word, index) => {
            const text = String(word);
            if (index === 0 && text.startsWith("desktop-"))
                return Quickshell.env("HOME") + "/.local/bin/" + text;
            return text.startsWith("~/") ? Quickshell.env("HOME") + text.slice(1) : text;
        });
    }
    // A row of a provider category by its id ("system.powerProfile.balanced"), null without one.
    function rowNamed(id) {
        const dot = id.lastIndexOf(".");
        const category = dot < 0 ? null : model.items[id.slice(0, dot)];
        return category && Model.hasRows(category) ? rows(category).find(row => row.id === id) ?? null : null;
    }
    // desktop-shell commands ID: a command or a row runs, a category opens in the launcher; "" opens the first level.
    function request(id) {
        const entry = id === "" ? null : model.items[id] ?? rowNamed(id);
        if (id !== "" && !entry)
            return false;
        if (entry && (entry.row || !Model.opens(entry))) {
            run(entry);
            return true;
        }
        ShellState.remember("launcher/commands", entry ? entry.id : "");
        if (ShellState.panel === "launcher")
            ShellState.commandsRequested();
        else
            ShellState.open("launcher");
        return true;
    }

    FileView {
        path: Quickshell.shellDir + "/commands.json"
        // Read at once: desktop-shell commands ID can be the first thing that asks for the commands.
        blockLoading: true
        watchChanges: true
        printErrors: true
        onFileChanged: reload()
        onLoaded: {
            try {
                root.shipped = JSON.parse(text());
            } catch (failure) {
                console.warn("commands.json:", failure);
            }
        }
    }
    // The commands of the user: an entry of the same id changes the shipped one, "hidden": true leaves it out, a new
    // one is added. A file that does not parse is left out whole, with a notification; no file, nothing added.
    FileView {
        path: Config.directory + "/commands.json"
        blockLoading: true
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoadFailed: root.own = {}
        onLoaded: {
            let value;
            try {
                value = JSON.parse(text());
            } catch (failure) {
                root.own = {};
                Quickshell.execDetached(["notify-send", "--app-name=" + I18n.tr("launcher.title"), "--app-icon=dialog-warning", I18n.tr("commands.errors.ownFile"), String(failure.message ?? failure)]);
                return;
            }
            root.own = value && typeof value === "object" && !Array.isArray(value) ? value : {};
        }
    }
    // Which programs named by "requires" are installed: one shell, a line per program found.
    Process {
        id: requireCheck
        property var names: []
        function check() {
            const wanted = Model.required(root.model);
            if (wanted.join(" ") === names.join(" "))
                return;
            names = wanted;
            if (wanted.length === 0) {
                root.programs = {};
                return;
            }
            command = ["sh", "-c", "for name; do command -v \"$name\" >/dev/null 2>&1 && echo \"$name\"; done", "sh"].concat(wanted);
            running = false;
            running = true;
        }
        // The programs of the desktop and of agents installers are in ~/.local/bin.
        environment: ({
                PATH: Quickshell.env("HOME") + "/.local/bin:" + Quickshell.env("PATH")
            })
        stdout: StdioCollector {
            onStreamFinished: {
                const found = {};
                for (const name of text.split("\n"))
                    if (name !== "")
                        found["requires:" + name] = true;
                root.programs = found;
            }
        }
    }
    // The workspaces not on tiling (config/workspace_layouts.lua), as the bar reads them.
    FileView {
        id: layoutsFile
        property var modes: ({})
        path: (Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME") + "/.local/state") + "/desktop-session/workspace-layouts.json"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            try {
                const value = JSON.parse(text());
                modes = value && typeof value === "object" ? value : {};
            } catch (failure) {
                modes = {};
            }
        }
    }
    // Restart to the firmware setup is offered only on a UEFI system.
    Process {
        id: efiCheck
        property bool found: false
        running: true
        command: ["test", "-d", "/sys/firmware/efi"]
        onExited: code => found = code === 0
    }
}
