# ROADMAP

Status updated on October 17, 2026, verified against repository files.
Completed items indicate features present in the code; outstanding hardware checks are listed separately.

## Current direction

- Follow this roadmap for future development.
- Retain the graphite palette; the October 13 request introduces glass blur through Hyprglass without returning to the earlier light macOS restyling request.
- Keep the custom desktop interface in Quickshell, with Hyprland Lua and GNU Stow packages.
- Keep code, comments, documentation, and default labels in English; Italian text belongs only in `i18n/it_IT.json`.

## Completed

### Desktop foundation

- [x] Dotfiles repository organized into Stow packages, with simulation, conflict backups, and verification scripts.
- [x] Modular Hyprland Lua configuration: monitors, input, appearance, rules, shortcuts, session, and local overrides.
- [x] Session startup/management through `desktop-shell` and `desktop-session`.
- [x] Basic XWayland support and GTK/Qt backend fallback.
- [x] hypridle, hyprlock, and hyprpaper integration; locking, DPMS, and automatic suspend configured.
- [x] Hyprlock: modern graphite layout, PAM password, and parallel native fingerprint authentication; Synaptics reader acquired and right-index verification started in the headless test.
- [x] Quickshell reorganized by function (`bar`, `controlcenter`, `panels`, `notifications`, `session`, `osd`), with shared components/services and updated imports.
- [x] ChatGPT/Nautilus blurred-text investigation: both reported instances were XWayland; native Wayland startup verified with isolated instances, local launchers corrected, and session environment updated. User applications need restarting to apply the backend.

- [x] Steam HiDPI startup: 1:1 XWayland rendering and a monitor-aware Steam launcher/desktop override and renderer-scoped CEF initialization workaround (visible 2× UI verified); optional per-game gamescope wrapper with native physical resolution, lower render resolution, FSR, and FPS controls.

### Cursor and terminal

- [x] Complete Kitty 0.47.1 configuration: 470 options, commented defaults/mappings, 33 existing custom values retained; native parser reports no errors.
- [x] Fastfetch 2.68.1 configuration in a dedicated Stow package: Fedora logo, neutral palette, system/session/hardware sections, and display, battery, and cursor modules; execution verified.

### Bar and navigation

- [x] 38 px top bar with transparent/translucent background, Fedora logo, and application menu.
- [x] Occupied and active workspaces represented by pills, highlighting active and urgent states.
- [x] At least two pills per monitor, empty placeholders with globally unique IDs, and wheel/touchpad navigation across the workspace area's full height.
- [x] Window title, spacer, tray, battery percentage/icon, Hints, notifications, Control Center, date/time, and power menu.
- [x] QML tray menus with matching background/border, rounded corners, hover, submenus, anchoring below the icon on its monitor, and keyboard navigation; Esc and outside clicks close the menu.
- [x] Centered status icons and native tooltips below buttons; bar buttons no longer retain a highlight from mouse focus after panels close, while keyboard and panel focus indicators remain available.
- [x] Launcher with search, application icons, left-aligned titles, and keyboard navigation.
- [x] Hints panel with search, categories, and shortcuts/descriptions read from actual Hyprland bindings.
- [x] Keyboard-accessible session menu with lock, suspend, logout, reboot, and shutdown; confirmation for the relevant actions.
- [x] Monthly calendar with day selection, keyboard navigation, indicators, and an agenda from GNOME/Online Accounts calendars through Evolution Data Server; recurring, all-day, multi-day, and time-zone-aware events, without account modifications.
- [x] OSDs for volume, speaker/microphone mute, and brightness, with level/device, configurable timeout, and positioning on the affected monitor; detects changes even with panels closed.
- [x] QML wallpaper picker on `Super + Shift + W`, with previews and persistence across sessions.
- [x] HyprCapture editor bindings for areas (`Super + Shift + S` / `Print`) and monitors (`Super + Shift + Alt + S` / `Alt + Print`); scratchpad bindings and shortcut conflicts removed.

- [x] XF86 MPRIS play/pause, pause, next, previous, and stop bindings through the native Quickshell media service, following the selected player and capabilities. Omnibook F1/F2/F10/F11 events captured; calculator and Control Center aliases configured, pseudotiling moved to `Super + Ctrl + P` to avoid the firmware `Super + P` conflict.

### Compositor plugins

- [x] Dedicated Lua configuration with API availability guards, supporting startup without plugins.
- [x] Five plugins compiled and loaded in the isolated session: Hyprspace, Hyprgrass, Hyprglass, hypr-hot-edge, and HyprCapture.
- [x] Local hyprpm packaging with pinned upstream revisions, matching COPR RPM headers, and a Lua 5.4 build patch for hypr-hot-edge; manifest names aligned with runtime names.
- [x] Top-left hot corner connected to Hyprspace, rearming on exit, with no keyboard binding to open it; opening/closing the internal workspace verified in an isolated session.
- [x] Hyprgrass touchscreen gestures for workspaces, overview, launcher, and controls; touchpad gestures retained.
- [x] Neutral Hyprglass preset with light refraction, no chromatic aberration or center distortion, applied to translucent surfaces and Quickshell panels.
- [x] Screenshot bindings migrated to HyprCapture; test-monitor PNG capture verified. RPM/ABI version guard prevents autoload of stale builds after COPR updates.
- [x] Hyprspace: extra 200 px reservation removed, bars/overlays excluded from previews; invisible bars release space and input while keeping surfaces available for restoration. 38 → 0 → 38 verified on the affected monitor in an isolated session.
- [x] Top-left hot corner toggles opening/closing after rearming on leaving the corner.
- [x] Native HyprCapture editor on all four screenshot shortcuts; Hints groups them under “Screen capture”, displays “Print”, and updates bindings on Hyprland reload while open.
- [x] HyprCapture overlay moves across monitors; virtual outputs at scales 1.667 and 1 verified with native 2880×1800/1920×1080 PNGs and an editor toolbar on the fractional-scale display.
- [x] Installation into hyprpm's protected cache and loading in the main session: all five enabled and loaded; autoload verified with `desktop-plugins reload`, configuration has no errors.
- [ ] Physical testing of touchscreen gestures, hot corners on both monitors, and glass appearance during daily use.

### Panels and Control Center

- [x] Modular Control Center with order, visibility, and dimensions configurable in `Config.qml`.
- [x] Network and Bluetooth subpanels at the top right, with return to Control Center and shared headers.
- [x] Wi-Fi: enable/disable, scanning, network search/selection, connection, and Personal-network password prompts; enterprise networks use preconfigured profiles.
- [x] Bluetooth: adapters, enable/disable, scanning, pairing through a BlueZ `KeyboardDisplay` agent with PIN/passkey, explicit confirmation/authorization, cancellation/timeout, connection/disconnection, and battery. Protocol verified on an isolated bus; physical pairing still needs UI testing.
- [x] Brightness: main slider, expandable section for other monitors, and configurable backlight/DDC backend mapping.
- [x] Immediate brightness slider updates and writes while dragging, with stale-reading and error handling.
- [x] MPRIS Control Center controls: title/artist, previous, play/pause, next, position, and player selection; capabilities and disappearing players handled through native Quickshell APIs.
- [x] Audio: volume slider/percentage, mute, input/output selection, and microphone level; expandable Control Center section and dedicated panel.
- [x] Do Not Disturb in the Control Center, with a right-aligned switch.
- [x] Notification center at the top right: in-memory history, actions, and Do Not Disturb/Clear all icons to the right of the title.
- [x] Notification popups with icons, limited safe markup, left-click for the default action, and right-click to hide while retaining history; Activate/Delete/Hide buttons removed from popups. Secondary actions and notification-center controls retained. Do Not Disturb silences popups.
- [x] Battery panel at the top right: percentage, power, energy, estimated times, and power-profile selection with icons.
- [x] Power-profile indicator in the bar's battery block: leaf for Power Saver, lightning bolt for Performance, and no extra icon for Balanced; current-profile tooltip and system-service updates.
- [x] Text buttons retain padding; compact variant removes padding for chevrons and narrow audio controls. Individual notification deletion is red, aligned with the title, and uses the same text size.
- [x] Shared side-panel dimensions and 22 px back/close icons.
- [x] Keep awake toggle connected to a Wayland `IdleInhibitor` on the bars: independent of Control Center visibility, with no additional packages.
- [x] Quickshell clipboard manager with search, keyboard navigation, text/images, pause, and deletion; cliphist history and XWayland bridge verified in both directions.

### Integrations and documentation

- [x] Multilingual Quickshell/helpers: nested Italian/US English JSON catalogs with semantic keys independent of text, selection from `/etc/locale.conf` (`LC_MESSAGES`/`LANG`), English fallback, live text updates, and localized calendar/clock/number formats. Hints translates categories and known descriptions; automated catalog/parameter checks. Active shell verified in `en_US`, both languages tested in isolated QML instances.
- [x] English documentation, filenames, comments, binding descriptions, default labels, helper errors, and test fixtures; Italian content confined to `i18n/it_IT.json`.
- [x] Udiskie Stow configuration and session autostart without a tray icon; automatic mounting of removable UDisks devices, Quickshell notifications, and Nautilus browsing. GVfs/AFC iPhone support with usbmuxd/libimobiledevice; pairing validation and GVfs AFC mounting verified on the connected iPhone after accepting the trust prompt.
- [x] Quickshell Polkit authentication agent.
- [x] Consistent dark glass theme: shared graphite palette across Quickshell, GTK 3/4, and Qt 5/6; translucent shell surfaces with opaque text and a neutral accent; applications retain native geometry and may use their own styling.
- [x] Matching Kitty theme, Adwaita Mono, translucent background, and ANSI palette.
- [x] Neutral primary and borderless Hyprland windows, inactive opacity, and blur.
- [x] Electron Wayland environment and explicit Wayland/X11 wrapper; VS Code verified on both backends with temporary profiles, existing Zen window identified as native Wayland.
- [x] XDG portals: Hyprland/GTK routing, environment import before startup, and a custom Quickshell sharing picker.
- [x] Screen sharing through ScreenCast/PipeWire and monitor/area recording through wf-recorder, with QML panel, audio selection, bar indicator, and video saving; real portal test and recording of a dedicated window, with the specific web app test still outstanding.
- [x] Concise README and separate `.claude/docs/` guides for installation, interface/shortcuts, configuration, integrations, and troubleshooting; updated for pairing, MPRIS, calendars, and DDC/CI results.
- [x] Icon pack redesigned in Figma ([Desktop Icons](https://www.figma.com/design/FYQsa6b0razfxqGI4Q9rG5)) and exported to `assets/icons/`: filled macOS-like style, battery fill levels (`battery-100/75/50/25/0`, replacing `battery`/`battery-low`), Wi-Fi strength (`wifi-1`, `wifi-2`), gauge icons for power profiles, toggle-style Control Center icon. Bar, battery panel, network tile, and network list select the new icons.
- [x] Network panel, phase 1: current-connection card, Ethernet devices with cable state and link speed, and a details view for saved networks (signal/band, IP, router, DNS, IPv6, MAC; reveal/copy/QR-share the Wi-Fi password; automatic connection; metered; Automatic/preset/custom DNS; disconnect; forget). Settings Quickshell does not expose go through `network.py` (nmcli; QR via the installed libqrencode). Fixed the Control Center tile showing the Ethernet icon while disconnected (`DeviceType.Ethernet` does not exist). Fixed centred icon+text `ActionButton`s overflowing to the right (the centering fillers added spacing not counted in the implicit width).
- [x] Network panel, phase 2: manual IPv4 (address/prefix and router, validated), MAC address mode (default, private per network, rotating, fixed), joining hidden networks (password passed on stdin to `nmcli connection edit`, failed profiles removed), and toggles for NetworkManager VPN/WireGuard profiles. Shared `ChoiceChips` component for single-choice pills; `vpn` icon added to the Figma pack.
- [x] Network panel, phase 3: personal hotspot (generated password set through `nmcli connection edit` on stdin; reveal/copy/QR through the shared `NetworkPassword` row), Tailscale state and up/down in the VPN section, "Advanced settings…" and per-profile "Edit in Network Connections…" opening `nm-connection-editor`; one `extras` poll every 4 s while the list is open. `hotspot` icon added to the Figma pack.
- [x] Motion, phase 1: restrained Hyprland animations (shared `out`/`accel`/`inout` curves, critically damped `move` spring for tiling reflow, popin windows, slidefade workspaces, tuned fades) and open/close animation for every Quickshell panel through `Overlay` (slide from the bar or scale from the centre; closing releases focus and input). Theme motion tokens and `Config.reduceMotion`; compositor animations off for `desktop-overlay`/`desktop-osd`.
- [x] Physical HDMI hotplug verified with Philips FTV: monitor, bar, and brightness list removed/restored without restarting the shell. I²C permissions applied through ddcutil's udev rules.

## Next developments

- [ ] Motion, phase 2: push/pop transitions between the Control Center and its sub-panels and between the network list and details; notification popups sliding in/out with animated reflow; OSD rise.
- [ ] Motion, phase 3: animated expanders in the Control Center, list add/remove transitions (notifications, clipboard, networks), launcher selection glide, pressed state on buttons, icon cross-fades.
- [ ] Complete a successful DDC/CI test (read, minimal change, restore) with a display that responds to the protocol. The connected Philips FTV is identified on bus 14 but responds to neither VCP 10 nor capabilities, even after applying permissions and increasing timings. GNOME's built-in control may use software brightness; this does not confirm the display's DDC/CI support.

## Review follow-ups (behavior changes awaiting approval)

Found during the October 27, 2026 repository review. Checked items were approved and applied the same day; the rest still change runtime behavior and await a decision.

- [x] Screen-share picker path: the systemd user `PATH` had lost `~/.local/bin` (the login-time import works when re-run, so it was likely reset later), leaving xdph unable to find `desktop-portal-picker`. `xdph.conf` now uses `~/.local/bin/desktop-portal-picker` (xdph runs it through `/bin/sh`). A real share from the calling web app still needs a manual test.
- [x] Power menu: `Overlay` and `PowerMenu` both handled Escape, so Esc closed the menu instead of cancelling a pending confirmation. `Overlay.closeOnEscape: false` now lets the menu cancel first, then close.
- [x] Share picker: the keyboard cursor is now the selection (highlight, Enter and Share all use `currentIndex`, like Launcher/Clipboard); the first source is preselected.
- [x] Battery panel: the level bar now draws the same track/accent fill as `ControlSlider` instead of relying on an ignored palette role.
- [x] Audio panel uses `ControlSlider` with accessible names; the microphone button shows the muted icon when muted.
- [x] Spacing: `Theme.panelPadding` (16, side panels) and `Theme.dialogPadding` (22, centred dialogs); Clipboard, Recording and the power menu now follow them, and the Control Center uses the shared `PanelHeader`. Fonts were already uniform at runtime (qt5ct default is Adwaita Sans).
- [ ] Environment import runs twice concurrently (`session.lua` and `desktop-session`) with different variable lists; consolidate into one call.
- [ ] Blur coverage differs: the layer rule blurs `desktop-bar` but not `desktop-tray-menu`, Hyprglass the reverse.
- [ ] `electron-flags.conf` is not read by any Fedora launcher and `UseOzonePlatform` is obsolete; keep or drop the package.
- [x] Workspace pills use `ScriptModel` keyed by `id`: delegates (button, tooltip window, timer) survive Hyprland updates and the width animation now runs.
- [ ] Lazy panels: deliberately not done. The shell uses about 200 MB RSS and 0.4% CPU, hidden panels gate their own work, and lazy loading would reset state that persists today (Control Center expanded sections, wallpaper directory) and needs first-open focus handling. Revisit if memory matters.
- [ ] Each `Icon` carries a `MultiEffect` for recolouring; `pragma ComponentBehavior: Bound` for `Bar`, `TrayMenu`, `WorkspaceStrip` after a runtime smoke test.
- [ ] Optional: `$HOME` in the qt5ct/qt6ct `color_scheme_path` (supported by qtXct, but the GUI rewrites it as absolute); subprocess timeouts in helpers; clearer messages for `StopIteration`/decode errors in the plugin scripts.

## Possible extensions identified

- [ ] Multi-distro installation support (add Debian and Arch).
