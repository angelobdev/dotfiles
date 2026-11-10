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
- [x] Scrolling past the last pill opens a new workspace on that monitor, unless the last one is empty; the assist button still stops at the ends.
- [x] Window title, spacer, tray, battery percentage/icon, Hints, notifications, Control Center, date/time, and power menu.
- [x] QML tray menus with matching background/border, rounded corners, hover, submenus, anchoring below the icon on its monitor, and keyboard navigation; Esc and outside clicks close the menu.
- [x] The screen-capture icon of the privacy indicator stays on through a recording: screencopy clients send an on/off pair per frame, so "off" waits 1.5 s.
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
- [x] Physical testing of hot corners on both monitors and glass appearance during daily use (touchscreen gestures: done with the touchscreen epic); confirmed by the user on 2026-10-29.

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
- [x] Public README with highlights, gallery and screenshots (English demo content, no personal data), MIT license, and the guides moved from `.claude/docs/` to `docs/`, one page per area.
- [x] GitHub Actions: `check.sh` in a `fedora:44` container on pushes to `main` and pull requests; `scripts/check-links.py` checks the links, headings and repository paths of the README and the docs through GitHub's own Markdown engine, and the doc paths in the catalogs.

## Next developments

Planned on October 29, 2026 after a research review (Omarchy 4.x, end-4, noctalia, caelestia, Claude Code docs). Implementation order: AI assistant → Dock → Theming.

### AI assistant (Claude Code)

- [x] Any coding agent through herdr (#2, part 1, 2026-11-07): with herdr installed the console is the Herdr app and the state comes from herdr-core (`hc events` / `hc ls`) for every agent it recognises; without it, Claude Code and its hooks as before. Next: choosing the agent without herdr, modular; an optional installer profile for herdr.
- [x] The Herdr app follows the desktop theme (#2, part 2, 2026-11-07): `theme.py` writes `themes/desktop.json` and the theme and fonts in its `settings.json`, keeping what is picked in Herdr; layouts with fixed colors (Terminals) need a copy without them.
- [x] Modular coding agents (#2, part 3, 2026-11-07, with GBSpada): one JSON descriptor per agent (`share/desktop/agents/`, the user's own in `~/.config/desktop/agents/`) read by `agents.py`; Settings → Assistant installs Claude Code, Codex and Antigravity CLI with their official installers and picks the primary agent `Super + A` starts (`aiPrimary`, `DESKTOP_AI_AGENT` wins). Claude Code keeps its hooks, status line and voice; other agents in the Kitty console show only running.
- [x] Installer profile for herdr (#2, part 4, 2026-11-07): `herdr` unpacks the Herdr app and herdr-core release archives (new manifest key `archives`: version, sha256 per architecture, `latest` for `pins`) into `~/.local` as herdr's installer does, only while missing (both update themselves); uninstall removes them; `pins` and the updates screen follow their releases. `desktop-ai` writes the desktop theme for Herdr before its first start (`theme.py herdr`).

- [x] `SUPER + A` toggles a floating Kitty window (`--class desktop-ai`) running `claude` on the special workspace `ai`; launched on first use, kept alive afterwards.
- [x] Hold-Space dictation through Claude Code voice: `hold` mode passed with `--settings` to the assistant session only, language from the locale (`assistant.language`) or `DESKTOP_AI_LANGUAGE`; claude.ai login present, no `ANTHROPIC_API_KEY`, `arecord` available as recorder fallback. Confirmed by the user with the built-in microphone.
- [x] Hints, i18n and docs (interface, integrations, troubleshooting).
- [-] Dropped on 2026-10-29: global dictation into any app (see the console epic below; Claude Code's own voice stays).

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
- [x] Phase 6, Glass (2026-11-03): Glass and Glass Light, macOS-style themes with mostly transparent surfaces and a refractive Hyprglass `liquid` preset (`glassStyle`, contour masks); a glass-settings page in the Theme tab tunes it per theme (`desktop-theme glass`); window gaps and screen margin join corners and border.
  - [ ] Try the glass page by hand and look at Glass Light on screen.
  - [x] Panels, the assistant console and translucent terminals showed a frozen copy of what was behind them: Hyprglass missed the changes, so `force_live_resample` is on for layers and `background_cache` is off for windows; measure its battery cost over a day and report it upstream if it holds.
  - [x] Top-level shell surfaces take exactly the window radius (aligned with windows and their glass); Glass popup notifications get a denser `shell.notice` fill.
  - [x] Dynamic palette styles dropped (they worked, but mostly moved the accent, and only showed while the dynamic theme was current); the mode stays.

### Shell state and shortcuts

- [x] Persistent notification history (`Notices` → state file), so shell restarts keep it.
- [x] Persist "Keep awake" (`Idle.keepAwake`) and "Do Not Disturb" (`Notices.quiet`) across shell restarts and logins (state file read at start).
- [x] Keyboard shortcuts to toggle "Keep awake" (`Super + Ctrl + K`) and "Do Not Disturb" (`Super + Ctrl + N`) with a state OSD, listed in Hints.

### AI assistant: console, state, usage and dictation (epic)

Designed on 2026-10-29 after Omarchy 4.5 (rc2 source: `default/hypr/qconsole.lua`, `shell/plugins/agents/`, `bin/omarchy-agent*`): Claude Code stays a TUI in Kitty (voice, permissions, slash commands intact), and its presentation and integration change. No native chat: it would lose voice and permission prompts. Decisions with the user: usage from the documented status line JSON only (no undocumented endpoint), dictation on the Copilot key (Right Alt is AltGr on the Italian layout), the bar icon opens a panel.

- [x] Phase 1, drop-down console: `special:ai` laid out under the bar by a Lua layout (60% of the usable height, twice as wide, side by side with two windows, above the docked keyboard), dimmed desktop, slide from the top; closes on a click or tap outside (a Quickshell Bottom-layer catcher) and on a workspace change; apps launched while it is open go to the normal workspace; `Super + Shift + A` moves the active window in or out.
- [x] Phase 2, state and notifications: Claude Code hooks and a status line passed with `--settings` feed `agent.py` (state file in the runtime dir, usage file in the shell state); `services/Agent.qml`, a bar icon with a state dot, notifications with Open when the console is hidden (permission needed, finished).
- [x] Phase 3, agent panel: plan (Max 5x), state, 5-hour and 7-day meters with reset times, model and context, Open/Hide console.
- [-] Dropped on 2026-10-29 (not needed; Claude Code's own hold-Space voice stays in the console). Phase 4, system dictation: hold the Copilot key (tap toggles), `pw-record` + whisper.cpp (a small helper against Fedora's `libwhisper`), text committed through the on-screen keyboard's input method (clipboard fallback); a microphone on the on-screen keyboard and in Assist.

Earlier findings (Claude Code docs, 2026-10-29), kept for a possible native widget later:
The assistant lives in a Kitty window on the special workspace `ai` (`Super + A`); the user does not like how the special workspace behaves, so the interaction is to be redesigned either way. Findings (Claude Code docs, 2026-10-29):
- `claude -p` uses the claude.ai subscription login (no API key; `ANTHROPIC_API_KEY` must not be in the environment, as it wins in `-p`; `--bare` ignores OAuth).
- `--input-format stream-json --output-format stream-json --verbose --include-partial-messages`: `system/init` (session id), `stream_event` text deltas, `assistant` / `user` (tool use and results), `result`. The raw stdin message shape is not documented as a contract (the Agent SDK uses `{"type": "user", "message": {...}}`).
- `--resume <session id>` continues the conversation across widget restarts.
- Permissions: in `-p` a call needing approval is denied unless a rule (`--allowedTools`), a hook or `--permission-prompt-tool` (an MCP tool, wire format undocumented) approves it.
- Voice (hold Space) exists only in the interactive TUI; a widget needs its own speech-to-text or keeps the terminal for voice.
- Policy: third-party products may not offer claude.ai login; a personal, undistributed UI is not addressed.

### Control Center switches

- [x] The final switches in a 2×2 grid: Do Not Disturb, Keep awake, Rotation lock and a new Night shift (hyprsunset, which `hyprctl hyprsunset` already drives), each a compact square tile with icon, name and state.

### Touchscreen support (epic)

Target: HP OmniBook Ultra Flip (2-in-1). ELAN 2513 touchscreen and stylus, `SW_TABLET_MODE` on "Intel HID switches", accelerometer through iio-sensor-proxy (active). Hyprgrass gestures: `swipe`, `edge`, `longpress`, `pinch`, `tap`; edge swipes were later dropped (not always recognised) for three- and four-finger swipes. Agreed design (review 2026-10-29):

- [x] Phase 1, tablet mode and rotation: Hyprland `switch:on/off` binds on the tablet switch set a shell `tablet` state (IPC, `desktop-shell status`). A rotation helper follows SensorProxy only in tablet mode and rotates the output together with touch and stylus input; rotation lock in the Control Center and in the helper menu, persisted like Keep awake. Verified on the OmniBook in all four orientations by the user. Floating windows refit on `monitor.layout_changed` (the assistant takes its 60% × 70% again, oversized ones shrink to 90%).
- [x] Phase 2, floating helper ("do everything" button, AssistiveTouch-like): a round button over every app, dragged by finger or mouse, snapping to the nearest side edge, position remembered per monitor and orientation, dimmed and half tucked when idle. Tap opens a grid of large actions (Keyboard, Apps, Dock, Control Center, Notifications, Overview, Workspace ←/→, Rotation lock; configurable like dock pins); long press runs a configurable quick action. Full-screen overlay with an input mask and no keyboard focus. Summoned with a three-finger long press (Hyprgrass) and IPC; shown automatically in tablet mode, hidden back in laptop mode.
- [x] Phase 3, on-screen keyboard in Quickshell: Italian layout, accents on long press, numbers/symbols page, Shift/Caps, repeating Backspace, arrows, optional Esc/Tab/Ctrl/Alt row. Docked at the bottom (full width, exclusive zone so windows shrink above it) by default, with a key that makes it floating and draggable. Never takes focus; keys go through a persistent helper on `zwp_virtual_keyboard_v1` with the `it` keymap (`osk.py`: the Wayland wire protocol in plain Python with a libxkbcommon keymap, no new packages). Opened from the floating helper.
- [x] Phase 4, automatic keyboard: the helper also registers as `zwp_input_method_v2`, used only as a focus signal: activate shows the keyboard, deactivate hides it, and the content purpose picks the layout (digits, email, password, terminal). Keys still go through the virtual keyboard. Works with text-input-v3 clients (GTK, Firefox/Zen, Qt6); Electron/Chromium need `--enable-wayland-ime`; Kitty reports its terminal as a text-input-v3 field (purpose `terminal`). Manual opening stays available everywhere.
- [x] Phase 5, touch-friendly shell: a touch scale (larger hit targets and spacing for bar, dock and panels) switched on in tablet mode; long press for context menus (dock, launcher); swipe to dismiss notifications.
- [x] Tablet review after the first physical test: the docked keyboard lifts the assistant (floating windows fit the usable area); gestures without edge swipes (three fingers as on the touchpad, four for windows and the overview); a window menu on the bar title (close, fullscreen, floating, move); the keyboard over the lock screen in tablet mode; `scripts/tablet-auth.sh` makes PAM skip the fingerprint reader in tablet mode.
- [x] Phase 6, physical testing on the OmniBook in both postures (includes the open "physical testing of touchscreen gestures" item), and docs. Done 2026-10-29 in both postures: gestures, dock, launcher, window menu, keyboard (automatic, hold-to-talk, over panels), rotation and the lock screen with the password field above the keyboard.

Backlog from tablet use (reported 2026-10-30):
- [x] Dock: a tap acts at once. Distances are measured in window coordinates (a touch warps the pointer, the magnification moved the press area, and a still finger seemed to travel); no magnification or hover tooltip in tablet mode; a finger sliding off does nothing; the menu opens at 0.5 s and a pin lifts at 2 s. Confirmed by the user.
- [x] Touch gestures no longer reach the app under them. `wev` and a test page in Zen showed a correct sequence (down, 100-400 ms of motion, cancel, never a click), yet the YouTube player reacted to it, so a Hyprgrass patch (upstream as `hold_touches` since #433) holds a new touch on a window for 40 ms and claims three or more fingers; two still fingers wait for the long press. Confirmed by the user in Zen and on YouTube. Never hot-swap the plugin: verification-log.md, 2026-10-30.
- [x] On-screen keyboard: one touch area over the keys, the key under the finger types on release, accents by long press and slide, two-thumb rollover. Confirmed by the user.
- [x] Research: prediction on the on-screen keyboard, as on iOS (2026-10-30, numbers in verification-log.md). Feasible at little cost: 50,000 words of FrequencyWords (CC-BY-SA-4.0, downloaded on demand like the wallpapers) add about 15 MB to `osk.py`, and a lookup takes 0.25 ms at worst. On text the list never saw, the next letter is in the top 3 about 72% of the time, three word suggestions save at most 28-31% of keystrokes, and a bounded growth of likely keys cuts simulated touch errors by 35-45%.
- [x] Upstream: `hold_touches` was merged into hyprgrass as [PR #433](https://github.com/horriblename/hyprgrass/pull/433) on 2026-11-07. `touch_as_pointer` ([PR #435](https://github.com/horriblename/hyprgrass/pull/435)) was closed on 2026-11-08: the maintainer wants it in Hyprland itself and would only reconsider if Hyprland refused it. Hyprland's [AI policy](https://github.com/hyprwm/.github/blob/main/policies/AI_USAGE.md) rejects AI-written logic even when it is disclosed and reviewed, so the user decided not to propose it there: `touch_as_pointer` stays a local patch, rebased at every hyprgrass update. Done 2026-11-08: the pin is `578e984` (#433 and the removal of deprecated options, before upstream stopped warping the pointer on touch, which `touch_as_pointer` relies on), the patch is `hyprgrass-touch-as-pointer.patch` (the diff of #435, 216 lines instead of 428), and `plugins.lua` sets `hold_touches` and `touch_as_pointer`. One upstream change: two fingers held still are now released by the long press timer (400 ms) instead of 100 ms after it.
  - [x] After the rebuild at the next login: tried by touch and confirmed working by the user (2026-11-08).
- [x] Prediction, phase 1: invisible hit areas (`osk/KeyScore.js`, `predict.py`), Italian and English lists merged and fetched on first use, off for password, pin, terminal, url, email, digits and the lock screen, totals of touch offsets for tuning. Confirmed by the user. First 100 real touches: spread 21 px across and 13 px down (3.8 and 2.4 mm), mean 6.6 px left of centre and 2.6 px low.
- [x] Prediction, phase 2: three suggestions in the strip, typed with ordinary keys so they work in every app, accents fixed, misspelled variants filtered. Tested end to end in a nested compositor and confirmed by the user.
- [x] Prediction, phase 3: learning from the user, word counts only, never from sensitive fields; a new word shows up after two uses, holding a suggestion forgets it. Tested end to end in a nested compositor, password and terminal fields included, and confirmed by the user.
- [ ] Prediction, later if wanted: next-word prediction needs pairs of words, no small free source has been assessed, and pairs learned locally would reveal fragments of sentences. The word typed is tracked locally, so moving the caret by touch leaves it stale until the next non-letter; `surrounding_text` could fix that where apps send it. There is no profanity filter: holding a suggestion removes it, one word at a time.
- [x] Kitty by touch: Kitty never asks for `wl_touch`, so touches reached nothing and a tap was no click either. The Hyprgrass patch now turns one finger into the pointer on such clients: a drag scrolls, a tap clicks. Tested in a nested compositor (6 of 6 on Kitty, 19 of 19 on touch clients) and confirmed by the user, gestures on Kitty and YouTube included.
- [x] Notification stacking from Omarchy 4.5 rc2 (`shell/plugins/notifications/`, same numbers: 10 px peek, 3.5% shrink, three cards drawn, 120 ms grace, 30 s hold-back): decks per app or site, hover to open, countdowns paused and new cards held while open. Added here: a tap opens a deck in tablet mode, a lone card keeps six lines, and the notification center groups too (Omarchy 4.5 has no center). Confirmed by the user.

### Installable by others (epic, decided with the user 2026-11-06)

Goal: anyone can install the desktop from GitHub on an ordinary laptop or desktop and keep it updated from the guided installer, while this OmniBook keeps behaving as it does today.

- [x] Overrides outside the repository: `~/.config/desktop/hypr.lua`, loaded last by Hyprland, and `~/.config/desktop/shell.json` for the options of `Config.qml`. The personal lines of `local.lua` (AI language, Zen, 1Password) move there.
- [x] Machine profiles: the OmniBook's values (tablet switch, panel scale, ELAN touch and pen, action keys) in `config/machines/omnibook_ultra_flip.lua`, chosen by DMI in `machines/init.lua`, instead of `local.lua` (removed) and `monitors.lua`. The stylus battery prefix stays a default of `Config.qml`, which matches nothing elsewhere.
- [x] `tablet.lua` split: display modes, lid and refresh per power source in a generic module that finds the internal panel (`eDP`, `LVDS`, `DSI`) and leaves the rules of other monitors alone; rotation and the tablet switch stay in the tablet module.
- [x] Touch only where there is touch: the on-screen keyboard's input method and the gestures in Hints only with a touchscreen.
- [x] Installer: a `tablet` profile apart from `hardware` (iio-sensor-proxy, libwacom, hid-sensors modules, tablet sign-in, ISH firmware), preselected by the TUI when it finds a touchscreen or a tablet switch. Hyprgrass built and loaded only with it (per-plugin selection: the bundle digest changes, the plugins rebuild once at the next login).
  - [x] Fingerprint sign-in on a laptop without `tablet`: `authselect enable-feature with-fingerprint` came with the tablet sign-in, so `hardware` alone installed fprintd without it (Workstation turns it on by itself, Server does not). The `auth` setting is now a list per unit: `hardware.fingerprint` asks for `with-fingerprint`, `tablet` for it and `custom/desktop-tablet`, and a removal undoes only what no unit that stays asks for (2026-11-10). Not tried on a machine without `tablet`.
- [x] Updates screen: after a pull, stow and a shell restart through the supervisor; the pin lines (zsh plugins, AUR, plugins) only for the maintainer, other installs get the pins with the repository.
- [x] Personal defaults: the keyboard layout from the system (`00-keyboard.conf`, `vconsole.conf`, else `us`) instead of `it`.
  - [ ] On-screen keyboard layouts besides Italian (`osk/layouts/`), picked to match `kb_layout`.
  - [ ] README and guides: say what a non-OmniBook gets (no tablet profile, panel found by name) once tried on another machine.

### Codebase review

- [x] Full review of the repository (2026-10-29): four read-only reviews (helpers and scripts, Hyprland and config packages, Quickshell services and IPC, Quickshell UI) plus a live UI and touch pass with screenshots of every panel in laptop, tablet and portrait. Findings below, by batch.

**A. Bugs** (no visible change unless noted)
- [x] `desktop-power lock` calls the shell (`keyboard locked`, `status`) and hyprctl with no timeout before hyprlock: a hung shell means no lock, and the held flock makes later requests exit silently. The tablet config Python under `set -e` also aborts the lock on a parse error. Add `timeout 2` and fall back to the themed config.
- [x] Notification history: ids restart at 1 in each Quickshell process, and archived entries whose `source` equals a live id are dropped on load, so the next reload after a restart empties the archive (confirmed in `notifications.json`: sources 21…1 twice). `arrived` also resets on reload.
- [x] Long-lived helpers are not restarted: `osk.py run`, `rotation.py watch`, `hyprsunset` (a dead keyboard helper drops every key, including on the lock screen). `NightShift.overrideUntil` is lost on reload.
- [x] `ToggleTile`: a tap on the Night shift chevron also toggles it (TapHandler passive grab over the MouseArea); a long press released late opens and closes the details.
- [x] Polkit and Bluetooth prompts map over an already shown on-screen keyboard and take every touch in tablet mode; re-raise the keyboard and subtract its area as `Overlay` does.
- [x] `share.qml`: exclusive focus and an autofocused field in tablet mode; through `Theme` it also creates `Tablet`, so a second `rotation.py watch` can run (racing `rotation.lua.tmp`).
- [x] `desktop-session`: a failing `desktop-theme` (for example a `current.json` naming a removed theme) stops hyprpaper, hypridle and udiskie from starting; `theme.py current()` should fall back to the default theme.
- [x] `Super + Ctrl + W` stays on Graphite's default wallpaper: `selection.json` holds the resolved path, `wallpaper_files()` the link (confirmed).
- [x] Window menu: "Floating" reads `lastIpcObject.floating`, stale without `Hyprland.refreshToplevels()`.
- [x] Dock menu origin and the `Super + D` keyboard hole assume the dock at the screen bottom; with the docked keyboard it sits higher.
- [x] `desktop_fit_floating()` shrinks floating windows larger than 95% even when they still fit.
- [x] Smaller ones: `desktop-theme window-style` not forwarded (documented); `themes(details)` raises KeyError for a theme without `ansi`; `vscode_settings('{}')` writes a trailing comma; `osk.py` dies on `struct.error`; `rotation.py` on `GLib.Error`; no lock between `generate` and panel commands in theme.py; `Tablet.sensed` kept across tablet sessions (double flip on re-entry); a field-opened keyboard stays after unlock; `NetworkInfo.loadProfile` drops a second request; `BarStyle.measure()` drops a change during a run; small state files can be written before their first read (`SessionState`, dock, assist, posture); `dock.json` watches its own writes (kept: hand edits apply live); `PopupMenu` resets its selection whenever entries rebuild; dock long press then drag starts a drag under the menu; workspace pills keep a focus background; IPC `theming(tab)` accepts any tab.

**B. Tablet experience** (behavior changes)
- [x] The docked keyboard stays open over panels and covers their bottom (Control Center switches, Hints, wallpaper picker, Theming, Clipboard, Session menu, the launcher list in portrait): close a field-opened keyboard when a panel without a focused field opens, and place dialogs and side panels in the area above it.
- [x] Panels that autofocus a search field (Network, Clipboard, Hints) pop the keyboard just to browse; skip the autofocus in tablet mode.
- [x] Laptop-only features with no touch path: screenshots (area, display), starting a recording, clipboard history, Theming, wallpaper picker and next wallpaper, Hints. Proposal: assist pages App · Window · System.
- [x] Window management by touch: the assist Window page (close, fullscreen, floating, split direction, move left / right, to previous / next workspace) and a two-finger long press drag; pseudotiling stays a shortcut.
- [x] Keyboard-only hints shown in tablet mode (launcher, Session menu, Theming, Hints title "Keyboard shortcuts"): touch hints instead, and the gestures listed in Hints.
- [x] Fixed sizes that ignore `Theme.hit`: Audio/Brightness expand chevrons and mute buttons, notification Delete, launcher logo, NetworkDetails and Theming inputs, rows in Audio, Calendar, Wallpaper picker; offsets that ignore `Theme.barHeight` (`SidePanelCard`, `NotificationPopups`, `Overlay`).
- [x] Number fields without `inputMethodHints` (Bluetooth passkey, IP, gateway, DNS) open on letters.
- [x] The 60 ms keyboard re-map over a new panel fades (`desktop-osk` missing from `no_anim`) and briefly reflows tiled windows.

**C. System choices** (behavior changes awaiting approval)
- [x] GTK `gtk-application-prefer-dark-theme=1` hard-coded, wrong under a light dynamic theme (libadwaita warns about it).
- [x] Secret portal not routed (`org.freedesktop.impl.portal.Secret=gnome-keyring`), for Flatpak apps.
- [x] `SDL_VIDEODRIVER=wayland` without the `x11` fallback.
- [x] Hyprglass `default_theme = "dark"` fixed under light themes.
- [x] Touch and stylus mapping global (`input.touchdevice`/`tablet`); per device (`hl.device`) would leave an external touch monitor alone.
- [x] hyprlock strings ("Password", fingerprint messages) in English only: render them through i18n.
- [x] Still open from earlier: environment import in three places; blur coverage differs (layer rule vs Hyprglass: tray menu, OSK, the auth dialogs); `electron-flags.conf` unused (now applied to VS Code and ChatGPT through `electron.py`).

**D. Docs out of date**
- [x] plugins.md gestures (edge swipes, three-finger overview); configuration.md `no_anim` list and "no window borders"; interface.md transparent bar "stays blurred", history/DND "reset on restart"; integrations.md "PAM files are not modified" (after `tablet-auth.sh`); ROADMAP lines on edge swipes and the open gesture test; the qtXct `$HOME` follow-up is obsolete.

**E. Cleanup and i18n**
- [x] Shared code: the workspace slots (`WorkspaceModel.fromHyprland`, used by the bar and the assist button); one watcher of `selection.json` (`DynamicTheme.wallpaper`, read by Theming and BarStyle); `Theming.query()` for `refresh()` and the queue; consistent XDG fallbacks (`get(var) or default`) in the helpers.
- [x] Deferred cleanups (no visible change): `components/MenuLayer.qml` is the full-screen layer of the tray, window and dock menus (grab, outside press, edge clamp); `libexec/desktop/common.py` holds atomic writes, image types, the `magick` call and the focused monitor for theme, wallpaper, xwayland, rotation, gaming and electron; the legacy Control Center rows stay as documented alternatives, now three short files on `controlcenter/SwitchRow.qml`; the `qt` Stow package (`qt*ct/colors/desktop.conf`, a stale Graphite scheme in the qtXct GUI) is gone, its links removed, and the test checks the rendered scheme instead.
- [x] Fix: `electron.py apply` had replaced the Stow link of the ChatGPT entry with a generated copy, so `stow.py` reported a conflict on `shell`. The repo entry now carries the flags itself, ChatGPT left `electron-apps.conf`, and a linked entry is never replaced.
- [x] Dead or stale: hyprgrass `edge_margin`, `osk.MASKS`, the keys `tablet.mode` and `osk.title`, the dangling `wifi-weak.svg` link in `$HOME`.
- [x] i18n: prefix strings now take `%1` (battery, OSD, recording, network, Bluetooth, sharing, wallpaper); modifier names in Hints come from the catalog (Maiusc in Italian); the workspace tooltip uses `I18n.plural`; "Workspace N" binds are translated; `check-i18n.py` scans every `i18n.py` call in the wrappers and the Hyprland config. Units (%, W, Wh) stay as symbols.
- [x] Accessibility: names for tray items, assist buttons, the share picker "Remember" switch and the wallpaper parent button; `ToggleTile` shows keyboard focus.
- [x] Timeouts on the one-shot calls of recording, portal picker, osk layout and clipboard; `check.sh` globs `scripts/tests/test_*.py`; fastfetch "threads"; the two animation literals follow `reduceMotion`.
- [x] Checked: the bar double-tap does not fire from a bar button or the window title. Buttons and the title accept the press, so the handler underneath never sees it (qmltestrunner with touch on the same structure: button and title 0 toggles, empty bar 1); the user confirmed it with the mouse.

### Backlog (reported 2026-11-03)

- [x] Light GTK dialogs with the dark theme (file chooser, keyring unlock): GTK 3 asked for `Adwaita-dark`, which Fedora 44 no longer ships (`gnome-themes-extra` is gone), and fell back to light Adwaita. Themes now name `adw-gtk3-dark`/`adw-gtk3` (`adw-gtk3-theme` in the manifest), which also takes the theme palette from `gtk.css`. The portal file chooser floats centered at 50%×60% of the monitor instead of tiling to full height (`portal-file-chooser` rule).
- [x] Volume did nothing with the JBL TUNE760NC: in that connection BlueZ's AVRCP volume stayed at 96/127 whatever PipeWire sent. After `systemctl --user restart wireplumber` hardware volume works (transport 38/76/57 for 0.3/0.6/0.45), so it was the connection, not the headset; the `bluetoothd` log shows a connect collision. A per-device rule for software volume was tried and dropped. Troubleshooting has the check and the restart.

### Battery (2026-11-05)

- [x] Helpers end with the shell (`setpriv --pdeathsig`); agent dot blinks on battery; event-driven brightness and camera watchers; adaptive bar-visibility polling. Details in the [verification log](verification-log.md#battery-and-resource-use-2026-11-05).
- [x] Display refresh in the battery panel: VRR (when the display supports it) or a listed rate, the user's choice, kept across reloads; power profiles as a row of icons; the panel fits its content.
- [x] A refresh choice for battery and one for mains power, applied when the source changes (plugging and unplugging tried by the user); Power Saver turns on by itself at 20% (a switch, on by default) and the charger brings the previous profile back.
  - [ ] See the switch at 20% on a real discharge.

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
- [x] Environment import runs twice concurrently (`session.lua` and `desktop-session`) with different variable lists: one call in `desktop-session` since review batch C.
- [x] Blur coverage differs: since review batch C the blur rule and Hyprglass cover the same surfaces (the rule adds the bar).
- [x] `electron-flags.conf` is not read by any Fedora launcher and `UseOzonePlatform` is obsolete: kept, `electron.py` applies it through desktop entries (review batch C).
- [x] Workspace pills use `ScriptModel` keyed by `id`: delegates (button, tooltip window, timer) survive Hyprland updates and the width animation now runs.
- [x] Lazy panels (2026-11-05): the 18 panels are created when they open and dropped a minute after they close; the state that persisted goes through `ShellState.recall` / `remember`, and a panel created open gets the same animation and focus. See the [verification log](verification-log.md#lazy-panels-auto-power-saver-refresh-per-power-source-2026-11-05).
- [x] Each `Icon` carries a `MultiEffect` for recolouring: kept (2026-10-29). Colorization alone samples the `Image` texture directly (no extra render pass), it is one shader node per visible icon, hidden panel windows draw nothing, and it is the only way to recolour the icon pack's symbolic glyphs too. `pragma ComponentBehavior: Bound` added to `Bar`, `TrayMenu` and `WorkspaceStrip` (their delegates already used required properties); the shell reloaded cleanly and the bar, tray and workspaces drew as before.
- [x] Clearer messages in `install-hypr-plugins.py`: outside the session, a missing Hyprland instance and non-JSON replies from hyprctl now say what happened instead of an empty exit or a traceback (`build.py` untouched, so the bundle digest stays). Helper timeouts were added in review batches D/E; the qtXct `$HOME` item is obsolete.

## Possible extensions identified

- [x] System updates in the bar (2026-10-29): a systemd user timer checks dnf and Flatpak 5 minutes after login and every 6 hours; an icon with the count, a notification for new ones, and a panel with Check now and Update (a terminal running dnf and Flatpak, with a reminder to rebuild the plugins after a Hyprland update).
- [x] Hyprland 0.57.0 from `lionheartp/Hyprland`, the COPR the Hyprland wiki recommends for Fedora (2026-10-30); `nett00n/hyprland` and `errornointernet/quickshell` are gone. New pins for all plugins, the touch patch redone for Hyprgrass v0.57.0, `hypr-hot-edge` dropped (it does not build on 0.57) for a hover area in the bar, `damping` for `dampening`. The build now reports its real commit.
- [x] Automated installer: `scripts/install-desktop.py` with `install/manifest.toml` and `install/fedora.py`, previewed by default and safe to repeat; `.github/workflows/install.yml` runs it in a fresh Fedora 45.
- [x] Uninstall (2026-11-05): `apply` keeps a record of what it changes and what it replaced (`~/.local/state/dotfiles/install.json`); `--uninstall` undoes it in a safe order, from a console with Hyprland logged out, and rebuilds the record from the manifest and the dnf history for installs made before it. In the guided installer as **Remove the desktop**.
- [x] Plugins rebuilt at login (2026-11-05): a changed packaging or a verified Hyprland update is rebuilt at the next login, before anything is loaded (`desktop-plugins reload` opens a terminal); `install-hypr-plugins.py` never replaces loaded plugins, and resets an ABI-mismatched cache only with nothing loaded. `VERIFIED` moved to `scripts/hyprpm/bundle.py`, out of the packaging digest.
- [x] One build cache key per plugin (#35, 2026-11-08): moving one pin compiles only that plugin, and the others are copied from `~/.cache/dotfiles/hyprpm-build/<plugin>/<key>`. A finished build deletes older entries of its plugin and the old layout (4.4 GB here).
- [x] Hyprland 0.57.2-1 (#56, 2026-11-10): the four pins built against its headers and loaded in a nested 0.57.2 with the real `plugins.lua`, then added to `VERIFIED` next to 0.57.1; the login rebuild on the machine followed. Arch's `0.57.2-1` (in `extra` since 2026-11-09) compiled in a container and accepted the same day.
- [x] Found while recording the README (2026-11-10): `desktop-radio video` closed an open Radio panel (#54, `ShellState.open()`), and the Theme tab kept **Current** on the old theme after a change from outside the panel (#58, fixed in #59).
- [x] Radio and music panel (#48, by GBSpada, merged 2026-11-10): stations from a JSON file the user can extend, YouTube search (ytfzf, else yt-dlp), one mpv of its own on MPRIS through mpv-mpris (media profile). Reworked in review: commands reach only that mpv, URLs are checked, no global mpv script. In review the video moved into the panel (Qt Multimedia, a video-only stream kept in step with mpv) and the controls to the bottom; tried by the user and on screen while recording the README (2026-11-10). The profile is now `radio`.
- [x] Installer profiles in parts (#49): parts picked one by one (`profile.part`) in the manifest, the installer, the TUI accordion and Settings → System → Profiles; new profiles: codecs in `core`, `hardware` in parts checked by detection, `apps` and `utils` with a base set checked, `assistant` (was `herdr`), `containers` without Tailscale, `radio` (was `media`), `gaming` with `steam-hidpi`; record version 3. Step 1 tried by the user (2026-11-09). Step 2: the plugins are parts (`plugins.hyprspace`, `plugins.hyprglass`, `plugins.hyprcapture`, record version 4), the installer writes its units to `~/.local/state/dotfiles/units`, and Hyprland and the shell hide what a missing plugin drives. Step 3: without `assistant`, the AI block is hidden (bar icon, Settings section, assist actions, launcher entry, Super + A and its keys); without `radio`, the radio (Control Center button, launcher entry, Super + M). The parts in Settings → System → Profiles were hidden until #53 (a list inside `modelData` is no JS array); tried by the user, with the chevron left of the title (2026-11-10). Step 4: the README (2026-11-10).
- [x] No terminal windows for system work (#37), step 1 of 4: the per-operation root broker (`privileged.py`, `scripts/privileged/root-broker`, the `sudo` shim) and its install through the core `files` step, tried by the user with the real pkexec (one prompt). Next: plugin rebuilds (with #36), updates, then profiles and agents in Settings.
  - [x] Step 2 (#36): Settings → System → Plugins (state, each plugin, rebuild with its log, the build cache), and the rebuild at login in the background behind one prompt instead of a terminal. The tab was seen by the user (2026-11-09). The rebuild at login ran for real after Hyprland 0.57.2 (2026-11-10): in the background behind one prompt, the four plugins copied from the build cache in 17 s and loaded with no config errors, confirmed by the user.
  - [x] Step 3: updates applied from the panel and Settings → System → Updates without a terminal (`desktop-updates apply`, `install-tui.py --apply-updates`, one prompt), with a switch per section and the progress and log in the panel. Tried by the user with a downgraded rsync (2026-11-09).
  - [x] Step 4: profiles (Install, Complete, Remove: the dry-run in the tab, then Apply in the background behind one prompt) and agent installs (in the background, as the user, with their output in Settings → Assistant), through `jobs.py` and `services/Job.qml`. **Open the guided installer** stays, for the first install, removing the desktop and firmware. Tried by the user with `utils.unrar` (2026-11-10): removed, then switched on again from Settings → System → Profiles, one prompt each. That found #61: a removal dropped the units installed without a record (the AI block), and a part left on the system stayed switched on. Fixed in #62. Agent installs from Settings → Assistant are still to try.
- [x] Polkit prompt with the password alone or the fingerprint (#40): a "failed, try again" line, the account it asks for and a choice of administrator, and with the `hardware` profile its own `/etc/pam.d/polkit-1`. Tried by the user (2026-11-09).
  - [x] Fingerprint first, then the password (asked by the user, 2026-11-09): `desktop-fingerprint` (`pam_exec`, `fprintd-verify`) instead of the empty answer, and **Use password** in the prompt stops the reader. The stacks and the step are tested; tried by the user (2026-11-09, #47).
- [x] Review follow-ups (2026-11-05): bugs (zsh clock, `desktop-theme glass`, wallpaper picker focus, malformed `updates.json`, stuck recording stop, gallery and brightness refreshes, notification text, Hints categories, Bluetooth and gaming messages, double assistant launch, monitors that go away, private state files) and approved behavior changes (Sleep key suspends once, daemons as user units, Quickshell supervised, lock timeouts, clamshell with the lid closed, offline update checks, language and formats from the session locale). See verification-log.md.
  - [ ] Clamshell with an external monitor, on the machine.
- [x] Window resize with `Super + Ctrl + arrows` and a touch swipe sideways for the Theming tabs and the assist menu pages (2026-11-05).
  - [x] Tried by the user (2026-11-05).
- [x] Code review issues (2026-11-05): 59 of 60 findings fixed, one commit each (security of theme names, Battery and Idle at startup, lost requests, list models, watchers, installer undo checks and speed, tests for `tablet.lua`, binds and panel names, `theme.py` and Theming/Network split into files). See verification-log.md.
  - [ ] VRR choice of the internal display toggling external monitors (#40), with an external monitor connected.
  - [ ] Open the changed panels once on screen (Theming tabs, Network, launcher, store, clipboard) and the on-screen keyboard.
- [x] Uninstall and plugin rebuild review (2026-11-05): a record holding only the profiles is rebuilt from the history; uninstall leaves what changed since the install, what packages installed by hand need and repositories still in use; an interrupted rebuild is retried at the next login. See verification-log.md.
- [x] Guided installer (2026-11-05): `scripts/install-tui.py`, a curses front end of the same steps (profiles, vendor firmware, review with per-step details, apply with one sudo prompt and an optional reboot, `post` inside Hyprland). `install-desktop.py` only gained `refuse()`, `preflight_warnings()` and `valid_profiles()`, split out of `preflight()` and `main()` with the same output.
- [x] Fedora 45 (2026-11-04): container test on the final repositories, `fc45` in the guard, laptop reset; Wi-Fi, audio, touch, screen sharing and the bar transparency work; Fedora 44 dropped from CI and the guard.
- [x] Fedora 45 follow-ups (2026-11-05): rotation (the HP ISH firmware in the initramfs, now the `firmware` step of `hardware` with `--firmware DIR`), fingerprint enrolled (GDM takes only the password at the first sign-in by GNOME design, which also unlocks oo7, so no keyring prompt), zsh as the login shell.
- [x] zsh as the login shell (2026-11-05): `core` installs it with Powerlevel10k (lean, theme ANSI colors), zsh-autocomplete, autosuggestions, syntax highlighting, fzf, zoxide, eza and bat; new `login_shell` and `clones` manifest keys and steps, and the `zsh` Stow package.
- [x] Installer profiles (2026-11-04): `apps` trimmed, opt-in `containers`, `media`, `gaming`, `steam-hidpi` and `codecs`, `swaps` for the RPM Fusion codecs, `exclude` for the GNOME extras GDM recommends, no Flatpaks, and no user name in the configuration.
- [x] Battery warnings at 20% (with Power Saver) and 10% (critical), once per discharge (2026-11-05).
  - [ ] See both on screen.
- [x] Per-app volume in the Audio panel (2026-11-05).
- [x] Alt + Tab window switcher with thumbnails, most recently used first (2026-11-05).
  - [x] Tried with the keyboard by the user (2026-11-05).
- [x] Stylus and peripheral batteries, color picker, focus sessions, text from a screen area and "ask Claude about this area", calculator and file search in the launcher (2026-11-05).
  - [x] OCR, ask Claude, the calculator, file search and the stylus battery tried by the user (2026-11-05).
- [x] Privacy indicators, emoji picker, media in the bar and on the lock screen, weather in the calendar, screen zoom, a High Contrast theme and a display picker with Extend / Mirror / External only / Laptop only (2026-11-05).
  - [ ] See a screen share and a player in the bar and on the lock screen; try the display modes with a real monitor.
- [x] Shell text scale, an emoji page on the on-screen keyboard, pinch zoom, and cursor packs (Adwaita, Breeze installed; macOS and Bibata fetched on demand) (2026-11-05).
  - [x] Pinch zoom and the emoji page tried by touch by the user (2026-11-05).
- [x] Cursor customization (requested 2026-11-05): theme and size from the Theming panel, applied everywhere the cursor is set today (Hyprland/hyprcursor and `HYPRCURSOR_SIZE`, GSettings `cursor-theme` from `theme.py`, the GTK `settings.ini` files that pin Adwaita 24, XWayland through `xwayland.py`, Qt). Done the same day in the Icons tab.
- [x] Settings, one GNOME-style panel for every configuration, with a desktop quick menu (#8, closed 2026-11-06). Phase 1 done 2026-11-06: the Settings panel (sidebar, compact mode, `Super + I`, `.desktop` entry, `desktop-shell toggle settings [SECTION]`), with Appearance as its first section; `theming` became an alias of Settings → Appearance (`ShellState.aliases`). Phase 2 done the same day: Desktop, Keyboard, Tablet and touch, Power and Privacy built from `SettingsSchema.js`, written to `shell.json` by `Config.set` / `reset`, with keyboard navigation. Phase 3, first half: Network, Bluetooth, Displays and Sound are sections too, showing the same views as their quick panels (`panels/network/NetworkView.qml`, `bluetooth/`, `displays/`, `audio/`), which gained a **Settings…** link. Phase 3, second half: Assistant and System (About from `about.py`, Updates, Advanced: own settings folder and files, Hyprland config errors, shell options reset), **Settings…** in the Control Center and the assistant and updates panels, and `SECTION/TAB` for the IPC. Phase 4: the desktop menu (right click or long press on the empty desktop, `desktop-shell desktop-menu`): Open (Applications, Settings) and Session (Lock, then Suspend, Log out, Restart and Shut down through the session menu on their confirmation), with monochrome shell glyphs (`glyph` in `PopupMenu`); the Settings sidebar got group labels; a transparent Bottom layer per screen (`components/DesktopCatcher.qml`) that steps aside for `ConsoleCatcher` while the console is open there. Phase 5: `settings.lua`, generated from the `hyprland` key of `shell.json` by `hyprsettings.py` and loaded before `hypr.lua`: keyboard layout and variant, personal shortcuts, the assistant's language. Monitor settings followed (#17): `displays.configure` in `displays.lua` (the panel takes scale and position over its rule; another monitor a whole rule through `M.monitor`), listed modes only, a 15-second confirm-or-revert. Also from the same round of feedback: the Network list (#16), Settings → Power with the power profile (#18), the Appearance Layout tab (#19: window rounding, border and gaps in a column; Bar and Effects stay on Theme).
- [x] Reduce effects (#3, 2026-11-06): one choice in Theming → Theme turns off Hyprland's animations, blur, shadows and the Hyprglass glass and the shell's motion, with near-opaque shell surfaces so translucent themes stay readable. Not done: an automatic mode (on battery, or from the machine profile).
- [x] Cursors tab of its own in the Theming panel (#5, 2026-11-06): each theme with five shapes previewed at the chosen size from its own XCursor or hyprcursor files, the size, and the KDE Store for cursors; the Icons tab keeps only icon packs.
  - [x] Cursor themes: Breeze in the manifest, macOS and Bibata on demand (Phinger dropped).
- [x] Cursor and icon themes from the KDE Store, searched and installed from the Theming panel (2026-11-05).
  - [x] Tried from the panel by the user (2026-11-05).
- [x] Arch Linux (2026-11-05, decided with the user: official repositories, AUR builds pinned to a commit, plugins too, tablet sign-in later): the `[arch]` table of the manifest (every name checked with `pacman -Si` and `pacman -F`) and `install/arch.py` (pacman with `-Syu`, multilib in `pacman.conf`, removal with `-Rsc`, the system before the desktop from `pacman.log`). New `aur` step: the PKGBUILD at its pinned commit, built by `makepkg` as the user; `install-desktop.py pins` shows newer AUR commits with a link to their changes and `--update` pins them. The plugin packaging reads the build with pacman (headers in `hyprland`, `0.57.1-1` verified to compile), so the bundle digest changed and the plugins rebuild once at the next login on Fedora. Updates through `checkupdates` and `pacman -Syu`, zsh and fzf paths of both, the distribution logo in the bar and in fastfetch, install hints per distribution, libical 3 or 4 in `calendar.py`, Qt tools in `/usr/lib` in `check.sh`, Arch jobs in both workflows. Fedora behaves as before. Tested in `archlinux` containers; see verification-log.md.
  - [ ] Install on a real Arch (a VM, then the laptop): GDM and the `hyprland-uwsm` session, portals, oo7 unlocked at login, the plugins loaded, rotation with the HP firmware in a mkinitcpio initramfs.
  - [ ] Tablet sign-in on Arch: PAM edited without authselect (`tablet-auth.sh`), tested in a VM before the laptop.
  - [ ] Tailscale tray icon on Arch: its package has no `tailscale-systray` unit.
  - [x] The installer as a management TUI (2026-11-05, decided with the user: the repository only as a fast-forward, new pins left for the user to commit): **Check for updates** in `install-tui.py` (`--updates` opens it) lists system packages, Flatpak apps, AUR packages and zsh plugins newer than their pins (zsh-autocomplete follows its release tags, Powerlevel10k its branch), the repository behind its upstream, what the installed profiles still need and the plugin state; the checked lines apply in one sudo run. `install-desktop.py pins` covers the clones too. `desktop-manager` opens it from any terminal (`desktop-manager updates`: the updates screen).
    - [ ] Try it on screen: check, pick, apply a system update and a pin, and a pull on the Arch machine.
    - [x] **Update** in the bar's updates panel opens it (2026-11-06, decided with the user): `desktop-updates upgrade` runs `desktop-manager updates` in its floating terminal instead of dnf (pacman) and Flatpak at once.
    - [x] The repository in the bar's check (#26, 2026-11-07): `updates.py` fetches this clone's upstream branch (never prompting) with the packages and Flatpak; the icon counts its new commits as one update, a notification announces them, the panel and Settings → Updates list them and say when the clone has commits of its own or local changes; a pull from the updates screen checks the repository again (`desktop-updates check repository`).
    - [x] Installer profiles managed from Settings (#28, requested 2026-11-07). Part 2 done 2026-11-07: Settings → System → Profiles (`profiles.py`) lists every profile with its state, Install or Complete opens the guided installer with it added (`--add`), Remove on its removal review (`--remove`), for profiles the installer recorded. Part 1: `install-desktop.py --remove PROFILES` and **Remove profiles** in the guided installer (`--add`, `--remove` to start on them) undo only what the record holds, the removed profiles name and no profile that stays names; packages of profiles that stay are kept from dnf's removal of dependents; `plugins` only from a console; the record drops the profile and what went.
- [x] README refreshed (2026-11-06): Arch Linux badge and subtitle, eight themes and the KDE Store, the guided installer and its updates screen, the newer small features; all screenshots retaken (English shell, demo content) and two new ones, the KDE Store page and the emoji picker.
- [x] README refreshed again (2026-11-10): highlights and gallery in one section, led by Settings (a cycle through its sections), the Radio panel (a recording with the video in the panel) and the installer in profiles (the guided installer and Settings → System → Profiles with their parts open); English shell, Tokyo Night, no personal data. Second pass the same day: the opening animation through the themes in Settings → Appearance, the radio moved into the table, new launcher, Themes and AI console (Herdr) pictures, the KDE Store picture dropped.
- [ ] Debian: a manifest table and a module with the functions of `install/fedora.py`, with names checked on Debian; `authselect` in `tablet-auth.sh` as on Arch.
