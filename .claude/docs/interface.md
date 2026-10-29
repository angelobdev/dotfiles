# Interface and shortcuts

[← README](../../README.md)

## Interface

- Bar height: 38 logical pixels. Fedora/app menu → occupied/active workspaces and at least two pills per monitor → window title → spacer → tray → battery (percentage + icon) → Hints → notifications → Control Center → date/time → session. Controls are 30 px, centered status icons 16 px, and the logo 18 px. Network and volume controls live in the Control Center.
- QML tray menus with rounded corners, neutral backgrounds/borders, hover, submenus, checkboxes, and disabled actions; Esc or an outside click closes the menu.
- Panels open with a short slide from the bar (side panels) or a scale from the centre (dialogs) and close with a quicker fade; Control Center sub-panels and the network details view push sideways; notification toasts slide in and out from the right; expandable sections grow open, pressed buttons sink slightly, the launcher selection glides, and icons cross-fade when their state changes; windows pop in and out, tiling reflow glides on a spring, and workspaces slide with a fade. See [Motion](configuration.md#motion).
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
| `Super + A` | AI assistant (Claude Code; hold `Space` to dictate) |
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
| `Super + Ctrl + W` | Next wallpaper of the current theme |
| `Super + Ctrl + T` | Theming: theme, wallpaper, font, icons |
| `Super + Ctrl + N` | Do Not Disturb on/off |
| `Super + Ctrl + K` | Keep awake on/off |
| `Super + Ctrl + C` | Clipboard / history |
| `Super + Ctrl + R` | Screen recording |
| `Super + D` | Show the dock with keyboard navigation / hide it |
| `Super + Alt + 1`…`9` | Open or focus the Nth dock item |
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

## Dock

A dock sits at the bottom of every monitor, hidden by default and reserving no space. Push the pointer against the bottom edge (a 3 px strip that leaves 64 px free at each corner for the hot corner and gestures) and it slides up after 120 ms; it slides away 400 ms after the pointer leaves. It also shows by itself on an empty workspace, for about a second after `Super + Alt + N`, and for about three seconds when a window asks for attention (its icon pulses and its dot turns red). It never shows over a fullscreen window or during the Hyprspace overview.

Pinned apps come first, then a separator and the other running apps, grouped by desktop entry (the `zen` window class belongs to `zen-browser`); apps without a desktop entry keep their window class and a generic icon. A dot marks running apps and widens for the focused one. Icons near the pointer magnify (up to 1.4× under it) and the dock widens around them. Left click opens a pinned app, focuses a running one (a window on the current workspace first), or, when it is already focused, cycles through its windows; middle click opens a new instance.

Right click opens the app menu: its windows (choose one to focus it; the focused one is marked), the actions its desktop entry declares (for example a private window), New window, Pin to dock / Unpin from dock, and Close, or "Close all N windows" with a confirmation. Arrow keys, Enter and Esc work in the menu; an outside click closes it.

Pins can also be changed by dragging: hold a pinned icon and move it at least 6 px, then drop it on another slot to reorder, or lift it more than an icon above the dock until it fades and says "Remove", and release to unpin it. In the launcher (`Super + Space`), pinned apps carry a pin mark on the right; `Ctrl+P` or a right click pins or unpins the selected app.

`Super + D` shows the dock on the focused monitor and gives it the keyboard: Left/Right (or Tab) move a selection ring with the app name, Home/End jump to the ends, Enter opens or focuses the app, Shift+Enter opens a new instance, the Menu key or Shift+F10 opens the app menu (Esc there returns to the dock), and Esc or `Super + D` hides the dock and keeps it down, even on an empty workspace, until the pointer visits it. Activating an app or clicking outside the dock ends keyboard mode. `Super + Alt + 1`…`9` activate items by position without taking the keyboard. `desktop-shell dock show|hide|toggle|launch N` does the same from scripts.

## Do Not Disturb, Keep awake and notification history

`Super + Ctrl + N` and `Super + Ctrl + K` toggle Do Not Disturb and Keep awake, the same switches as in the Control Center. An OSD shows the new state. It appears even with Do Not Disturb on, since it is the shell's own feedback rather than a notification. Both states are saved, so they survive shell restarts and logins until changed. With Keep awake on, the computer does not suspend on idle, and the bar shows the cup icon.

The notification center keeps up to 50 notifications from the last 7 days across shell restarts. Those from before a restart are marked **Archived**: they can be read and deleted, but their action buttons are gone, because the sending application bound them to the previous notification server. **Clear all** removes live and archived ones.

## Theming

`Super + Ctrl + T` opens the Theming panel. `Ctrl+Tab` / `Ctrl+Shift+Tab` (or `Ctrl+PgDown` / `Ctrl+PgUp`) switch tabs, arrows move within a tab, Enter applies, and Esc closes.

**Tabs**
- **Theme:** a card per theme with a small mock-up of its surfaces, text and accent, plus its terminal colours; the current one is marked. Choosing one switches colours at once, and the theme's wallpaper follows.
  - **Bar: Shaded · Transparent** sets the bar style. Transparent drops the dark gradient, and the bar stays transparent. Only its text and icons change colour, taking whichever of the theme's light and dark text contrasts more with the wallpaper under the bar. The layer stays blurred.
  - A double-click on an empty part of the bar switches the style too.
  - **Window corners** (0–24) and **Border** (none, 1–4 px) set the window rounding and border width. The border colours come from the theme: its accent for the focused window, its border colour for the others.
  - The corners apply to the whole desktop, scaled from the design size of 16: windows, shell panels, cards, buttons, chips, the dock, OSD, tooltips, menus and the lock screen password field. Small dots and slider tracks stay round.
  - **Dynamic**, the last card, generates a theme from the current wallpaper with matugen and switches to it; its mock-up sits on that wallpaper. Choosing it again generates again. While it is the current theme, every wallpaper change (the gallery, Custom…, `Super + Ctrl + W`) generates it anew, and `Super + Ctrl + W` cycles the folder of the image it came from. Without matugen the card shows the install command instead.
  - **Dynamic mode: Auto · Dark · Light** and **Palette: Tonal spot · Vibrant · Expressive · Fidelity · Neutral** (shown once matugen is installed) shape the generated theme. Auto lets the image decide between light and dark. A change regenerates at once when the dynamic theme is active.
- **Wallpaper:** thumbnails of the current theme's set, with the current one outlined. For Graphite these are the images in the local wallpaper folders.
  - Thumbnails are cached JPEGs (`~/.cache/desktop-theme/thumbs/`), so WebP and very large images preview too.
  - Images that are not downloaded yet show a placeholder; "Download wallpapers" fetches them, and thumbnails appear as they arrive.
  - **Custom…** opens the file picker (`Super + Shift + W`).
  - A pick from either is remembered for the theme.
- **Font:** the installed interface and monospace families, each written in itself, plus a size from 9 to 13 and a preview. "Theme default" goes back to the theme's font.
  - **Use the monospace font everywhere** gives the interface the monospace family as well (shell, GTK, Qt, hyprlock, Kitty).
  - **Other installed family…** takes any installed family by name, even one the lists leave out; the name is checked with fontconfig first.
  - **Open fonts folder** opens `~/.local/share/fonts`; after adding fonts there, **Rescan** refreshes the font cache and the lists.
- **Icons:** the installed icon packs with five sample icons each, drawn from that pack. "Theme default" goes back to the theme's pack.
  - **Shell icons: Desktop · Icon pack** sets where the glyphs of the bar, Control Center, OSD and panels come from. Desktop uses the bundled set. Icon pack uses the pack's symbolic icons, tinted like the bundled ones, and keeps a bundled glyph wherever the pack has none.
  - **Other installed icon theme** takes a theme by its folder name, and **Open icons folder** opens `~/.local/share/icons` for packs installed by hand.

Font, size, icon pack, shell icons and bar style are your preferences: they apply to every theme. GTK applications follow them at once, and Kitty reloads. Qt applications follow them when reopened. The shell reads fonts and icons only at start, so after a font or icon change the panel shows a **Restart shell** banner. The restart reopens the panel on the same tab and clears the notification history.

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
