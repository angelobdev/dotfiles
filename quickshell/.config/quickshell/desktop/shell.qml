//@ pragma UseQApplication
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Services.UPower
import Quickshell.Networking
import Quickshell.Bluetooth
import "modules"
import "services"
ShellRoot {
    // Eagerly load shared services, including the notification D-Bus owner.
    property var audio: Audio
    property var notices: Notices
    IpcHandler {
        target: "desktop"
        function toggle(panel: string): void { ShellState.toggle(panel); }
        function close(): void { ShellState.close(); }
        function status(): string {
            return JSON.stringify({ panel: ShellState.panel, screens: Quickshell.screens.length,
                workspace: Hyprland.focusedWorkspace?.id ?? -1,
                volume: Audio.volume, muted: Audio.muted,
                audioOutputs: Audio.outputs.length, audioInputs: Audio.inputs.length,
                audioOutput: Audio.sink?.description ?? "", audioInput: Audio.source?.description ?? "",
                batteryWatts: UPower.displayDevice?.changeRate ?? null,
                batteryTimeToEmpty: UPower.displayDevice?.timeToEmpty ?? null,
                hintsBindings: hints.bindings.length, powerSelection: powerMenu.selectedAction, powerPending: powerMenu.pending,
                bluetoothAdapters: Bluetooth.adapters.values.length, brightness: Brightness.monitors, quiet: Notices.quiet,
                networkDevices: Networking.devices.values.length,
                notifications: Notices.notifications.values.length,
                polkitRegistered: authentication.registered, popups: Notices.popups.length,
                popupVisible: popupWindow.visible, popupHeight: popupWindow.implicitHeight });
        }
    }
    Variants {
        model: Quickshell.screens
        delegate: Scope {
            required property var modelData
            Bar { screen: modelData }
        }
    }
    Launcher {}
    Controls {}
    NetworkPanel {}
    AudioPanel {}
    BluetoothPanel {}
    BatteryPanel {}
    CalendarPanel {}
    Hints { id: hints }
    WallpaperPicker {}
    NotificationCenter {}
    NotificationPopups { id: popupWindow }
    PowerMenu { id: powerMenu }
    Authentication { id: authentication }
}
