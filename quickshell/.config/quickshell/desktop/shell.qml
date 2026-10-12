//@ pragma UseQApplication
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Services.UPower
import Quickshell.Networking
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
            Wallpaper { screen: modelData }
            Bar { screen: modelData }
        }
    }
    Launcher {}
    Controls {}
    NotificationCenter {}
    NotificationPopups { id: popupWindow }
    PowerMenu {}
    Authentication { id: authentication }
}
