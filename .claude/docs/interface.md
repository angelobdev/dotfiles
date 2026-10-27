# Interface and shortcuts

[← README](../../README.md)

## Interface

- Bar height: 38 logical pixels. Fedora/app menu → occupied/active workspaces and at least two pills per monitor → window title → spacer → tray → battery (percentage + icon) → Hints → notifications → Control Center → date/time → session. Controls are 30 px, centered status icons 16 px, and the logo 18 px. Network and volume controls live in the Control Center.
- QML tray menus with rounded corners, neutral backgrounds/borders, hover, submenus, checkboxes, and disabled actions; Esc or an outside click closes the menu.
- Vector icons in a filled, macOS-like style (solid shapes with knockouts, 1.8 px round lines, 24 px grid) and native tooltips below buttons, outside the bar surface. Original application icons retain their colors.
- Launcher with search, left-aligned titles, icons, arrow-key navigation, and Enter; terminal applications open in Kitty.
- Translucent surfaces, light borders, and Hyprland blur; hyprpaper supplies the wallpaper.
- Network, Bluetooth, Notifications, and Battery panels align to the top right, sharing a width configured in `Config.qml` and headers with 22 px icons. Do Not Disturb/Clear all actions sit to the right of the Notifications title. Select power profiles in the battery panel; the battery block in the bar shows a gauge with the needle low for Power Saver and high for Performance, with no extra icon for Balanced. The battery icon fills in quarters with the charge (100/75/50/25/0) and switches to the charging icon on AC power; Wi-Fi icons in the Control Center tile and the network list show signal strength in three steps. The indicator follows external system profile changes; the tooltip always includes the current profile.
- Separate panels: Network & Wi-Fi with network search/selection, a current-connection card (IP, band/channel or link speed), Ethernet devices with cable state, and a details view for saved networks (arrow on the row or the card; Back or `Esc` returns to the list). Details show signal, band, IP, router, DNS, IPv6 and hardware address; reveal, copy, or share the Wi-Fi password as a QR code; toggle automatic connection and metered state; choose Automatic, preset, or custom DNS; switch IPv4 between DHCP and a manual address/prefix and router (prefilled from the current lease; manual addressing also needs DNS servers); pick the MAC address mode (Default, Private per network, Rotating, or Fixed; changing it reconnects); disconnect; and forget the network after a confirmation click. **Other network…** below the Wi-Fi list joins a hidden network (open or WPA/WPA2/WPA3 Personal); a failed attempt removes the profile it created. A **VPN** section shows Tailscale (state, address, online devices, exit node; the switch runs `tailscale up`/`down`, which needs the user to be the Tailscale operator) and toggles NetworkManager VPN and WireGuard connections; it appears only when Tailscale or such profiles exist. NetworkManager VPNs that ask for a password or OTP at connection time need a secret agent, which the shell does not provide. **Personal hotspot** shares this computer's connection over Wi-Fi (named after the host, WPA2 with a generated 12-character password shown with reveal, copy, and QR); on this card the client Wi-Fi turns off while it is on, so it is useful with Ethernet or USB tethering. **Advanced settings…** opens `nm-connection-editor`, and **Edit in Network Connections…** in the details view opens the profile there. Copied passwords are marked sensitive (excluded from clipboard history) and cleared after 45 s if still on the clipboard; Audio with volume, mute, default input/output, and microphone level; Battery with power in W, energy in Wh, remaining runtime/charging time, and power profiles. Personal Wi-Fi networks have a password prompt; enterprise networks require a preconfigured profile.
- Compact Control Center at the top right: Network/Bluetooth tiles, primary display brightness with an expandable section for other displays, selected speaker volume with an expandable input/output selector and microphone level, MPRIS media controls, Do Not Disturb, and Keep awake. Configure modules and ordering in `Config.qml`. Bluetooth has a subpanel with adapters, scanning, PIN/confirmation pairing through a dedicated BlueZ agent, connection/disconnection, and battery level when exposed by BlueZ. Power profiles depend on hardware.
- Notification popups with icons and formatted text (`b`, `i`, `u`, `s`, `strong`, `em`, `br`); left-click invokes the default action when present, right-click hides the popup while retaining the notification. Other actions remain buttons; in the notification center, **Delete** is red and aligned with the title, and the default action remains available as a button. History is in memory and resets when the shell restarts. Images and HTML attributes are stripped from the text.
- QML Polkit agent using the default identity suggested by Polkit.
- Keyboard-accessible power menu: immediate lock; suspend, logout, reboot, and shutdown require confirmation. Command errors appear in the panel.
- Monthly calendar with day selection, indicators, and an agenda from calendars enabled in GNOME/Online Accounts. Includes recurring, all-day, multi-day, and time-zone-aware events through Evolution Data Server. The panel reads existing calendars without creating/modifying events or accounts.
- Hints with search and categories (Applications, Shell & panels, Screen capture, Windows, Workspaces, Mouse, Audio & brightness, Session, Other): reads `hyprctl -j binds` whenever opened and when Hyprland reloads while the panel is visible. It shows actual shortcuts and descriptions, including submaps and bindings added in `local.lua`. `Print` is displayed as “Print” in English; screenshots and recording have a dedicated category. Known descriptions and categories follow the selected UI language.
- QML wallpaper picker with directory navigation and previews; no external dialog.
- Quickshell clipboard with search and pause; custom screen-sharing picker and recording panel with a bar indicator.
- Quickshell OSDs for volume, speaker mute, microphone, and brightness: icon, level, and device at the bottom center, without intercepting mouse or keyboard input.

NetworkManager, BlueZ, PipeWire/WirePlumber, UPower, Polkit, and power-profiles-daemon provide system services. Configuration starts Quickshell, hypridle, and hyprpaper. No Waybar, nm-applet, Blueman, Sway, or separate notification server is used.

## Shortcuts

| Keys | Action |
| --- | --- |
| `Super + B` | Browser (`zen-browser`) |
| `Super + Shift + Space` | 1Password quick access (local override) |
| `Super + Enter` | Kitty |
| `Super + Q` | Close window |
| `Super + Space` | Applications |
| `Super + Shift + C` | Control Center |
| `Super + Shift + E` | Network & Wi-Fi |
| `Super + Shift + V` | Sound & audio devices |
| `Super + Shift + B` | Battery & power |
| `Super + Shift + N` | Notifications |
| `Super + Shift + D` | Calendar |
| `Super + Shift + H` | Hints / active bindings |
| `Super + Shift + Q` | Session menu |
| `Super + Shift + W` | Choose wallpaper |
| `Super + Ctrl + C` | Clipboard / history |
| `Super + Ctrl + R` | Screen recording |
| `Super + L` / `XF86Sleep` | Lock / suspend with lock |
| `Super + Shift + R` | Restart Quickshell |
| `Super + V` / `Super + Shift + F` | Floating / fullscreen |
| `Super + Ctrl + P` / `Super + J` | Pseudotiling / split orientation |
| `Super + arrows` / `Super + Shift + arrows` | Focus / move window |
| `Super + 1…9,0` / `Super + Shift + 1…9,0` | Workspace / move to workspace |
| `Super + Shift + S` / `Print` | Area screenshot with editor |
| `Super + Shift + Alt + S` / `Alt + Print` | Monitor screenshot with editor |
| `Super + left/right drag` | Move / resize window |
| `XF86AudioPlay` / `XF86AudioPause` | Play/pause toggle / pause |
| `XF86AudioNext` / `XF86AudioPrev` / `XF86AudioStop` | Next / previous / stop |
| `XF86Calculator` | Calculator (`gnome-calculator`) |
| Multimedia keys | Volume, microphone, brightness |
| `Esc` / outside click | Close panel |

In the session menu, **↑/↓ and Tab/Shift+Tab** move focus; **Enter or Space** activates the button. Confirmation requests focus **Cancel**: use **←/→ or Tab** to choose Confirm. **Esc** cancels confirmation, then closes the panel. The first button receives focus on opening.

In the calendar, arrow keys move between days, PgUp/PgDn changes months, and Home selects today. In the wallpaper picker, arrows navigate the list, Enter opens a directory/selects an image, and Backspace goes to the parent; Tab reaches the path, apply, and restore controls.

## Omnibook action keys

Verified with `wev` on this machine. Fn/Fn Lock determines whether the action keys require holding Fn; ordinary F1/F2 function keys are not rebound.

| Physical action key | Event emitted by firmware | Action |
| --- | --- | --- |
| F1, two displays | `Super + P` | Control Center (including display brightness controls) |
| F2, calculator | `XF86Calculator` | GNOME Calculator |
| F10, play/pause | `XF86AudioPlay` | Play/pause the selected MPRIS player |
| F11, three diamonds | `XF86Launch2` | Control Center |

The original `Super + P` pseudotiling shortcut conflicted with the firmware's display key; pseudotiling now uses `Super + Ctrl + P`. Machine-specific Control Center aliases live in `hypr/config/local.lua`. The screenshot shortcut remains `Super + Shift + S`; no ordinary function-key shortcut was added for screenshots.

Media keys call Quickshell through `desktop-shell media ACTION`, using the same selected/playing/fallback player as the Control Center. Commands unsupported by that player, or commands with no available player, do nothing. Play/pause, pause, next, previous, and stop remain available while locked, without repeat-triggering transport actions. No additional media daemon or playerctl process is required.

## Workspaces per monitor

The bar shows occupied/active workspaces and at least two pills per monitor. Empty slots are placeholders: a workspace is created only when clicked or reached by scrolling. IDs are assigned globally without reusing another monitor's workspaces; special workspaces are excluded. Clicking first focuses the bar's monitor. Scrolling or a vertical touchpad gesture over the workspace area moves to the previous/next workspace, stopping at the ends. Touchpad deltas accumulate to prevent accidental switches; the area responds over the entire bar height.

In `Config.qml`: `minimumWorkspaces: 2` (minimum 2, maximum 10) and `workspaceScroll: true`.

## Clipboard

`Super + Ctrl + C` opens Quickshell history: search, arrows/Enter to copy, individual deletion, clearing with confirmation, and collection pause. Copying closes the panel; paste into an application with its normal shortcut. Cliphist retains text and images, with two `wl-paste` watchers managed by the shell. Hyprland's XWayland bridge synchronizes the X11/Wayland selection; no second synchronizer is started. Hyprland may limit X11 reading when no X11 window has focus.

`clipboardEnabled: true` and `clipboardMaxItems: 200` are in `Config.qml`. Pause resets on restart. History persists in `$XDG_CACHE_HOME/cliphist/db` (normally `~/.cache/cliphist/db`), with a private directory: **it is stored on disk, unencrypted**. Cliphist ignores selections marked `sensitive` by an application; this requires the application to mark them. Disable collection or pause it for content you do not want retained. History does not synchronize the X11 primary/mouse selection.

## Screen recording

`Super + Ctrl + R` opens the Quickshell panel. Choose a display or area, then None/Speaker/Microphone audio and Start. For areas, drag within a single monitor; `Esc` cancels. While recording, the bar shows an icon and elapsed time: clicking stops and saves; the panel also offers **Stop and save**. Recording continues while the panel is closed. The wrapper forwards SIGINT to the recorder to finalize the file even when terminated by the shell.

Videos are saved to the XDG Videos directory, in `Recordings`, with unique filenames and private permissions. Format: Matroska (`.mkv`), VP9 video, and Opus audio when enabled. In `Config.qml`: `recordingFramerate: 30` (1–60) and `recordingCodec: "libvpx-vp9"`. Speaker audio captures the default output's monitor at startup; Microphone uses the default input. Change devices before starting. Stop recording before leaving the session.

## Screenshots

HyprCapture handles capture; the screenshot key uses the `Print` keysym.

| Shortcut | Capture |
| --- | --- |
| `Super + Shift + S` / `Print` | Area selection, then editor |
| `Super + Shift + Alt + S` / `Alt + Print` | Current monitor, then editor |

`Esc` cancels selection. PNGs are saved in the XDG Pictures directory under `Screenshots`, copied to the clipboard, and announced through Quickshell. Configure the directory and behavior in `hypr/config/plugins.lua`, under `hyprcapture`. Scratchpad bindings remain removed. All screenshot shortcuts open HyprCapture's native editor after selection: rectangles, ellipses, arrows, drawing, text, pixelation, and numbering. `Enter` or the checkmark exports; `Esc` cancels. No additional editor is needed.

The overlay follows the pointer across monitors (`overlay_scope = "focus"`), including different scales. To capture the built-in display, start there or move the pointer from the external monitor before selecting. Area selections stay within a single monitor; `fullscreen_scope = "current"` captures the chosen monitor rather than the entire desktop.

Follow [Hyprland plugins](plugins.md) to enable the backend. If the plugin is not loaded, the binding shows a notification. Quickshell panel recording continues to use wf-recorder.

## Hot corner and touchscreen

The top-left corner of each monitor opens or closes Hyprspace through hypr-hot-edge. The zone is 8 px, with a 220 ms delay; the exact corner pixel triggers immediately, as designed by the plugin. After activation, leave the zone before activating again; returning to the corner closes an open overview. `Esc` closes the overview. No keyboard binding opens it.

During the overview, the affected monitor's bar is invisible, releases its 38 px, and receives no clicks. Previews exclude bars and overlays; Hyprspace adds no 200 px reserved area. Closing restores the bar and normal layout.

| Touchscreen gesture (Hyprgrass) | Action |
| --- | --- |
| Three-finger horizontal swipe | Workspace |
| Three-finger upward swipe | Hyprspace |
| Swipe upward from bottom edge | Applications |
| Swipe downward from top edge | Control Center |
| Long press on window border | Resize |

Sensitivity, edge margins, and actions are in `hypr/config/plugins.lua`. Touchpad gestures remain in `input.lua`: three fingers horizontally for workspaces, upward for applications, downward for controls.

## Panel data

Audio uses PipeWire nodes and changes default devices through Quickshell APIs; WirePlumber decides how to route existing streams. UPower supplies battery power in W, energy in Wh, and estimated times: this is not total wall-socket consumption and may vary over time. Missing estimates are indicated without inventing a runtime. The calendar reads enabled Evolution Data Server sources, including Online Accounts; GNOME still manages synchronization and credentials. Reads may require network access. Events remain in shell memory; EDS keeps its own cache. Do Not Disturb silences popups while retaining notifications in the center; its state resets when the shell restarts.

Tray menus open below the icon on the same monitor. Positioning follows actual Wayland surface dimensions; near an edge it is constrained to available space, and submenus may open to the left.
