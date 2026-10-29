//@ pragma UseQApplication
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Services.UPower
import Quickshell.Networking
import Quickshell.Bluetooth
import "bar"
import "dock"
import "panels"
import "controlcenter"
import "notifications"
import "session"
import "osd"
import "services"

ShellRoot {
    // Eagerly load shared services, including the notification D-Bus owner, the dynamic theme watcher and the tablet posture.
    property var audio: Audio
    property var notices: Notices
    property var clipboard: Clipboard
    property var bluetoothAgent: BluetoothAgent
    property var dynamicTheme: DynamicTheme
    property var tablet: Tablet
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
        function close(): void {
            ShellState.close();
        }
        // Opens the Theming panel on a tab; desktop-shell uses it to come back after a restart.
        function theming(tab: string): void {
            themingPanel.tab = tab;
            if (ShellState.panel !== "theming")
                ShellState.toggle("theming");
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
                batteryWatts: UPower.displayDevice?.changeRate ?? null,
                batteryTimeToEmpty: UPower.displayDevice?.timeToEmpty ?? null,
                hintsBindings: hints.bindings.length,
                powerSelection: powerMenu.selectedAction,
                powerPending: powerMenu.pending,
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
                workspaces: Quickshell.screens.map(s => ({
                            monitor: s.name,
                            active: Hyprland.monitorFor(s)?.activeWorkspace?.id
                        })),
                quiet: Notices.quiet,
                tablet: {
                    active: Tablet.active,
                    accelerometer: Tablet.available,
                    orientation: Tablet.orientation,
                    transform: Tablet.transform,
                    rotationLock: Tablet.locked
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
        }
    }
    OsdPopup {}
    Launcher {}
    Controls {}
    NetworkPanel {}
    AudioPanel {}
    BluetoothPanel {}
    BluetoothAuthentication {}
    BatteryPanel {}
    CalendarPanel {}
    Hints {
        id: hints
    }
    RecordingPanel {}
    ClipboardPanel {}
    WallpaperPicker {}
    ThemingPanel {
        id: themingPanel
    }
    NotificationCenter {}
    NotificationPopups {
        id: popupWindow
    }
    PowerMenu {
        id: powerMenu
    }
    Authentication {
        id: authentication
    }
}
