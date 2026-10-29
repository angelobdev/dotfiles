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
- [x] Motion, phase 2: sideways push/pop between the Control Center and its sub-panels (`ShellState.push()`/`back()`) and between the network list and details; notification toasts in a `ListView` over a `ScriptModel` with slide-in/out and animated reflow (delegates are reused, so remaining toasts no longer restart their expiry timers when one leaves); OSD rise.
- [x] Motion, phase 3: `Expander` for Control Center sections with animated chevrons, width-aware press feedback on `ActionButton`, gliding launcher selection, notification-center add/remove/reflow transitions, and icon cross-fades in `Icon` (the outgoing glyph is loaded only during the fade). The clipboard list keeps its colour transition (a moving highlight would sit under the delete button) and the network list is left static because scans reorder it constantly.
- [x] XWayland fractional scaling: X resources from the focused monitor (`Xft.dpi` 160, Adwaita cursor theme, `Xcursor.size` 40 at 1.667) applied at session start and on monitor hotplug through `desktop-xwayland`; global `XCURSOR_SIZE` removed; Steam back to the monitor's own fractional scale; `desktop-aseprite` Steam launch option sets Aseprite to 200% × the monitor scale, rounded (3 on the built-in panel, 2 on an unscaled display) and enables its native cursor when unset.
- [x] Physical HDMI hotplug verified with Philips FTV: monitor, bar, and brightness list removed/restored without restarting the shell. I²C permissions applied through ddcutil's udev rules.

## Next developments

Planned on October 29, 2026 after a research review (Omarchy 4.x, end-4, noctalia, caelestia, Claude Code docs). Implementation order: AI assistant → Dock → Theming.

### AI assistant (Claude Code)

- [x] `SUPER + A` toggles a floating Kitty window (`--class desktop-ai`) running `claude` on the special workspace `ai`; launched on first use, kept alive afterwards.
- [x] Hold-Space dictation through Claude Code voice: `hold` mode passed with `--settings` to the assistant session only, language from the locale (`assistant.language`) or `DESKTOP_AI_LANGUAGE`; claude.ai login present, no `ANTHROPIC_API_KEY`, `arecord` available as recorder fallback. Confirmed by the user with the built-in microphone.
- [x] Hints, i18n and docs (interface, integrations, troubleshooting).
- [ ] Optional: global dictation into any app (whisper.cpp + wtype, Voxtype-style press/release bind).

### Dock

- [x] Phase 1: `dock/DockWindow.qml` `PanelWindow` per screen (namespace `desktop-dock`, bottom anchor, `exclusiveZone: 0`). Always auto-hide: the surface stays mapped, a 3–4 px input strip away from the corners reveals it, it slides away on leave after a short delay, never reveals over fullscreen windows and follows `BarVisibility` during Hyprspace.
- [x] Phase 1: pinned apps (desktop-entry IDs), separator, running apps grouped by `appId` (`ToplevelManager`, `DesktopEntries.heuristicLookup`, icon fallback). Click focuses or launches, middle-click opens a new instance, running/active indicators. Pins from `Config.dockPinned`; state-backed pin/unpin moves to phase 2.
- [x] Phase 1: IPC `dock(action)` (show/hide/toggle) and `launch(n)` behind `desktop-shell dock …`; `SUPER + D` toggles, `SUPER + ALT + 1-9` launches/focuses the Nth item. Blur layer rule and Hyprglass namespace; Theme motion tokens and `reduceMotion`.
- [x] Phase 2: hover magnification (1.4×, `dockMagnification`), context menu (windows, desktop actions, new window, pin/unpin, close / close all with confirmation), pins persisted in `~/.local/state/desktop-shell/dock.json`, drag to reorder and drag off to remove, launcher pinning (mark, `Ctrl+P`, right click), `Super + D` keyboard navigation (separate `DockKeyboard` surface), `desktop-ai.desktop` with its own icon (Figma "App icons").

### Theming system (hand-authored themes + dynamic custom theme)

- [x] Phase 1, pipeline: `theme.py` renders `themes/<id>/theme.json` through `templates/*.tpl` into `~/.local/state/desktop-theme/` (Quickshell JSON watched live, Hyprland `config/theme.lua`, Kitty `include`, GTK relative `@import`, qtXct `color_scheme_path`, hyprlock `--config` from `desktop-power`), GSettings from the theme; `desktop-theme apply|set|list`. Graphite ported with no visual change (byte-identical renders, screenshots); `test_theme.py` guards the fallbacks.
- [x] Phase 2, themes: Catppuccin Mocha (mauve), Tokyo Night (blue), Gruvbox (yellow), Everforest (green) from the projects' Kitty ports; derived shell/Qt/Hyprland values; WCAG contrast tests. VS Code follows (`workbench.colorTheme` and the preferred theme for the mode, extensions installed), btop gets a generated `desktop` theme (Graphite included), Zen follows `color-scheme`.
- [x] Phase 3, wallpapers: eight per theme (Omarchy backgrounds plus community collections), pinned URLs with sha256, downloaded on demand into `~/.local/share/desktop/wallpapers/<theme>/`; theme switches apply the remembered or first wallpaper in the background; `Super + Ctrl + W` / `desktop-wallpaper --next` cycles the set; Graphite uses the local collections.
- [x] Phase 4, "Theming" panel (one Quickshell panel replacing the separate theme picker and gallery):
  - [x] Theme: list of themes with a palette preview (surfaces, accent, ANSI swatches), applied live through `desktop-theme set`.
  - [x] Wallpaper: gallery of the current theme's set (download progress from `theme.py fetch`) plus "Custom…" for any image (the existing picker or a file chooser); the choice is remembered per theme.
  - [x] System font: research how to switch the UI and monospace fonts across Quickshell, GTK (GSettings `font-name`), Qt (qtXct `[Fonts]`), Kitty and hyprlock; which installed families to offer (fontconfig, `fc-list`), size, and whether fonts belong to the theme or override it.
  - [x] Icon pack: research switching the application icon theme (GSettings `icon-theme`, qtXct `icon_theme`, Quickshell `iconPath` lookups); which installed themes to offer (Papirus variants, Adwaita, …), Papirus folder colours per theme, and whether the pack belongs to the theme or overrides it.
  - [x] Shortcut (`SUPER + CTRL + T`), i18n, docs.
  - [x] Round 2 (user feedback): cached JPEG thumbnails (WebP previews), one monospace font everywhere, shell glyphs from the icon pack (`IconNames.js`), custom installed font/icon theme by name with folder and rescan buttons, transparent bar (double-click on the bar or the Theme tab).
  - [x] Round 3: transparent bar text and icons take whichever theme text colour has the higher WCAG contrast over the strip under the bar (cover-cropped at the monitor size), the bar itself staying transparent; font and icon changes show a "Restart shell" banner instead of restarting by themselves.
  - [x] Window corners (0–24) and border width (0–4 px) in the Theme tab; border colours from the theme (accent active, border inactive); the corners also scale every shell radius (`Theme.corner`) and the lock screen field.
  - [x] The border width and colours also frame the shell surfaces: panels and menus in the active colour, dock, OSD and notification popups in the inactive one; with no border they keep the thin stroke.
- [x] Phase 5, dynamic theme: `theme.py generate` turns matugen's JSON for the wallpaper into `~/.config/desktop/themes/dynamic/theme.json` (Material roles → palette, standard terminal hues harmonized toward the primary with a contrast floor, nearest GSettings accent) and applies it through the same templates; Dynamic card plus mode (Auto · Dark · Light) and palette style chips in the Theme tab; `DynamicTheme.qml` regenerates on every wallpaper change while it is current; light themes shade the bar with their background; installation docs updated.

### Shell state and shortcuts

- [x] Persistent notification history (`Notices` → state file), so shell restarts keep it.
- [x] Persist "Keep awake" (`Idle.keepAwake`) and "Do Not Disturb" (`Notices.quiet`) across shell restarts and logins (state file read at start).
- [x] Keyboard shortcuts to toggle "Keep awake" (`Super + Ctrl + K`) and "Do Not Disturb" (`Super + Ctrl + N`) with a state OSD, listed in Hints.

### Control Center switches

- [ ] The final switches in a 2×2 grid: Do Not Disturb, Keep awake, Rotation lock and a new Night shift (hyprsunset, which `hyprctl hyprsunset` already drives), each a compact square tile with icon, name and state.

### Touchscreen support (epic)

Target: HP OmniBook Ultra Flip (2-in-1). ELAN 2513 touchscreen and stylus, `SW_TABLET_MODE` on "Intel HID switches", accelerometer through iio-sensor-proxy (active). Hyprgrass gestures: `swipe`, `edge`, `longpress`, `pinch`, `tap`; edge swipes from bottom/top and three-finger swipes are taken. Agreed design (review 2026-10-29):

- [x] Phase 1, tablet mode and rotation: Hyprland `switch:on/off` binds on the tablet switch set a shell `tablet` state (IPC, `desktop-shell status`). A rotation helper follows SensorProxy only in tablet mode and rotates the output together with touch and stylus input; rotation lock in the Control Center and in the helper menu, persisted like Keep awake. Verified on the OmniBook in all four orientations by the user.
- [ ] Phase 2, floating helper ("do everything" button, AssistiveTouch-like): a round button over every app, dragged by finger or mouse, snapping to the nearest side edge, position remembered per monitor and orientation, dimmed and half tucked when idle. Tap opens a grid of large actions (Keyboard, Apps, Dock, Control Center, Notifications, Overview, Workspace ←/→, Rotation lock; configurable like dock pins); long press runs a configurable quick action. Full-screen overlay with an input mask and no keyboard focus. Summoned with a three-finger long press (Hyprgrass) and IPC; shown automatically in tablet mode, hidden back in laptop mode.
- [ ] Phase 3, on-screen keyboard in Quickshell: Italian layout, accents on long press, numbers/symbols page, Shift/Caps, repeating Backspace, arrows, optional Esc/Tab/Ctrl/Alt row. Docked at the bottom (full width, exclusive zone so windows shrink above it) by default, with a key that makes it floating and draggable. Never takes focus; keys go through a persistent helper on `zwp_virtual_keyboard_v1` with the `it` keymap (python3-pywayland or a small C helper, decided at implementation). Opened from the floating helper.
- [ ] Phase 4, automatic keyboard: the helper also registers as `zwp_input_method_v2`, used only as a focus signal: activate shows the keyboard, deactivate hides it, and the content purpose picks the layout (digits, email, password, terminal). Keys still go through the virtual keyboard. Works with text-input-v3 clients (GTK, Firefox/Zen, Qt6); Electron/Chromium need `--enable-wayland-ime`; Kitty to be checked. Manual opening stays available everywhere.
- [ ] Phase 5, touch-friendly shell: a touch scale (larger hit targets and spacing for bar, dock and panels) switched on in tablet mode; long press for context menus (dock, launcher); swipe to dismiss notifications.
- [ ] Phase 6, physical testing on the OmniBook in both postures (includes the open "physical testing of touchscreen gestures" item), and docs.

### Codebase review

- [ ] Full review of the repository once the current work is done: correctness, dead code, consistency of services/helpers, docs accuracy, i18n coverage and tests.

### Hardware

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
