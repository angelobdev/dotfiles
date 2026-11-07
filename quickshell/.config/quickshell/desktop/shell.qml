//@ pragma UseQApplication
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Services.UPower
import Quickshell.Networking
import Quickshell.Bluetooth
import "bar"
import "assist"
import "components"
import "dock"
import "panels"
import "controlcenter"
import "notifications"
import "osk"
import "session"
import "osd"
import "services"

ShellRoot {
    // Eagerly load shared services, including the notification D-Bus owner, the dynamic theme watcher, the tablet posture, Night shift, the assist button and the on-screen keyboard (raised over panels).
    // Panels are lazy, so every service with side effects (warnings, inhibitors, power changes) must be listed here.
    property var audio: Audio
    property var notices: Notices
    property var clipboard: Clipboard
    property var bluetoothAgent: BluetoothAgent
    property var dynamicTheme: DynamicTheme
    property var tablet: Tablet
    property var nightShift: NightShift
    property var battery: Battery
    property var idle: Idle
    // The rotation sensor and helper run for this shell only, not for other configs that load Theme.
    Binding {
        target: Tablet
        property: "enabled"
        value: true
    }
    IpcHandler {
        target: "desktop"
        function toggle(panel: string): void {
            ShellState.toggle(panel);
        }
        function media(action: string): bool {
            return Media.control(action);
        }
        function dock(action: string): bool {
            return Dock.request(action);
        }
        function dockLaunch(index: int): bool {
            return Dock.launchIndex(index);
        }
        function keepAwake(action: string): bool {
            return Idle.request(action);
        }
        function quiet(action: string): bool {
            return Notices.request(action);
        }
        function tablet(action: string): bool {
            return Tablet.request(action);
        }
        function rotationLock(action: string): bool {
            return Tablet.requestLock(action);
        }
        // The overview is opening (the four-finger swipe in plugins.lua): watch the bars closely for a while.
        function overview(): void {
            BarVisibility.wake();
        }
        // Screen zoom: in, out, reset, toggle.
        function zoom(action: string): bool {
            return Zoom.request(action);
        }
        // A focus session: toggle, start (minutes: 0 for Config.focusMinutes), stop.
        function focus(action: string, minutes: int): bool {
            return Focus.request(action, minutes);
        }
        function nightShift(action: string): bool {
            return NightShift.request(action);
        }
        function assist(action: string): bool {
            return Assist.request(action);
        }
        // The menu open on a page (apps, window, system), for scripts and tests.
        function assistPage(name: string): bool {
            if (!Assist.pages.some(p => p.name === name))
                return false;
            Assist.page = name;
            return Assist.request("menu");
        }
        // Alt + Tab: next, previous, commit, cancel (binds.lua).
        function switcher(action: string): bool {
            return windowSwitcher.request(action);
        }
        function windowMenu(): void {
            ShellState.requestWindowMenu();
        }
        function keyboard(action: string): bool {
            return Keyboard.request(action);
        }
        function close(): void {
            ShellState.close();
        }
        // The desktop menu in the middle of the focused monitor.
        function desktopMenu(): void {
            ShellState.desktopMenuRequested(Hyprland.focusedMonitor?.name ?? "");
        }
        // Opens Settings on a section (appearance, …), or toggles it with none.
        function settings(section: string): void {
            if (section === "")
                ShellState.toggle("settings");
            else
                ShellState.openSection("settings", section, null, false);
        }
        // Opens Settings → Appearance on a tab; desktop-shell uses it to come back after a restart.
        // A tab, or store-icons / store-cursors for the KDE Store page.
        function theming(tab: string): void {
            ShellState.openSection("settings", "appearance", null, false);
            // Opening creates it at once (LazyPanel).
            settingsPanel.item?.showSection("appearance", tab);
        }
        function loadedPanels(): var {
            // data, not children: the loaders are not items.
            const names = [];
            for (let i = 0; i < panels.data.length; i++) {
                if (panels.data[i].item)
                    names.push(panels.data[i].name);
            }
            return names;
        }
        function status(): string {
            return JSON.stringify({
                panel: ShellState.panel,
                language: I18n.language,
                screens: Quickshell.screens.length,
                workspace: Hyprland.focusedWorkspace?.id ?? -1,
                volume: Audio.volume,
                muted: Audio.muted,
                audioOutputs: Audio.outputs.length,
                audioInputs: Audio.inputs.length,
                audioOutput: Audio.sink?.description ?? "",
                audioInput: Audio.source?.description ?? "",
                audioApps: Audio.streams.map(node => Audio.streamName(node)),
                batteryWatts: UPower.displayDevice?.changeRate ?? null,
                batteryTimeToEmpty: UPower.displayDevice?.timeToEmpty ?? null,
                batteryAlert: Battery.level,
                focusMinutesLeft: Focus.minutesLeft,
                privacy: {
                    microphone: Privacy.microphoneApps,
                    camera: Privacy.cameraApps,
                    sharing: Privacy.sharing
                },
                // Panels exist only while open and shortly after (LazyPanel): null otherwise.
                loadedPanels: loadedPanels(),
                hintsBindings: hints.item?.bindings.length ?? null,
                powerSelection: powerMenu.item?.selectedAction ?? null,
                powerPending: powerMenu.item?.pending ?? null,
                keepAwake: Idle.keepAwake,
                bluetoothAdapters: Bluetooth.adapters.values.length,
                bluetoothAgentRegistered: BluetoothAgent.registered,
                mediaPlayers: Media.players.length,
                calendarEvents: Calendar.events.length,
                calendarSources: Calendar.sources.length,
                brightness: Brightness.monitors,
                osd: {
                    visible: Osd.visible,
                    kind: Osd.kind,
                    percent: Osd.percent,
                    monitor: Osd.targetScreen?.name ?? ""
                },
                dock: {
                    items: Dock.items.map(i => i.key + (i.running ? "*" : "")),
                    pinned: Dock.pinned,
                    pinsSaved: Dock.pinned !== Config.dockPinned,
                    menu: Dock.menuScreen,
                    keyboard: Dock.keyboardScreen,
                    shown: Object.keys(Dock.shown),
                    requested: Dock.requested,
                    touch: Dock.touchScreen,
                    peeking: Object.keys(Dock.peeks)
                },
                clipboard: {
                    collecting: Clipboard.collecting,
                    count: Clipboard.entries.length
                },
                recording: {
                    running: Recording.running,
                    stopping: Recording.stopping,
                    seconds: Recording.seconds,
                    error: Recording.error
                },
                updates: {
                    count: Updates.count,
                    packages: Updates.packages.length,
                    flatpaks: Updates.flatpaks.length,
                    compositor: Updates.compositor,
                    checked: Updates.checked,
                    checking: Updates.checking,
                    errors: Updates.errors
                },
                agent: {
                    available: Agent.available,
                    agent: Agent.agent,
                    name: Agent.name,
                    installed: Agent.installedAgents,
                    running: Agent.running,
                    needsRestart: Agent.needsRestart,
                    directory: Agent.sessionDirectory,
                    agyStatusline: Agent.agyStatusline,
                    console: Agent.consoleScreen,
                    state: Agent.state,
                    unseen: Agent.unseen,
                    hasLimits: Agent.hasLimits,
                    plan: Agent.plan,
                    usage: Agent.usage
                },
                workspaces: Quickshell.screens.map(s => ({
                            monitor: s.name,
                            active: Hyprland.monitorFor(s)?.activeWorkspace?.id
                        })),
                quiet: Notices.quiet,
                tablet: {
                    active: Tablet.active,
                    accelerometer: Tablet.available,
                    touchscreen: Tablet.touchscreen,
                    orientation: Tablet.orientation,
                    transform: Tablet.transform,
                    rotationLock: Tablet.locked
                },
                nightShift: {
                    available: NightShift.available,
                    mode: NightShift.mode,
                    active: NightShift.active,
                    temperature: NightShift.temperature,
                    overridden: NightShift.overridden
                },
                keyboard: {
                    shown: Keyboard.shown,
                    floating: Keyboard.floating,
                    ready: Keyboard.ready,
                    page: Keyboard.page,
                    inputMethod: Keyboard.inputMethod,
                    purpose: Keyboard.purpose,
                    autoShown: Keyboard.autoShown,
                    locked: Keyboard.locked,
                    predicting: Keyboard.predicting,
                    learning: Keyboard.learning,
                    letters: Object.keys(Keyboard.letters).length,
                    touch: Keyboard.touchSpread(),
                    area: Keyboard.areaVisible ? [Keyboard.screenName, Keyboard.area.x, Keyboard.area.y, Keyboard.area.width, Keyboard.area.height] : []
                },
                assist: {
                    shown: Assist.shown,
                    menu: Assist.menuOpen,
                    actions: Assist.actions.map(a => a.name)
                },
                dynamicTheme: {
                    active: DynamicTheme.active,
                    source: DynamicTheme.source,
                    running: DynamicTheme.running
                },
                networkDevices: Networking.devices.values.length,
                notifications: Notices.notifications.values.length,
                archivedNotifications: Notices.archived.length,
                polkitRegistered: authentication.registered,
                popups: Notices.popups.length,
                popupVisible: popupWindow.visible,
                popupHeight: popupWindow.implicitHeight
            });
        }
    }
    Variants {
        model: Quickshell.screens
        delegate: Scope {
            id: scope
            required property var modelData
            Bar {
                screen: scope.modelData
            }
            DockWindow {
                screen: scope.modelData
            }
            ConsoleCatcher {
                screen: scope.modelData
                screenName: scope.modelData.name
            }
            // A right click or long press on the empty desktop: launcher, Settings, session.
            DesktopCatcher {
                screen: scope.modelData
                screenName: scope.modelData.name
                onMenuRequested: (x, y) => desktopMenu.popup(x, y)
            }
            DesktopMenuWindow {
                id: desktopMenu
                screen: scope.modelData
            }
        }
    }
    OsdPopup {}
    AssistWindow {}
    KeyboardWindow {}
    BluetoothAuthentication {}
    // Panels are created when they open and dropped a minute after they close (components/LazyPanel.qml).
    Item {
        id: panels
        LazyPanel {
            name: "launcher"
            Launcher {}
        }
        LazyPanel {
            name: "controls"
            Controls {}
        }
        LazyPanel {
            name: "network"
            NetworkPanel {}
        }
        LazyPanel {
            name: "audio"
            AudioPanel {}
        }
        LazyPanel {
            name: "bluetooth"
            BluetoothPanel {}
        }
        LazyPanel {
            name: "battery"
            BatteryPanel {}
        }
        LazyPanel {
            name: "calendar"
            CalendarPanel {}
        }
        LazyPanel {
            id: hints
            name: "hints"
            Hints {}
        }
        LazyPanel {
            name: "recording"
            RecordingPanel {}
        }
        LazyPanel {
            name: "agent"
            AgentPanel {}
        }
        LazyPanel {
            name: "updates"
            UpdatesPanel {}
        }
        LazyPanel {
            name: "clipboard"
            ClipboardPanel {}
        }
        LazyPanel {
            name: "wallpaper"
            WallpaperPicker {}
        }
        LazyPanel {
            id: settingsPanel
            name: "settings"
            SettingsPanel {}
        }
        LazyPanel {
            name: "emoji"
            EmojiPanel {}
        }
        LazyPanel {
            name: "displays"
            DisplayPanel {}
        }
        LazyPanel {
            name: "notifications"
            NotificationCenter {}
        }
        LazyPanel {
            id: powerMenu
            name: "power"
            PowerMenu {}
        }
    }
    WindowSwitcher {
        id: windowSwitcher
    }
    NotificationPopups {
        id: popupWindow
    }
    Authentication {
        id: authentication
    }
}
