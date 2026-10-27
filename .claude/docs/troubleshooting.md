# Troubleshooting and verification

[← README](../../README.md)

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

## Icon pack verification

The 48 icons were exported from Figma as plain SVG paths (knockouts flattened by boolean operations, so no masks are needed) and recolored to `white` for `MultiEffect` colorization. After `./scripts/stow.py apply` linked the seven new files and the dangling `battery`/`battery-low` links were removed, a `desktop-shell restart` loaded without icon warnings. A screenshot confirmed the bar battery at 61% rendering `battery-50`, filled bell/keyboard/Control Center icons, and the network tile showing `wifi-2` (connected network at signal 0.46, with the dimmed outer fan visible). Quickshell's `signalStrength` is in the 0–1 range.

## Network panel verification

`network.py` was exercised end-to-end on a temporary inactive Wi-Fi profile (SSID and password containing `:`, `;`, `"`, and `\`): profile reads, Cloudflare and custom DNS (invalid servers rejected with a translated error), Automatic DNS, metered and autoconnect toggles, password read, QR payload escaping, and a 33×33 QR matrix from libqrencode; the profile was deleted afterwards. NetworkManager allowed profile changes and secret reads without a Polkit prompt for the logged-in user. A copied test password carried `x-kde-passwordManagerHint`, did not enter cliphist history, and was cleared after 45 s. The live panel showed the current-connection card (IP, 2.4 GHz channel 1), detail arrows on saved networks, and locks on secured unknown ones; the details view was rendered with the real connection (password hidden) and with a QR code from the temporary profile. Changing DNS on the real connection was left to the user. No Ethernet adapter was connected, so the wired section is untested on hardware.

Phase 2 was tested the same way on temporary profiles: manual IPv4 with prefix and dotted-mask forms, rejection of malformed addresses, network/broadcast addresses, missing prefixes and routers outside the subnet, return to DHCP; all four MAC modes (`stable-ssid`, `random`, `permanent`, and empty for the system default, which is `stable-ssid` on Fedora); and a WireGuard profile without peers or addresses listed, brought up, and down. Hidden-network joining was run against a non-existent interface so activation failed without touching Wi-Fi: the profile was saved with the password from stdin, the failure was reported without the editor transcript (which echoes the password), and the profile was deleted. `nmcli` reports the saved profile on stderr when stdin is not a terminal and asks for confirmation when saving with autoconnect on, so the helper saves with autoconnect off and enables it after a successful activation. The panel was rendered in a separate instance with the VPN section and the hidden-network form, and the details view with the IPv4 and MAC sections.

Phase 3: `tailscale up` while already running was confirmed to be a no-op (only an `--accept-routes` notice); `tailscale down` was not run to avoid cutting live tailnet sessions. The hotspot profile was created against a non-existent interface so activation failed without touching Wi-Fi: AP mode, 2.4 GHz band, shared IPv4/IPv6, WPA2 (RSN/CCMP), autoconnect off, a 12-character password set through stdin, and a 29×29 QR code; the profile was then deleted. Actually turning the hotspot on was left to the user because it disconnects Wi-Fi. The panel was rendered with the Tailscale row (Running, address, 1/3 devices online), the hotspot row, and the advanced-settings link; the details view was re-rendered after moving the password row into `NetworkPassword.qml`. The combined `extras` poll takes about 240 ms.

## Motion verification

`Hyprland --verify-config` against scratch configs confirmed the Lua layer-rule fields `no_anim` and `animation` (unknown fields such as `no_animation` are rejected), spring curves (`type = "spring"`, `mass`, `stiffness`, `dampening`), and `slidefade` styles; the live config reloaded with no `hyprctl configerrors`, and `hyprctl animations` shows `windowsMove` on `spring:move`. After restarting the shell, the Control Center, launcher, and power menu were toggled repeatedly with no log warnings, `ShellState.panel` returned to empty, and no `desktop-overlay` layer remained mapped. Captured frames showed the Control Center mid-slide and scaled while opening and still visible while fading out on close. `grim -g` takes logical coordinates (the internal panel runs at scale 1.667).

Phase 2: two `notify-send` toasts were captured mid-entrance (the second offset and translucent, the first unmoved, so it was not recreated), with no log warnings. A separate instance with the Control Center and Network panels drove `ShellState.push("network")` and `back()`; burst-captured frames showed the Network panel entering from the right and, on Back, leaving to the right while the Control Center returned. The live `layer_rule` now also covers `desktop-notifications`.

Phase 3: after `stow.py apply` linked `Expander.qml`, the shell restarted cleanly and the Control Center, launcher, notification center, and clipboard opened and closed with no log warnings. A separate instance switched three 96 px icons from `wifi` to `wifi-off` and grabbed them at 40, 100, and 600 ms: both glyphs overlapping, the new one dominant, then only the new one.

## Steam and gamescope verification

The user confirmed improved text clarity with 1:1 XWayland rendering, but changing `-forcedesktopscaling` from 1.667 to 2 did not visibly enlarge the interface. Exporting `STEAM_FORCE_DESKTOPUI_SCALING` to both client and web helper also left the header unchanged. Steam's Interface HiDPI switch was already on. SDL reported content scale 1 through Wayland and 2 through X11 with its hint, but that alternate backend did not change the desktop UI either. Those diagnostics establish that startup arguments and environment alone are insufficient for this installed build.

The renderer initialization workaround was then verified with cropped menu screenshots: the same 500×95 logical region showed visibly doubled labels and controls after setting the CEF scale to 2 at initialization. A subsequent restart through the permanent runtime wrapper retained the enlarged rendering. `/proc` checks confirmed the managed library in all eight web-helper processes and absent from the main Steam client's preload environment; temporary test preloads were removed by the clean restart. No Steam binaries or startup scripts were edited, no debugger remains attached, and no debugging port was enabled. See [Steam and gamescope](integrations.md#steam-and-gamescope) for implementation and disabling the workaround.

`~/.config/desktop/steam.json` selects 2 for eDP-1 while other monitors retain their detected scale. Simulated startup on an unscaled HDMI monitor selected 1; physical HDMI startup remains to be checked. Exit and reopen Steam after changing a preference. A one-off override is `DESKTOP_STEAM_SCALE=1.5 desktop-steam` (range 1–4). Other legacy X11 applications may become smaller under the global 1:1 policy.

Gamescope 3.16.29 was tested with a temporary GLX graphics window on the Intel LNL GPU using Mesa 26.2.4: native Wayland presentation to Hyprland, Vulkan composition, and Intel OpenGL rendering succeeded. The installed wrapper also ran fullscreen on the 2880×1800 output with a 1920×1200 internal resolution, FSR, and a 60 FPS setting. High-priority Vulkan queues were unavailable and gamescope successfully fell back to normal priority; no elevated privileges or driver workarounds were needed.

Argument checks covered monitor scale 1/1.667, boolean/integer Hyprland option formats, rotated physical dimensions, caller scaling overrides, invalid scales, and command arguments containing spaces/shell characters. Script/Lua parsing, desktop-entry validation, Stow, and internationalization checks passed. These graphics tests do not establish performance, Steam overlay support, anti-cheat compatibility, or Proton behavior for a particular game. Test the desired game with `desktop-gamescope -- %command%` in its launch options and remove that option if it causes issues.
