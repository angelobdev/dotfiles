//@ pragma UseQApplication
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Services.UPower
import Quickshell.Networking
import Quickshell.Bluetooth
import "bar"
import "panels"
import "controlcenter"
import "notifications"
import "session"
import "osd"
import "services"

ShellRoot {
    // Eagerly load shared services, including the notification D-Bus owner.
    property var audio: Audio
    property var notices: Notices
    property var clipboard: Clipboard
    property var bluetoothAgent: BluetoothAgent
    IpcHandler {
        target: "desktop"
        function toggle(panel: string): void {
            ShellState.toggle(panel);
        }
        function close(): void {
            ShellState.close();
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
                networkDevices: Networking.devices.values.length,
                notifications: Notices.notifications.values.length,
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
            required property var modelData
            Bar {
                screen: modelData
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
