# Troubleshooting and verification

[← README](../README.md)

## Customization and diagnostics

`hypr/.config/hypr/config/local.lua` holds machine overrides. The QML palette is in `Theme.qml`, icons in `assets/icons`, and GTK CSS/Qt colors in their respective packages. Quickshell and Hyprland reload their configurations; restart hypridle/hyprpaper after changing their files. Autostart runs at login; `desktop-session start` and `desktop-shell start` avoid duplicate processes. `desktop-shell restart` waits for the previous instance to exit before starting another.

```sh
~/.local/bin/desktop-shell status
~/.local/bin/desktop-session status
qs log -c desktop
hyprctl configerrors
hyprctl getoption xwayland:enabled
xprop -root _NET_SUPPORTING_WM_CHECK
readlink -f ~/.local/state/desktop-session/wallpaper/current.jpg
cat ~/.local/state/desktop-session/hypridle.log
cat ~/.local/state/desktop-session/udiskie.log
./scripts/check.sh
```

Completed checks: OSDs with simulated services (volume, speaker/microphone mute, rapid updates, timeout, disabling, audio reconnection, panel suppression, and multiple monitors); backlight watcher on simulated sysfs (baseline, changes, hotplug, and invalid values); brightness dragging regression with queued writes; Lua/script parsing; QML loading/layout; Control Center and expandable sections; tooltip placement; brightness helper with fake backends (routing, limits, and DDC scaling); live dragging updates without stale-value rollback and hardware error handling; Wayland inhibitor creation/release while panels are closed; native Wi-Fi scanning; audio devices and UPower readings; leap-year/year-boundary calendar behavior; complete power-menu navigation with a fake command; persistent wallpaper selection. Wallpaper tests cover spaces/commas in filenames and retention of the previous choice after invalid files or IPC errors. Earlier Hyprshot checks covered duplicate bindings and saving/copying in all four modes with simulated backends; its interactive capture was not physically tested before replacement by HyprCapture.

Later checks: multiple-monitor workspace model (minimum count, unique IDs, active/urgent states, and exclusion of special workspaces); isolated clipboard history with byte-for-byte Unicode text and PNG copying, deletion, and clearing; X11/Wayland bridge with the original selection restored; real recordings of a test window with/without speaker audio, finalized Matroska files, and ffprobe inspection; VS Code/Electron X11 and Wayland with temporary profiles; ScreenCast portal and PipeWire frame reception; new Hyprlock layout and fprintd device acquisition in a headless compositor. QML panels were checked with mock data. Physical unlock tests and the user's calling web app remain to be tested.

## Current-phase verification

- Popups: simulated click events on the real component, default action invoked once, right-click without deletion; filtered markup and notification-center actions retained.
- Bluetooth: simulated BlueZ on a private D-Bus bus, agent registration/release, PIN and passkey, confirmation, rejected authorizations, stale responses ignored, code display, and cancellation. No real device was paired or removed during testing.
- MPRIS: two players on a private bus, metadata, selection, state changes, transport commands, seeking with seconds/microseconds conversion, and fallback when a player disappears.
- Calendars: all four existing EDS sources read without errors; event contents omitted from diagnostic logs.
- QML layout: Control Center, agenda, Bluetooth request, and popups rendered with mock data.
- Hotplug: physical HDMI disconnection/reconnection verified. DDC/CI on the Philips FTV was unavailable in these tests; see [details](configuration.md#philips-ftv-display-verification-results).

Final pairing with a physical device remains manual through **Bluetooth → Scan for devices**. Real DDC reads/writes still need validation on a compatible monitor.

- Application rendering: the reported ChatGPT and Nautilus instances were X11 at scale 1.667; instances with isolated profiles/buses were verified as native Wayland. Local launchers were updated without closing the user's applications.
- Tray: regression with the icon 600 px from the edge, menu below the icon after Wayland sizing, hover, disabled actions, checkboxes, submenus, Escape, and outside clicks.
- Reorganization: full QML loading and the sharing picker verified after updating imports and Stow links.
- Internationalization: nested semantic catalogs, locale selection, placeholders, plural messages, fallback, QML/Python/command references, and both interface languages checked. Italian expectations are read from `it_IT.json`; other repository content uses English.

## References

[Hyprland Lua](https://wiki.hypr.land/Configuring/Start/), [Quickshell](https://quickshell.org/docs/v0.3.0/types/), [PopupAnchor](https://quickshell.org/docs/v0.3.0/types/Quickshell/PopupAnchor/), [IdleInhibitor](https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/IdleInhibitor/), [Hyprshot](https://github.com/Gustash/Hyprshot), [DDC/CI brightness](https://www.ddcutil.com/command_getvcp/), [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/), [hyprlock](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/), [hyprpaper](https://wiki.hypr.land/Hypr-Ecosystem/hyprpaper/), [Hyprland portal](https://wiki.hypr.land/Hypr-Ecosystem/xdg-desktop-portal-hyprland/), [Electron Wayland](https://www.electronjs.org/blog/tech-talk-wayland), [cliphist](https://github.com/sentriz/cliphist), [wf-recorder](https://github.com/ammen99/wf-recorder), [Kitty](https://sw.kovidgoyal.net/kitty/conf/).

## Removable media verification

Udiskie 2.7.0 accepted the managed configuration, started without errors or a tray icon, and remained a single process after two consecutive `desktop-session start` calls. iPhone pairing validation, AFC mounting, and a root metadata query succeeded after device trust was accepted. No personal file contents were read. Insertion and safe removal of a physical USB drive remain to be tested.

## Omnibook keys and bar focus

The action-key capture identified F1 as `Super + P`, F2 as `XF86Calculator`, F10 as `XF86AudioPlay`, and F11 (three diamonds) as `XF86Launch2`. The existing pseudotiling binding consumed the P event; a temporary non-consuming bind confirmed the firmware combination and was removed immediately afterward.

The bar's persistent button highlight was reproduced with a real BarButton and synthetic mouse events: a clicked button retained active focus after the pointer left. Bar buttons now visualize only keyboard focus (`visualFocus`), while panel buttons retain programmatic focus highlighting. Regression checks cover mouse exit, keyboard focus, and panel focus. MPRIS transport was tested with two simulated players on a private D-Bus bus, including selected-player routing and rejection of unsupported commands; no personal playback was controlled during those tests.
