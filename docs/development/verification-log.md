# Verification log

[← Docs](../README.md)

What was tested, how and with what result, oldest first. For help with a problem, see [Troubleshooting](../guide/troubleshooting.md).

## Early checks

Completed checks: OSDs with simulated services (volume, speaker/microphone mute, rapid updates, timeout, disabling, audio reconnection, panel suppression, and multiple monitors); backlight watcher on simulated sysfs (baseline, changes, hotplug, and invalid values); brightness dragging regression with queued writes; Lua/script parsing; QML loading/layout; Control Center and expandable sections; tooltip placement; brightness helper with fake backends (routing, limits, and DDC scaling); live dragging updates without stale-value rollback and hardware error handling; Wayland inhibitor creation/release while panels are closed; native Wi-Fi scanning; audio devices and UPower readings; leap-year/year-boundary calendar behavior; complete power-menu navigation with a fake command; persistent wallpaper selection. Wallpaper tests cover spaces/commas in filenames and retention of the previous choice after invalid files or IPC errors. Earlier Hyprshot checks covered duplicate bindings and saving/copying in all four modes with simulated backends; its interactive capture was not physically tested before replacement by HyprCapture.

Later checks: multiple-monitor workspace model (minimum count, unique IDs, active/urgent states, and exclusion of special workspaces); isolated clipboard history with byte-for-byte Unicode text and PNG copying, deletion, and clearing; X11/Wayland bridge with the original selection restored; real recordings of a test window with/without speaker audio, finalized Matroska files, and ffprobe inspection; VS Code/Electron X11 and Wayland with temporary profiles; ScreenCast portal and PipeWire frame reception; new Hyprlock layout and fprintd device acquisition in a headless compositor. QML panels were checked with mock data. Physical unlock tests and the user's calling web app remain to be tested.

## Current-phase verification

- Popups: simulated click events on the real component, default action invoked once, right-click without deletion; filtered markup and notification-center actions retained.
- Bluetooth: simulated BlueZ on a private D-Bus bus, agent registration/release, PIN and passkey, confirmation, rejected authorizations, stale responses ignored, code display, and cancellation. No real device was paired or removed during testing.
- MPRIS: two players on a private bus, metadata, selection, state changes, transport commands, seeking with seconds/microseconds conversion, and fallback when a player disappears.
- Calendars: all four existing EDS sources read without errors; event contents omitted from diagnostic logs.
- QML layout: Control Center, agenda, Bluetooth request, and popups rendered with mock data.
- Hotplug: physical HDMI disconnection/reconnection verified. DDC/CI on the Philips FTV was unavailable in these tests; see [details](../guide/configuration.md#philips-ftv-display-verification-results).

Final pairing with a physical device remains manual through **Bluetooth → Scan for devices**. Real DDC reads/writes still need validation on a compatible monitor.

- Application rendering: the reported ChatGPT and Nautilus instances were X11 at scale 1.667; instances with isolated profiles/buses were verified as native Wayland. Local launchers were updated without closing the user's applications.
- Tray: regression with the icon 600 px from the edge, menu below the icon after Wayland sizing, hover, disabled actions, checkboxes, submenus, Escape, and outside clicks.
- Reorganization: full QML loading and the sharing picker verified after updating imports and Stow links.
- Internationalization: nested semantic catalogs, locale selection, placeholders, plural messages, fallback, QML/Python/command references, and both interface languages checked. Italian expectations are read from `it_IT.json`; other repository content uses English.

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

## XWayland scaling verification

Cursor captures over floating zenity windows showed the X11 pointer as the X server's blocky fallback arrow while Wayland windows used Adwaita; naming the theme and a 40 px size fixed it. After `desktop-xwayland apply` (eDP-1, scale 1.667 → `Xft.dpi` 160, `Xcursor.theme` Adwaita, `Xcursor.size` 40), an X11 zenity started without `XCURSOR_SIZE` showed the Adwaita arrow at the Wayland size and normal-size text, and `qt6ct` on `xcb` rendered identically to its Wayland instance. `Hyprland --verify-config` accepted `hl.on("monitor.added"/"monitor.removed")`. The Aseprite ini edit was tested on copies (only `screen_scale` changed; missing section or file handled), and the wrapper started a test command without `XCURSOR_SIZE`. `steam_command` now yields `-forcedesktopscaling 1.667` on eDP-1; the user confirmed Steam. Aseprite first received 2 (the nearest whole number to 1.667), which looks like 1x because X11 draws in physical pixels; the wrapper now multiplies its 200% base by the monitor scale, giving 3 on the built-in panel. Its default pixel cursor then became huge: laf builds custom X cursors at surface size × scale, while native cursors come from the X theme (`XCreateFontCursor`, themed by libXcursor at `Xcursor.size`), so the wrapper enables `use_native_cursor` (default `false` in Aseprite's `pref.xml`) only when the key is absent. The previous Steam settings are in `~/.config/desktop/steam.json.bak-before-fractional`. `XCURSOR_SIZE` stays in the current session's environment until the next login; the Steam and Aseprite wrappers already drop it.

## Steam and gamescope verification

The user confirmed improved text clarity with 1:1 XWayland rendering, but changing `-forcedesktopscaling` from 1.667 to 2 did not visibly enlarge the interface. Exporting `STEAM_FORCE_DESKTOPUI_SCALING` to both client and web helper also left the header unchanged. Steam's Interface HiDPI switch was already on. SDL reported content scale 1 through Wayland and 2 through X11 with its hint, but that alternate backend did not change the desktop UI either. Those diagnostics establish that startup arguments and environment alone are insufficient for this installed build.

The renderer initialization workaround was then verified with cropped menu screenshots: the same 500×95 logical region showed visibly doubled labels and controls after setting the CEF scale to 2 at initialization. A subsequent restart through the permanent runtime wrapper retained the enlarged rendering. `/proc` checks confirmed the managed library in all eight web-helper processes and absent from the main Steam client's preload environment; temporary test preloads were removed by the clean restart. No Steam binaries or startup scripts were edited, no debugger remains attached, and no debugging port was enabled. See [Steam and gamescope](../guide/integrations.md#steam-and-gamescope) for implementation and disabling the workaround.

`~/.config/desktop/steam.json` selects 2 for eDP-1 while other monitors retain their detected scale. Simulated startup on an unscaled HDMI monitor selected 1; physical HDMI startup remains to be checked. Exit and reopen Steam after changing a preference. A one-off override is `DESKTOP_STEAM_SCALE=1.5 desktop-steam` (range 1–4). Other legacy X11 applications may become smaller under the global 1:1 policy.

Gamescope 3.16.29 was tested with a temporary GLX graphics window on the Intel LNL GPU using Mesa 26.2.4: native Wayland presentation to Hyprland, Vulkan composition, and Intel OpenGL rendering succeeded. The installed wrapper also ran fullscreen on the 2880×1800 output with a 1920×1200 internal resolution, FSR, and a 60 FPS setting. High-priority Vulkan queues were unavailable and gamescope successfully fell back to normal priority; no elevated privileges or driver workarounds were needed.

Argument checks covered monitor scale 1/1.667, boolean/integer Hyprland option formats, rotated physical dimensions, caller scaling overrides, invalid scales, and command arguments containing spaces/shell characters. Script/Lua parsing, desktop-entry validation, Stow, and internationalization checks passed. These graphics tests do not establish performance, Steam overlay support, anti-cheat compatibility, or Proton behavior for a particular game. Test the desired game with `desktop-gamescope -- %command%` in its launch options and remove that option if it causes issues.

## AI assistant verification

`Hyprland --verify-config` accepted the `desktop-ai` window rule (`workspace`, `float`, `size`, `center`) and rejected an unknown field in the same test, so the field names are checked. After the live reload `hyprctl configerrors` was empty and `Super + A` was listed as "AI assistant". The first `desktop-ai` call opened one floating `desktop-ai` client on `special:ai`, 1036×756 at 346,181 on eDP-1 (60% × 70% of 1728×1080 logical, centred below the bar), with the special workspace shown. The next two calls hid and showed it again without a second client. After the window was closed, the next call started a new one. `pgrep` showed `claude --settings {"voice": {"enabled": true, "mode": "hold"}, "language": "english"}` under the `en_US` locale. With `hl.env("DESKTOP_AI_LANGUAGE", "italian")` in `local.lua`, a session started through Hyprland exec got `"language": "italian"`. No `ANTHROPIC_API_KEY` is set and Claude Code has a claude.ai login. The user confirmed hold-`Space` dictation with a real microphone.

## Dock verification

After stowing, the live shell loaded the dock (`Configuration Loaded`). A first attempt named the window file `dock/Dock.qml`, which clashes with the `Dock` singleton ("Composite Singleton Type Dock is not creatable"), so it is `DockWindow.qml`. Quickshell kept the previous instance until the fix. `hyprctl layers -j` showed `desktop-dock` on eDP-1 at 0,1000, 1728×80, next to the unchanged 38 px `desktop-bar`. `desktop-shell status` listed the six pins plus `desktop-ai`, with `zen` grouped under `zen-browser`. The Kitty-based `desktop-ai` window has no desktop entry of its own, so it keeps its class and the generic icon. `dock toggle` twice set `shown` to `eDP-1`, then back to none, with the request `true` then `false`. Invalid actions and `launch 0` exit 2 with the usage text. `dock launch 2` focused Zen, and `dock launch 7` focused the assistant again and reopened `special:ai`. Each launch peeked the dock, and the peek cleared about one second later. `Super + D` and the nine `Super + Alt + N` binds are registered, and `hyprctl configerrors` is empty. The user then confirmed edge reveal, corners, fullscreen, Hyprspace, the empty workspace, urgency and blur. One bug turned up: with the pointer resting on the bottom edge beside the dock, the dock bounced up and down. Reproduced with `hl.dsp.cursor.move` to 300,1079 (`shown` alternated): once shown, the input region shrank to the dock body, the pointer fell outside it, the dock hid, and the strip revealed it again. The input region is now the strip plus, while shown, the dock body. With a hide request active, the same move kept `shown` steady on the edge. A second bug remained: the dock still hid when the pointer moved from the edge onto an icon. Cursor warps did not show it, because a warp does not deliver hover to the icons the way real pointer motion does. An offscreen `qmltestrunner` test with real mouse moves did: a `HoverHandler` on a sibling below a hover-enabled `MouseArea` reports `hovered: false` over it, while one on an ancestor keeps `true`. The dock's handler now sits on the item that contains the strip, the dock body and the icons. The user confirmed that icons can then be reached and clicked.

## Dock phase 2 verification

**Pins**
- `FileView` with `atomicWrites` created `~/.local/state/desktop-shell/` on first save, so no `mkdir` is needed.
- After a restart the pins fell back to the defaults, although the file held the new list. A loaded `JsonAdapter` list is not a JS array (`Array.isArray` is false). An isolated `qs` instance showed it and confirmed `Array.from` as the fix.
- The user then confirmed that pins survive restarts.

**Assistant icon**
- The `desktop-ai` icon resolved to Papirus `desktop`. Qt applies the dash fallback inside each theme before moving to its parents, so `desktop-ai` became `desktop` in Papirus before `hicolor` was searched.
- Renders from an isolated instance showed the dashless name `desktopai` resolving from `~/.local/share/icons/hicolor`.
- New desktop entries and icon names need a shell restart: `DesktopEntries` does not see them live.
- The icon and the `pin` glyph were drawn in the Desktop Icons Figma file ("App icons" section, `icon/pin`) and exported.

**User-confirmed**
- The menu entries and close confirmation.
- Launcher pinning (mark, `Ctrl+P`, right click).
- Magnification.
- Drag reorder and drag-off removal. Hyprland keeps delivering motion outside the input region while the button is held.

**Keyboard mode**
- Giving the dock window itself keyboard focus made Qt replay a stale hover on it. `pointer.hovered` stayed true with the cursor elsewhere, so the dock never hid. Keyboard handling therefore moved to a separate `DockKeyboard` surface.
- The first version of that surface was 1 px, always mapped, and switched its keyboard interactivity to exclusive when needed. `Window.active` stayed false, so Hyprland never gave it focus, and none of the keys worked. Before that, a Hyprland focus grab requested in the same frame as the surface mapped had been cleared at once.
- Several later variants were edited with `sed -i`. That replaces the file, and Quickshell stopped watching it: `hyprctl layers` still showed the old 1×1 surface, so those tests measured stale code. Earlier "reload stuck after an error" moments had the same cause.
- **Final design** (written in place):
  - The surface is a full-screen Overlay layer, mapped only in keyboard mode, with static exclusive focus, the same as tray menus and the launcher.
  - Its input region excludes the dock body; a press anywhere else ends keyboard mode. No focus grab is used.
  - `Window.active` and item focus were true in three of three IPC cycles.
  - The user confirmed arrows/Tab, Enter, Shift+F10 and Esc.
- `qs ipc call desktop dock show` printed the function signature instead of calling it: `show` is read as a `qs` subcommand. `desktop-shell` now passes `--` before the argument. This was broken since phase 1; only `toggle`/`hide` had been tested then.
- `dock show`/`hide`/`toggle` each held their state over five cycles via IPC. Keys need the physical check.

**Tests and side effects**
- `scripts/tests/tst_dock_model.qml` (9 tests) covers resting offsets, magnification, the drop slot and drag shifts.
- During testing, `dock launch 1` opened a Kitty window in the session.

## Theme pipeline verification

**Equivalence with today's files**
- Templates for hyprlock, GTK and Qt were derived from the existing files and rendered back byte-identically: hyprlock 101 lines, GTK 37 colours, Qt 3×21 roles.
- The Kitty, Quickshell and Hyprland values match their current settings.
- `test_theme.py` keeps checking this.

**Consumers**
- **Quickshell:** an isolated `qs` showed `Theme` taking a probe colour from the JSON, and keeping Graphite with the file missing or broken.
- **Hyprland:** `--verify-config` passed with and without the state file. A probe value in it reached the config, and a value of the wrong type was ignored.
- **Kitty:** `kitty +runpy load_config` expanded `~` in `include`, and skipped a missing file with a notice.
- **GTK:** PyGObject `CssProvider` loaded the relative `@import` through the stowed symlink for GTK 3 and GTK 4: 37 rules, no errors.
- **gsettings:** the first `apply` left everything unchanged except `cursor-theme`, which went from `'default'` back to `'Adwaita'`. That is what `desktop-theme` already set at every login, and Fedora's `default` cursor theme inherits Adwaita.

**Screenshots**
- Before and after the switch, the bar and the open launcher were captured at the same pointer position.
- The left of the bar was pixel-identical, and the opaque launcher row was identical at 1% fuzz.
- The remaining differences sit under translucent surfaces (the windows behind had changed) and next to the clock.

**Probe theme**
- A theme with every colour inverted and different fonts, rendered with `render --out` into a scratch directory, changed every generated file: GTK 37/37 lines, Hyprland 2/2, hyprlock 14, Kitty 31 (opacity unchanged), Qt 3/3, Quickshell 21/21.
- It never touched the session state.

**Lock screen:** the user confirmed that `Super + L` (now through the generated config) looks and unlocks as before.

## Theme switching verification (phase 2)

**Palette sources**
- Kitty ports, fetched as data:
  - catppuccin/kitty `mocha.conf`;
  - folke/tokyonight.nvim `tokyonight_night.conf`;
  - kitty-themes `gruvbox-dark.conf` and `everforest_dark_medium.conf`.
- The surfaces come from each project's scale, which matches those files.
- btop's format was checked against catppuccin/btop and the themes shipped in `/usr/share/btop/themes` (an empty `main_bg` as in `adapta`).

**Contrast** (WCAG, shell text composited over the background)

| Theme | fg/bg | muted/bg | accent text/accent | shell text |
| --- | --- | --- | --- | --- |
| Catppuccin Mocha | 11.34 | 9.26 | 9.23 | 11.34 |
| Tokyo Night | 10.59 | 8.10 | 7.14 | 10.59 |
| Gruvbox | 10.75 | 5.30 | 8.69 | 10.75 |
| Everforest | 7.38 | 5.12 | 6.23 | 7.38 |
| Graphite | 15.29 | 9.05 | 11.97 | 15.29 |

`test_theme.py` enforces the minimums: 7, 4.5, 4.5 and 7.

**Live switch**
- The four VS Code extensions were installed, and their contributed theme ids match the `vscode.theme` values.
- `desktop-theme set` through every theme and back to Graphite gave, each time:
  - no `hyprctl configerrors`;
  - the Quickshell accent, GSettings accent, VS Code `workbench.colorTheme` and btop `color_theme = "desktop"` all following the theme;
  - Control Center captures showing the theme surfaces and accent.
- `settings.json` (mode 644) kept its permissions and formatting.
- `window.autoDetectColorScheme` is on in it, so VS Code reads `workbench.preferredDarkColorTheme` rather than `workbench.colorTheme`; both are now set.
- Backups of `settings.json` and `btop.conf` from before the first switch are kept outside the repository.
- The user tried the themes and approved them.

## Wallpapers per theme verification

**Curation**
- Candidates from the Omarchy theme backgrounds (branch `quattro`) and three community collections were downloaded into a scratch directory and viewed as contact sheets.
- Eight per theme were kept, all landscape and at least 1920 px wide. Images under 1920 px or in portrait were replaced, for example a 1456 px Gruvbox painting and a 1582×2048 Everforest photo.
- URLs are pinned to the commit SHAs resolved through the GitHub API at the time.

**Fetch**
- All four sets downloaded: 8/8 each, 5.9–18 MB per theme, and every sha256 re-checked on disk.
- A probe manifest with a wrong sha256 rejected that file and left no temporary file. A second run reported every file as `present`.

**Live**
- Starting from Graphite with the user's Apple wallpaper, `set tokyo-night` showed `01-liftoff`. `--next` twice gave `02-winding-road`, then `03-quattro`.
- `set graphite` brought back the Apple wallpaper, and `set tokyo-night` brought back `03-quattro`.
- `hyprctl hyprpaper listactive` showed the render of that file.
- With the Everforest set moved away, `set everforest` returned in 0.4 s. `01-tree-tops` was on screen after 1.6 s, and the full set of 8 followed in the background.
- The user reviewed the final contact sheet and kept all 32.

## Theming panel verification

**Qt configuration**
- `qtct.conf.tpl` renders Graphite identically to the old stowed `qt5ct.conf`, apart from its header line.
- `apply` replaced the two Stow links with real files, and the repository copies stayed untouched (an installed output never writes through a link). The stowed copies were then removed from the `qt` package.

**Live reload**
- With the icon pack switched to Breeze, a dock capture was pixel-identical to the one taken with Papirus. Quickshell reads the Qt icon theme only at start, hence the Restart shell button.
- GSettings and the qtXct files changed at once. The preference was then reset to the theme default.

**Listings**
- `fonts`: 10 interface and 6 monospace families before the optional fonts.
- `icons`: 26 packs, about 2.4 s uncached and 0.1 s cached.
- Fedora's Adwaita sets `Hidden=true`, so `Hidden` is ignored.
- A first version of the cache kept serving a stale list after the rules changed; the signature now carries a version.

**Panel**
- Each tab was opened through a temporary default tab and captured. The theme cards, the Graphite wallpaper folders with Custom…, both font lists each rendered in its own family, and the icon packs with their own samples all showed, with no QML warnings.
- `test_theme.py` covers preference merging, the qtct render, link replacement, font filtering and icon discovery through `Inherits` (21 tests).

## Theming panel, round 2

**Previews**
- Twelve theme wallpapers had no preview: the log showed `Unsupported image format` for `.webp`, since `qt6-qtimageformats` is not installed.
- The gallery now shows JPEG thumbnails made by `theme.py thumbs` (about 0.45 s each, cached by path, mtime and size). After that every Gruvbox image, the WebP one included, previewed.

**Bar**
- `bar-style transparent` dropped the gradient. Over a dark wallpaper top (luminance 0.28) the bar text stayed light, and `toggle` returned to shaded.

**Shell icons**
- With Yaru as the Qt icon theme, all 55 bundled glyphs resolved to a pack icon through `IconNames.js`.
- `tst_icon_names.qml` checks that the map covers exactly the files in `assets/icons` and lists symbolic names only.

**Custom fonts and icons**
- `check-font` rejected a family that is not installed and accepted Adwaita Sans.
- `check-icons` accepted `breeze` and rejected `../etc`.

**Restart and reopen**
- `desktop-shell restart theming TAB` validates the tab, waits for the new instance to answer `status`, then calls the new `theming(tab)` IPC.

**Capture pitfall**
- A capture taken right after an in-place QML edit can catch the shell mid-reload: the overlay is there but its card is not. Wait a few seconds after an edit before capturing.

## Transparent bar contrast

**The problem**
- Over Gruvbox `03-village-square` the transparent bar was unreadable.
- The strip mean was 0.58, just under the old fixed 0.6 threshold, so the bar got light text at about 2.7:1.
- The strip was also measured on the uncropped image, which is not what hyprpaper shows.

**Measurements** (mean / deviation)
- All 32 theme wallpapers and the local ones were measured on the cover-cropped strip.
- Flat dark strips: Catppuccin minimal 0.10/0. Flat light: Everforest fog and sea 0.81–0.86/<0.03. Mid-tone paintings: village 0.58/0.10, procession 0.33/0.17. The Apple wallpaper is dark with bright streaks: 0.12/0.14.

**Fix**
- The rule now picks the text with the higher WCAG contrast.
- A translucent backing added at first made the bar look shaded again, so it was removed at the user's request: the bar stays transparent and only text and icons change colour.
- The contrast uses the current theme's own two text colours.
- Over the village strip, Gruvbox's dark text gives 4.9:1.
- `test_theme.py` checks every shipped theme at strip greys from 0 to 1: the chosen colour never falls below 3:1.
- Over busy parts of a painting (branches behind the window title) a colour change alone cannot reach that everywhere.
- The user confirmed the result.

**Restart**
- The automatic restart after font and icon changes was removed at the user's request. The panel shows the restart banner instead, and its button still reopens the panel on the same tab.

**Halo (#171, 2026-11-11)**
- On a 1920×1080 monitor with the Dynamic theme, a bright sky on the left of the strip and a darker right half averaged to light text, and the logo, workspace strip and window title almost disappeared.
- The transparent bar row now has a soft halo in the other text colour (`MultiEffect` shadow, no offset, `blurMax` 8); the Shaded bar is unchanged.
- Checked with `check.sh` (qmllint) only; the look over that wallpaper is still to be confirmed on the live session.

**Bar spacing (#173, 2026-11-11)**
- Measured from the code: a lone icon sat 7 px inside its 30 px button, a tray icon 6 px inside 28 px, and a label or icon group (media, privacy, battery, updates, focus) 4 px inside, so the glyph gaps on the right ranged from 13 to 19 px. Bar buttons now pad 7 px (`Theme.hit(7)`), tray slots are 30 px, the clock lost its extra 3 px margins (same footprint) and the battery icons sit 10 px from the percentage like every other icon and label: every gap is 19 px.
- The faint square beside the media title is the privacy indicator: a screenshot is a screencopy client, Hyprland sends `screencast` for it, and the screen-sharing glyph (`monitor`, a filled rounded rectangle in the theme accent) shows until 1.5 s after the last copied frame, so a capture can catch it, and the next one in a series does. Not a shell bug.
- Checked with `check.sh` only; the look is still to be confirmed on the live session.

## Shell state persistence verification

**Keep awake and Do Not Disturb**
- `desktop-shell dnd toggle` showed the new state OSD ("Do Not Disturb · On", bell-off).
- Quick alternating toggles first left `session.json` behind the in-memory state: the `FileView` watched its own file, so the echo of one write reloaded the adapter over the next change. Only the shell writes the file, so it is no longer watched. Three rapid toggle pairs then left memory and file equal.
- With both on, `desktop-shell restart` brought both back on (`status` `keepAwake`/`quiet` true), and both were then set off again.

**Notification history**
- `notify-send` entries were saved within 500 ms. After the restart, 30 entries came back archived: shown with "Archived", Delete only and no actions.
- A probe file with 55 recent entries plus one 8 days old loaded as 50 archived, the old one dropped. The original file was restored.
- Rewriting `shell.qml` with identical content does not reload Quickshell; a real change (a temporary comment) does.
- The user confirmed the shortcuts and the archived entries.

## Window borders verification

- `Hyprland --verify-config` accepted `general.col.active_border` as `"rgba(rrggbbaa)"`, `"0xAARRGGBB"` and gradient tables. The theme uses the first form.
- With the defaults, `hyprctl getoption` still reported rounding 16 and border 0.
- `window-style --rounding 8 --border 2` gave 8, 2 and the Gruvbox accent (`fffabd2f`) live. `--default` restored 16 and 0.
- `ChoiceChips` is a `Flow` with no natural width, so it wrapped inside rows that did not stretch it, which the wider monospace font showed. It now sets `Layout.preferredWidth` to the width of its pills; `implicitWidth` is read-only on a `Flow`, and setting it failed the load.
- Corners across the shell: 31 literal radii of 6 or more in 20 QML files now go through `Theme.corner()`.
  - With the user's rounding 0, the Theming panel, its chips and cards, the dock, its tooltip and keyboard ring all rendered square. At the default 16 the radii are unchanged.
  - The lock screen field corners follow too: 26 at 16, and the Graphite render is still byte-identical.

## Dynamic theme verification

- matugen 4.2.0 from the COPR. `--json hex --dry-run` prints `colors.<role>.{dark,light,default}` and `base16.base00…base0f` in the same shape, plus `mode` and `is_dark_mode`. With `-m light`, `default` is the light value.
- The first mapping took the ANSI colours from matugen's base16. On `gruvbox/03-village-square` every one came out beige (hue 40–52°, saturation under 0.4), because base16 holds the image's own colours in no hue order, so red and green were the same. ANSI, success and warning now use the standard hues turned at most 15° toward the primary, then the contrast floor. The same image gave a distinct red, green, yellow, blue, magenta and cyan.
- From the panel state on village-square: the dark theme was generated in under a second, with GSettings accent orange. The card showed the mock-up over the wallpaper. Kitty, the bar and the panel followed.
- Choosing `catppuccin-mocha/04-salty-mountains` through `wallpaper.py`, as the gallery does: `DynamicTheme.qml` regenerated by itself. In Auto, matugen `smart` judged this image dark.
- `dynamic --mode light`: the first light theme. `color-scheme` became `prefer-light` and GTK Adwaita. The bar shade used the theme background with dark text, and the panel and Kitty were readable.
- `desktop-wallpaper --next` (`Super + Ctrl + W`) moved to `05-shaded-landscape` in the same folder, and the theme followed.
- Back to Auto and `desktop-theme set gruvbox`: village-square came back, `prefer-dark`, and no further generation ran (`status` → `dynamicTheme.active` false).
- Without matugen, the card showed the install command and could not be clicked, and the mode and palette rows were hidden.
- `test_theme.py` checks the mapping, the hues and contrast of every ANSI colour in both modes, the light bar shade, and a real matugen run when it is installed.

## Shell surface borders verification

- `window-style --border 3` on the dynamic theme rendered `borderSize 3`, `activeBorder #acc7ff` and `inactiveBorder #44474e` into `quickshell.json`, and the shell followed live.
- The Theming panel had a 3 px accent frame. The dock, a `notify-send` popup and the Keep awake OSD had 3 px frames in the border colour.
- With None, `Theme.frameWidth` is 1 and the colours are `stroke`, so every surface draws as before. The Graphite test checks the new `quickshell.json` keys against the `Theme.qml` defaults.

## Tablet mode and rotation verification

- Hyprland 0.56 runs Lua sent with `hyprctl eval` in the config state: a global defined by one eval is callable from the next, and `hl.monitor` applies at once. `Hyprland --verify-config` accepted the `switch:on:Intel HID switches` binds; `hyprctl binds` lists them as locked `__lua` binds.
- `/proc/bus/input/devices` reports `SW=2` (SW_TABLET_MODE) on "Intel HID switches"; the lid is a separate device. iio-sensor-proxy 3.8 reports an accelerometer (no light or proximity sensor).
- `rotation.py apply 1` turned eDP-1 to transform 1 (portrait layout, bar and windows rearranged) with `input:touchdevice:transform` 1; `hyprctl reload` kept it; `apply 0` restored it.
- `desktop-shell tablet on` started `rotation.py watch` (orientation normal, transform 0); `rotation-lock on` showed the OSD and stopped the watcher; `tablet off` stopped it too. `session.json` holds `rotationLock`, the posture file `tablet`.
- The Control Center shows the Rotation lock tile on the OmniBook.
- The user folded the OmniBook into tablet mode and turned it in all four directions: the switch, the sensor mapping, touch and the rotation lock all behaved.
- The assistant window kept 1036×756 after a rotation and overflowed the portrait screen. `hl.window.resize` takes `{ x, y, window }` and `hl.window.center` `{ window }`; `HL.Monitor.width/height` stay physical after a transform. On `monitor.layout_changed` it now becomes 648×1209 in portrait (60% × 70% of 1080×1728 logical), centred, and 1036×756 again upright.

## Assist button verification

- `desktop-shell assist show` mapped one `desktop-assist` overlay layer (1728×1080, eDP-1) with the button on the right edge at 62% of the free height.
- The input region was meant to be the button only, but the item that catches taps outside the open menu also had `anchors.fill`, which overrides its zero size: while the button was shown (all of tablet mode) the transparent surface took every touch and click, and the user could not reach Zen or Nautilus. The item now has no anchors, only a size while the menu is open.
- `assist menu` opened the eight actions beside the button, towards the middle. The first version bound the menu origin to its own grid size and Qt reported a binding loop, as the layout polished during the evaluation; the menu is now placed after layout (`Qt.callLater`) from the button's resting place. With the monospace interface font, "Notifications" needs 100 px buttons.
- `hl.dsp.focus({ workspace = "e+1" })` stays put when no other workspace exists, unlike the bar; the workspace buttons now step along `WorkspaceModel.build` like bar scrolling.
- `geometry tests` (`tst_assist_model.qml`): placing, tucking, snapping, the round trip and the menu origin.
- The Hyprland plugins were not loaded in this session: Hyprland moved from 0.56.2-17 to -20 on 2026-10-24 and `plugins.py` suspends autoload for an unverified build ("Build differs from the verified version"). The three-finger long press needs them rebuilt (`./scripts/install-hypr-plugins.py`).
- Rebuild: `build.py` pinned 0.56.2-17 and refused the -20 build. Upstream version and ABI hash were unchanged (the COPR changelog only updates Nix inputs), so the pin moved to -20 with the same plugin revisions. The new digest needs `hyprpm remove dotfiles-desktop` before `install-hypr-plugins.py` ("Packaging has changed"). Afterwards all five plugins loaded, `plugins.py` passed and `plugin:hyprgrass` options were applied.

## On-screen keyboard verification

- Hyprland 0.56 advertises `zwp_virtual_keyboard_manager_v1`, `zwp_input_method_manager_v2`, `zwp_text_input_manager_v3` and `zwp_text_input_manager_v1`.
- `osk.py check` against the `it` keymap: è/é on code 26, @ # € with AltGr, [ ] { } with AltGr (and Shift), ~ on AltGr+ì; every label of `it.json` is checked by `test_osk.py`. Hyprland reports unset options as `[[EMPTY]]`, which libxkbcommon rejected as a variant until it was mapped to an empty string.
- Typing into a test Kitty window (focus checked first) gave `ciaoèé@` and Enter. A client that exits right after writing loses its keys; the shell keeps the helper running. The virtual keyboard shows in `hyprctl devices` as `hl-virtual-keyboard-python3.14`.
- Docked: windows shrank above the keyboard, keys centred at 1100 px on the 1728 px screen. Floating: centred near the bottom once the surface has its size (a position computed on map put it at the top left), framed with the window border.
- The assist menu has nine actions in a 3×3 grid with Keyboard first.
- After the first touch test the user asked for larger keys: docked 46 → 64 px (about a third of the landscape height), floating 42 → 56 px and 640 → 900 px wide, with larger labels, icons and strip.

## Automatic keyboard verification

- `osk.py run --input-method` alone: Kitty with the focus sent `activate` with purpose `terminal`; a `zenity --entry` field `activate` `normal`, then `deactivate` when it closed, and Kitty `terminal` again.
- Through the shell, with `desktop-shell tablet on`: the zenity field opened the keyboard by itself (`autoShown`), closing zenity kept it open for Kitty (its extra row shown), and `tablet off` closed it. In laptop mode fields do not open it.
- Entering tablet mode while a field already has the focus does not open the keyboard; the next tap into a field does.

## Touch-friendly shell verification

- `Theme` reads `Tablet.active` through `import "services"` without a singleton cycle. With `desktop-shell tablet on` the bar layer went from 38 to 48 px and the dock surface from 190 to 228 px; the Control Center switches, slider handles and buttons grew, text did not. `tablet off` restored 38 and 190.
- The notice swipe handler first sat on the notice itself, under the popup MouseArea, which accepts the press first, so a popup could never be swiped. It now lives inside the MouseArea (handlers of an item see the press before the item and can take the drag over); in the center the area accepts no buttons, so events still reach it.
- Long press and swipe need a touchscreen; they are left to the physical test (Phase 6).

## Tablet review (2026-10-29)

- **Assistant over the docked keyboard:** floating windows ignore a reserved area. `desktop_fit_floating()` in `rules.lua` (also on `monitor.layout_changed` and when the assistant opens) fits them into the monitor minus `monitor.reserved` (`{left, top, right, bottom}`, logical px); the keyboard window calls it 200 ms after it appears or goes. Docked (406 px reserved) the assistant went from 1036×756 at 346,181 to 1036×604 at 346,54, and back when the keyboard closed. Without the keyboard nothing moves.
- **Gestures:** edge swipes were not always recognised, so the map is now three fingers as on the touchpad and four for windows and the overview. `hl.dsp.window.move({ workspace = "r+1" })` and `focus` with `r±1` step to the neighbouring workspace, empty ones included.
- **Window menu:** on a test Kitty window `hl.dsp.window.float({ action = "toggle" })`, `fullscreen()`, and `move` to `r+1` and back all applied.
- **Fingerprint in tablet mode:** at the sudo prompt "Place your right index finger on the fingerprint reader", Ctrl+C sent by the virtual keyboard went on to "[sudo] password for angelo:" (fprintd-pam 1.94.5); a second Ctrl+C cancelled sudo. Polkit has no such escape and waits for the reader to time out, hence `tablet-auth.sh`. Its check answered 0 only for angelo in tablet mode (1 in laptop mode, for another user and for an empty `PAM_USER`), and the inserted line lands right before `pam_fprintd.so` in the `local` template.
- **Lock screen keyboard:** `keyboard locked` shows the docked keyboard only in tablet mode and `unlocked` hides it; locking for real is left to the physical test, since an unlock needs the password.
- **Workspace swipe in Zen:** the live `workspace` gesture follows the fingers and commits only past `gestures:workspace_swipe_cancel_ratio` (0.5) of the screen width, while the page under the fingers scrolls until Hyprgrass recognises the gesture. Hyprgrass recognises a swipe after `150 / sensitivity` px (about 37 px at 4.0) and then sends touch cancel to the app (`debug:send_cancel`, on). The touchscreen now uses discrete three-finger binds (`focus` to `r±1`), like the four-finger window moves; the touchpad keeps the live gesture and the global ratio, so its feel does not change.
- **Dock in tablet mode:** taps started a drag of pinned icons, as a finger moves more than the 6 px threshold while it taps; the threshold is 24 px in tablet mode.
- **Launcher in tablet mode:** its search field opened the keyboard, but a Top layer sits under the Overlay panels. The keyboard is now an Overlay layer and maps again over a panel opened after it; typing "zen" through a virtual keyboard filled the search and found Zen Browser.
- **Hold-to-talk:** Space held for 1.5 s through `press 57` / `release 57` gave 24 spaces in a test Kitty (client-side repeat), the repeat Claude Code reads as a held Space.
- **Dock still not tappable:** the assist button raised the dock in keyboard mode, whose full-screen `desktop-dock-keys` surface leaves a hole where the dock should be: the bottom of the screen minus the dock height. With the docked keyboard reserving the bottom, the dock sat at y 516 while the hole stayed near 852, so the surface covered the dock. The assist button now uses `Dock.request("touch")`: no keyboard surface, a 6 s timer restarted by each press on an icon, closed on activation, and the hover release ignored. Checked: only `desktop-dock`, above the keyboard, gone after 6 s.
- **Launcher closed and the assistant opened:** a tap on a key reached the launcher list under it ("AI assistant" is its second row). With the keyboard shown first, the launcher, and the keyboard re-mapped over it, the layers were stacked correctly and drawn so; since touch delivery could not be checked here, open panels now subtract `Keyboard.area` from their input region (docked: 0, 674, 1728×406, matching the layer; floating: its own rectangle).
- **Window menu not found:** there was nothing to see in tablet mode, only a long press on the title text. The app icon now shows in tablet mode, first placed after the title (it landed at the right end of the bar) and moved before it; `desktop-shell window-menu` opened the menu under it with Floating checked for the floating assistant.
- **Keyboard over the launcher, again:** with the keyboard rectangle out of the launcher input region, keys did nothing at all, which fits the touch going to the layer with exclusive keyboard focus wherever it lands (also the earlier tap that reached the list). In tablet mode panels and the polkit and Bluetooth dialogs now take the focus on demand; the launcher still got it on open, the field opened the keyboard, and typing filled the search.
- **Lock in tablet mode:** the posture file was rewritten `false` at 16:54:36 and hyprlock started at 16:54:38; Hyprland does not log bind commands, so `desktop-shell tablet` and `desktop-power lock` now log to the journal (`journalctl -t desktop-shell`). hyprlock showed its own fingerprint prompt, which PAM does not control; in tablet mode it now gets a config with fingerprint unlock off.
- **Lock screen keyboard, found:** the journal showed the lock starting in tablet mode (17:08:45) and the posture turning off only when the user opened the screen to type (17:08:55), so tablet mode was not lost. A self-unlocking Quickshell `WlSessionLock` test (3 s, with `misc:allow_session_lock_restore` on as a safety net, then off again) showed the docked keyboard over the lock, so `above_lock = 2` works. The keyboard had been opened by the focused text field (Kitty), and the lock taking the focus sent `deactivate`, which closed it. While locked it no longer closes by itself; with a zenity field open, the same test lock kept it on screen.
- **Password field under the keyboard:** the user unlocked by typing blind, as the field sat 180 px from the bottom. With the keyboard shown first, `keyboard.area` gave 406 px, and a first lift of 438 left the field level with the keyboard: hyprlock positions are physical pixels (406 logical × 1.667 ≈ 677). The lift is now the scaled keyboard height plus the field-to-user gap of the config (26) minus the field position: field at 703, user at 781; clock and date stay at the top.

## Control Center switches and Night shift verification

- The Control Center shows Do Not Disturb, Keep awake, Rotation lock and Night shift as a 2×2 grid of square tiles; before hyprsunset was installed the Night shift tile said "Install hyprsunset" and was disabled. Availability is probed at start and whenever the Control Center opens, so the install showed up without a restart.
- hyprsunset 0.4.0 (nett00n COPR): `night-shift on` started `hyprsunset -t 4000`, `hyprctl hyprsunset temperature 3000` answered `ok` while it ran, and `off` stopped it. Screenshots do not show the filter (it applies at scan-out).
- Automatic mode at 17:33 (window 20:00–07:00): off; a tap turned it on until 20:00 (`overridden`), a second tap off again; `off` cleared the override. `tst_night_shift.qml` covers the window across midnight and the next boundary.
- Writing `desktop-shell` left a stray `esac` for a few seconds, which broke the wrapper (and the Hyprland binds that call it) until the next save; `bash -n` caught it.

## Review batch A (bugs), 2026-10-29

- **Lock:** `desktop-power lock` bounds every call to the shell and hyprctl with `timeout 2`, and a failure of the tablet config script keeps the themed config instead of aborting the lock (a config with `size = 20%, 5%` made it exit 1; the real one still lifts the field to 703).
- **Notification history:** at load the live list was empty (the server restores after the file), so every reload archived the live copies again: the file held sources 21…1 twice and the duplicates pushed real history past the cap of 50. With the reconcile step: 21 live and 10 archived, unchanged over three reloads.
- **Helpers restart:** killing `hyprsunset`, `osk.py run` and `rotation.py watch` brought each back within 4 s (Timer while needed, running set imperatively, as a binding on `running` does not run a process again).
- **Polkit over the keyboard:** with the docked keyboard shown in tablet mode, `pkexec true` mapped `desktop-authentication` and the keyboard came back on top (`desktop-osk` last); Esc cancelled (exit 126). The prompts now share `KeyboardHole` with `Overlay`.
- **Window menu:** Floating unchecked for a new tiled Kitty, checked once floating (`refreshToplevels()` on open).
- **Dock menu with the docked keyboard:** opened with Shift+F10 in keyboard mode, it now sits above the raised dock (`Keyboard.reservedOn()`), as does the keyboard-mode hole.
- **theme.py:** a removed saved theme falls back to Graphite; a theme without 16 `ansi` colours is invalid instead of crashing the list; `{}` VS Code settings get valid JSON; `next_wallpaper` compares resolved paths (Graphite moved on from the stowed default); state-changing commands hold `STATE/.lock`. Regression tests in `test_theme.py`.
- Smaller: `desktop-theme window-style` forwarded; `osk.py` ignores out of range codes; `rotation.py` reports a failed accelerometer claim; `desktop-session` starts the daemons even if the theme or wallpaper step fails; the share picker no longer starts the rotation sensor (`Tablet.enabled`, set by `shell.qml`) and takes focus on demand without a focused field in tablet mode; the Night shift chevron no longer toggles; the automatic-mode tap survives a reload; `Tablet.sensed` resets on leaving tablet mode; a field-opened keyboard closes after unlock; second network profile request and wallpaper tone change queued; small state files load synchronously; menus keep their selection while entries rebuild; a long press on a dock icon no longer starts a drag; workspace pills take no focus; IPC `theming(tab)` validates the tab; `desktop_fit_floating()` leaves windows that still fit alone.
- Not changed: `dock.json` keeps `watchChanges`, so hand edits still apply live (documented).

## Review batch B (tablet experience), 2026-10-29

- **Panels and the keyboard:** with a field-opened keyboard (a zenity entry), opening the Control Center closed it; the launcher field brought it back; a keyboard opened by hand stayed with the Control Center. `Overlay` gives panels a stage above the docked keyboard (its height minus `Keyboard.reservedOn()`): on the internal screen the Control Center scrolled above it, Hints and Theming shrank to fit, the launcher sat above it with its touch hint.
- **Assist pages:** App, Window and System open from chips at the top of the menu (`desktop-shell assist menu window` for scripts); the menu keeps the height of the longest page. Window actions are dispatchers on the active window, which the button never takes the focus from; screenshots wait 250 ms for the menu to go.
- **Hints:** in tablet mode the touch gestures come first under "Gestures and shortcuts"; the keyboard opened by nothing.
- **Touch sizes:** expand chevrons and mute buttons in the Control Center, the notification Delete, the launcher logo, Network and Theming inputs, Theming font rows, Audio, Calendar and wallpaper picker rows now go through `Theme.hit`; side panels sit 20 px below the bar whatever its height.
- **Number fields:** Bluetooth passkey (`ImhDigitsOnly`), IP address, gateway and DNS (`ImhFormattedNumbersOnly`) open the keyboard on its numbers page.
- **Gesture:** a two-finger long press then drag moves the window (`hl.dsp.window.drag()` with `mouse = true`, from the Hyprgrass docs); to be tried on the screen.
- The keyboard is in the `no_anim` layer rule, so its re-map over a panel does not fade.

## Review batches D and E (docs, cleanup, i18n), 2026-10-29

- Docs: gestures in plugins.md, the transparent bar blur, history across restarts, `no_anim` coverage, window borders, PAM and `tablet-auth.sh` in integrations.md, roadmap lines.
- `check-i18n.py` now finds the keys after every `i18n.py` call in `shell/.local/bin/desktop-*` and `hypr/.config/hypr/config/*.lua` (desktop-power, desktop-ai, binds.lua today), and the shared-catalog test uses `network.passwordFor` with a `$&` argument.
- After the prefix-to-placeholder change, Python helpers call `tr(key, [value])`; Hints still built its 86 binds with the catalog modifier names; `qmltestrunner` 26 passed with `WorkspaceModel.fromHyprland`.
- Removed the dangling `~/.config/quickshell/desktop/assets/icons/wifi-weak.svg` link (its file left the repo); no other dangling link in the stowed directories.

## Review batch C (system choices), 2026-10-29

- GTK: `gtk-application-prefer-dark-theme=1` removed from both settings.ini; dark themes stay dark through GSettings `gtk-theme` and `color-scheme`.
- Secret portal: after `systemctl --user restart xdg-desktop-portal`, `org.freedesktop.portal.Secret` is on the portal object (it was missing).
- Environment: one `dbus-update-activation-environment` in `desktop-session` (the copies in `session.lua` and `desktop-theme` are gone), now with SDL, Clutter, the cursor size and `DESKTOP_AI_LANGUAGE`; an unset name is ignored (exit 0).
- Hyprglass follows the theme mode; the blur rule and the Hyprglass list now cover the same surfaces. The polkit prompt now blurs the whole screen behind it and the keyboard is glassed like the panels.
- hyprlock text through i18n: an Italian render gives "Tocca il sensore d’impronta per sbloccare"; the Graphite test renders as en_US.
- Touch and stylus by device: `hl.device` for the two ELAN devices; `getoption` cannot read device options; the user confirmed touch and stylus alignment after a rotation on the OmniBook.
- Electron: `electron.py apply` wrote the VS Code override and updated the hand-made ChatGPT entry (backup taken first); both validate; a VS Code started with the flags ran native Wayland, and its command palette activated the input method (purpose `normal`).

## Electron entry fix, 2026-10-29

- Electron: `stow.py dry-run` reported a conflict on `shell` because `electron.py` had replaced the ChatGPT link with a generated copy. `stow.py apply` backed the copy up (`~/.local/state/dotfiles/backups/20261029-191244-205186`) and restored the link; the repo entry now has the three flags, the same Exec line as the copy. `electron.py status` lists VS Code only (current), and `apply` left its entry untouched.

## Deferred cleanups, 2026-10-29

- `common.py`: `test_common.py` (new files 0644, replaced files keep their mode, links followed or replaced, a failed block leaves the old file and no temporary). Live: a wallpaper render into a scratch state directory gave the same digest name as the current one (`hyprctl` left out, so nothing was applied); a thumbnail was made at 0644 with no temporary left; `monitor_size` gave 1728×1080 and the tone mean 0.1197, both as in the live `tone.json`; `xwayland.py status` and an Aseprite ini write in a scratch directory; `gaming.focused_monitor` through the shared module.
- Menus on `MenuLayer`: the window menu from `desktop-shell window-menu` opened under the title with Floating checked and closed when a panel opened; `qs log` reloaded cleanly after each file.
- Control Center rows on `SwitchRow`: with `doNotDisturb`, `idle` and `rotation` added for the test, the open Control Center was pixel-identical with the old and the new files (ImageMagick AE 0 on the panel area); the module list was restored afterwards.
- `qt` package: `stow --delete qt` removed both links, the empty `colors` directories went with them, and `qt5ct.conf`/`qt6ct.conf` still point at `~/.local/state/desktop-theme/qt-colors.conf`.
- Bar double-tap: a qmltestrunner scene with the structure of the bar (a TapHandler under a Button and a MouseArea), with touch: a double tap on the button or the title toggled nothing and on the empty bar toggled once. QTest moves mouse timestamps apart on purpose, so a mouse double click could not be tested there.
- By hand, the user confirmed the tray and dock menus (open, close on an outside click, dock menu above the dock) and that a double click on a bar button leaves the bar style alone.

## Assistant console (phase 1), 2026-10-29

- Lua layout: `hl.layout.register("console", …)` works, but a workspace rule names it `lua:console`; with the bare name the workspace stayed on `dwindle` (`workspace.tiled_layout`). `ctx.area` is the usable area in global coordinates after the reserved space and `gaps_out`; `target:place()` applies the inner gaps (a 1250×625 box became 1242×621 at 243,42 on the 1728×1080 OmniBook with the bar).
- Do not switch `general.layout` to test a layout: it relaid every workspace and took Zen out of fullscreen on DP-1 (restored with `hl.dsp.window.fullscreen_state({ internal = 2, client = 2, action = "set", window = … })`). Test on a hidden workspace with a rule instead.
- Test windows: one window centred under the bar, two side by side across 96%; a window opened with the console shown landed on workspace 1 and the console closed; `desktop_console_move` moved a window in silently (`follow = false`) and back out; the dim measured about 40% darker on the wallpaper (mean 0.047 against 0.077); the catcher layer was mapped (Bottom, 1728×1080) only while the console was open.
- By hand (user): a click and a tap outside close the console, a workspace change closes it, `Super + Return` and the launcher open outside, `Super + Shift + A` in and out, animation and dim fine. In tablet mode a three-finger workspace swipe also closes it, as intended.
- Tablet keyboard: it did not open on the console. Kitty kept `purpose = terminal` while the console was hidden over an empty workspace, so showing it again sent no activate. With `Keyboard.qml` following `Agent.consoleOpen` (`desktop-shell tablet on` for the test), toggling the console showed and hid the keyboard (`autoShown`).
- `ConsoleCatcher` bound `visible` to `screen?.name`, which looped while mapping; the screen name now comes from the `Variants` model.

## Assistant state, usage and panel (phases 2 and 3), 2026-10-29

- Hooks through `--settings` on Claude Code 2.1.312: a one-shot `claude -p` with every planned event (including `PermissionDenied`, `PostToolUseFailure`, `StopFailure`) accepted the settings and logged `SessionStart startup`, `UserPromptSubmit`, `Stop` with `last_assistant_message` and `SessionEnd other`. The status line runs only in the interactive TUI: `test_agent.py` covers it with the documented JSON, and the real check is the next console session.
- `test_agent.py`: a turn through ready, working, permission (with the command), working, finished, and removal at the end; an older event never overwrites a newer one; idle and unknown events change nothing; the hook prints nothing and exits 0 on garbage; the status line keeps the last limits until new ones arrive and reports an expired window as unknown.
- Shell: with sample files the panel showed the plan (Max 5x), the meters (91% in red) and the model and context; a written `permission` state with the console hidden raised the notification "Claude is asking for permission · Bash: rm -rf build" with Open console. `desktop-shell status` has an `agent` block.
- QML: `escape` is not a valid method name (a global JavaScript function) and broke the whole shell reload ("Illegal method name"); inside an animation `parent` is undefined, so the bar dot uses its id.- Live, in a console session started with the new settings (`/resume` brought the conversation back): the panel showed 5 hours at 8% and the week at 0% with Max 5x, Opus 5.5 at 45% context, matching the status line; the hooks wrote `working` during a reply. The user confirmed the finished and permission notifications, Open console, and the keyboard opening with the console in tablet mode. The assistant left the dock (pins and running window), its bar icon replaces it.

## Code quality and system updates, 2026-10-29

- `pragma ComponentBehavior: Bound` on `Bar`, `TrayMenu`, `WorkspaceStrip`: the shell reloaded without warnings; bar, tray (1Password) and workspaces drew as before. `Notice.qml` no longer warns when a notification closes (its object goes null before the delegate): an expiring notification added no warning.
- `install-hypr-plugins.py` outside the session now says "Run this from inside the Hyprland session"; a non-JSON reply names the command and its output.
- Updates: `dnf repoquery --upgrades` with a `queryformat` replaces parsing `check-update`; dnf5 does not expand `\t` in the format, so `updates.py` passes a real tab. A first check took about 7 s and found nothing (as `dnf check-update --refresh`); the timer was scheduled 5 minutes after start. With a sample list containing Hyprland, the bar showed the count, the notification and the panel flagged Hyprland, and the panel listed both sources.
- Notification icons: with libnotify 0.8.9 `notify-send --icon` sends the image hint, and the small app icon our popups draw comes from `--app-icon`; the assistant and update notifications now use `--app-icon` (the assistant one had shown through its desktop-entry hint).

## Tablet follow-ups, 2026-10-30

- Gestures: `wev` on a test window and a page logging events in Zen show every gesture as down, 100-400 ms of motion, then `wl_touch.cancel` (`pointercancel`/`touchcancel`, never `mousedown` or `click`). Fingers land within about 25 ms. The YouTube player still reacted, probably to `pointerdown` or to the cancel itself (not verified on YouTube); a test build that cancelled at the third finger did not stop it, while delivering nothing at all did.
- **Do not swap a Hyprland plugin in the running session.** `hyprctl plugin unload` followed by `plugin load` of a test build of hyprgrass worked once and crashed the compositor the second time (SIGSEGV, null read in `pluginInit`). The core dump shows the unloaded `/var/cache/hyprpm/.../hyprgrass.so` still mapped: its 86 unique symbols, `g_config` and `g_pGestureManager` among them, keep `dlclose` from removing it. The exact path to the null pointer was not established. After a crash `start-hyprland` restarts with `--safe-mode` (no user config, no plugins, no shell); a new login restored the normal session with the installed plugins.
- A hold check based on `m_foundLSToFocus`/`m_foundWindowToFocus` never held anything in the first test build, so the patch hit-tests the touch point instead.
- The patch was verified in a nested Hyprland (`LIBSEAT_BACKEND` set to an invalid name so it cannot take a session or the GPU, `HYPRLAND_NO_SD_VARS`, `HYPRLAND_NO_SD_NOTIFY`, a private bus and temporary XDG directories) with a small plugin that registers a simulated `Aquamarine::ITouch` and `updateCapabilities()`, and `wev` as the client. The unpatched plugin reproduced the sequence of the real panel. With the patch, 20 of 20 scenarios passed: gestures and long presses deliver nothing, tap, scroll, pinch and two-finger tap arrive whole, a late third finger cancels, shell layers get no delay, and touches with no window under them are harmless. That simulator is not kept in the repository.
- Physical test: the built plugin replaced the installed file with `install` (the running compositor keeps its copy) and loaded at the next login. Gestures no longer disturb Zen or YouTube, confirmed by the user. `build.py` then produced a byte-identical `hyprgrass.so`.
- After the new login Quickshell did not reload on edits made with the Edit and Write tools, though it had earlier the same day; the cause was not established. Check for "Reloading configuration" in the log, and force it with an in-place change to `shell.qml` (the conventions describe it).
- Decks, in an isolated instance (a `shell.qml` with only the popups and the center, `dbus-run-session`, temporary `XDG_STATE_HOME`, `QT_NO_XDG_DESKTOP_PORTAL=1` so a private bus starts no portals; screenshots with grim): closed and open decks, a lone `notify-send` card, countdowns paused past their timeout while open, a card held back and released, expiry, the center with stacks closed and open. Found there: hiding a popup destroys its delegate, so the timer must finish its work first. Hover and tap were scripted through `hold()`, not done physically.

## Keyboard prediction analysis, 2026-10-30

- Probe in a nested Hyprland: an input method built on `osk.py` that logs `surrounding_text` and sends `delete_surrounding_text` + `commit_string` ("ciao cas" to "ciao casa "). GTK4 (Text Editor) and Qt6 (Quickshell `TextInput`) report the text and take the commit. Kitty reports nothing and ignores the delete (the result was "ciao cascasa "). VS Code reported a single unusable string ("ciao cassac oaic") and the outcome of the commit was not established. Zen never activated its field in the nested session, so nothing is known about it yet.
- Engine: sorted words, `bisect` on the prefix, a scan of the range. 50,000 words add about 15 MB of RSS, median lookup 1 µs, worst 0.25 ms; 200,000 words add 48 MB. The helper uses about 15 MB today.
- Test text: four Italian Wikipedia articles (47,699 words), the Italian catalog (2,079) and 313 words typed by the user. Keystrokes saved with three suggestions, a ceiling assuming every suggestion is seen and tapped: 29.7%, 27.9%, 30.8%; words outside the list: 8.4%, 15.5%, 10.2%. Next letter in the top 1 / 3 / 5: about 46 / 72 / 82%.
- Touch errors per letter with docked keys, simulated with Gaussian offsets, full Bayes and a probability floor of 0.02: none at 1.5 mm; 0.66-1.0% down to 0.13% at 2.5 mm; 3.9-4.2% down to 1.3-1.5% at 3.5 mm. Right keys turned wrong: 0.02-0.29%. The real spread of fingers on this panel is not known, and the floating keyboard was not simulated.
- Languages: FrequencyWords has the same list for English. Share of keystrokes saved at most / next letter in the top 3, for the Italian list, the English list and the two merged (each word by its share of its language): Italian Wikipedia 30.8/73.3, 3.2/48.0, 27.7/68.9; the messages of the user 30.8/69.7, 3.3/47.2, 28.2/68.0; English Wikipedia 8.9/49.1, 35.3/71.1, 30.5/69.1; the English docs of this repository 6.2/47.4, 27.6/68.2, 24.2/65.8. Merged: 83,973 words, 72 ms to load, about 10 MB. A list in the wrong language is almost useless; the merged one loses 2-5 points on either.
- Phase 1, the rule as shipped: real key rectangles, a gain of at most 0.2 of the key height (12.8 px docked), probability floor 0.02, merged lists, typed prefix. Simulated errors per letter on the messages of the user and on Italian Wikipedia: none at 1.5 mm; 0.85% to 0.46% and 0.72% to 0.46% at 2.5 mm; 5.01% to 3.19% and 4.37% to 3.08% at 3.5 mm; right keys turned wrong at most 0.08%. A gain of 19 px brought little more and up to 0.33% of damage. The earlier Bayes figures measured distance from key centres, which would let a letter take touches visibly inside its neighbour: they do not apply.
- The engine on the real lists: 83,973 words, 79 ms and about 15 MB on first use, then 1 ms at worst per lookup. `import urllib` alone added 8 MB to `osk.py`, so `fetch()` imports it itself.
- `Config.oskTouchStats` keeps five totals in `session.json` (`oskTouch`), never a letter or a time; `desktop-shell status` shows them under `keyboard.touch` in pixels (1 px is about 0.18 mm).

## Hyprland 0.57, 2026-10-30

- Before touching the system: `hyprland-devel` unpacked into a scratch folder and a `hyprland.pc` pointing at it let every plugin compile against 0.57 headers at its new pin. `hypr-hot-edge` fails: `managers/KeybindManager.hpp` and its dispatcher map are gone from 0.57, 13 errors remained once those were cut, and the compiler falls back on the system headers of the older version, which looks like an environment problem. It was replaced by a hover area of the bar.
- The GDM session runs `hyprland-uwsm.desktop`, which this COPR ships in the weak dependency `hyprland-uwsm`: `install_weak_deps=False` would break the login.
- After `distro-sync`, from the old session: `--verify-config` on the installed 0.57; in a nested 0.57, the touch lab with the plugin from `build.py` (19 of 19 scenarios) and the four plugins with the real `plugins.lua` and the whole shell on the new Quickshell (no config errors, the overview opened and closed; the only warning was the second polkit agent). `--verify-config` skips the plugin blocks, so only the nested run covers them. The lab lives in `~/.local/share/dotfiles/hyprgrass-test/touchlab/`, outside the repository.
- The new build reports its real commit, so the ABI hash differs from the cache and the installer refuses it: reset `/var/cache/hyprpm/$USER` after logging in on the new version, then run the installer. The first login comes up without plugins, which is expected, and no plugin is loaded when the installer loads them.
- The old 0.56 compositor segfaulted at 20:08:30, ten seconds before the login on 0.57, with its binary and libraries already replaced on disk. The cause was not established, and 0.57 has not crashed since.
- Confirmed by the user on the panel after the move: hyprlock, gestures on YouTube, the hot corner in the bar. Screen sharing on the new portal (1.5.0) is still to be tested.

## Keyboard suggestions, 2026-10-30

- End to end in a nested Hyprland: the real keyboard and a Qt text field, with the simulated touchscreen tapping the keys and the suggestion chips (`touchlab/osk/run.py`). Typing, a suggestion with its space, `perche` to `perché`, an English word, a capital kept and Backspace before a suggestion all reached the field. The lab has to set `kb_layout = "it"`: on the default layout `é` came out as `{`, since the keyboard follows the keymap of the compositor.
- Word lists from subtitles drop accents: `perche` outnumbers `perché`, and `perchè` is common. Comparing pairs, a needed accent is at least half as common as the plain form (perché 85%, già 80%, città 100%), a real second word much less (là 1%, sì 32%, è 35%).

## Touch on clients without wl_touch, 2026-10-30

- Kitty (0.47 and 0.49) never calls `wl_seat.get_touch`: the seat announces touch, `glfw-wayland.so` has no `wl_touch` code, and a finger reached it only as the pointer warp of hyprgrass. No Kitty option changes this.
- Fixed in the Hyprgrass patch, tested in a nested 0.57 with `touchlab/kitty-probe.py`, which reads the Wayland traffic of Kitty: a drag gives axis events and no button, a tap gives press and release, three fingers give neither.
- Two traps: `windowAt()` needs `RESERVED_EXTENTS | INPUT_EXTENTS | ALLOW_FLOATING`, as `FOCUS_PRIORITY` alone finds no window; and `forwardTouchUp()` reports blocked when the touch has no surface, which is always true for such a client.

## Keyboard learning, 2026-10-30

- End to end in a nested Hyprland with the real keyboard (`touchlab/osk/run.py`, 17 of 17): a word counted once at a space, offered after two uses, forgotten by holding its suggestion with nothing typed; the file at mode 0600 with sorted keys. A word typed in a Qt password field and one typed in Kitty reached those fields and did not reach the file. Fields that report no purpose were not exercised: `Keyboard.learning` excludes them by reading `purpose`.
- With a full memory of 5,000 words: 1.4 ms to learn, 8 ms at worst for a lookup. `letters("")` is worked out once at load, as it covers every word and is needed after each word.

## GitHub Actions, 2026-10-30

- The commands of `.github/workflows/check.yml`, read from the YAML and run in a fresh `fedora:44` container with `CI=true` and `HOME=/github/home`: `check.sh` passes, 138 Python tests (1 skipped, as matugen is not installed), 49 QML tests, and Hyprland 0.57.0 from the COPR accepts the config without plugins. This container stands in for the GitHub runner.
- Hyprland refuses to start as root and needs `XDG_RUNTIME_DIR`, so the job runs `check.sh` as a normal user with its own runtime directory.
- Without Stow, `i18n.py` finds no catalogs under `~/.config`, and `test_theme.py` compared raw keys: it now reads the catalogs of the tree.
- `check-links.py` on a damaged copy: found a missing image in `src="..."`, a missing file and a missing heading, and ignored a link inside inline code.
- After the review of that commit: `test_real_matugen_output_converts` fell back to an SVG that matugen cannot read, so `check.sh` failed with matugen installed and no JPEG wallpaper (reproduced with an empty `HOME`). It now uses the bundled `desktop-night.jpg`, and CI installs matugen. The same workflow commands in a fresh container: 149 Python tests, none skipped, 49 QML tests, config accepted.
- `scripts/tests/test_links.py`: ten defects put back one at a time into a copy of `check-links.py` (titles, `src`/`href`, leaving the repository, followed symlinks, schemes, leading slash, headings, repeated headings, code, exit code), and the tests caught all ten.

## Doc checks on GitHub's Markdown engine, 2026-10-31

- `check-links.py` now reads the pages through `python3-cmarkgfm`, GitHub's own engine, instead of regular expressions. Compared with what GitHub's markdown API returns for all 19 pages: the same 186 ids and the same 113 internal links. The only difference is that GitHub wraps each README image in a link to itself.
- `scripts/tests/test_links.py`: 26 tests. Twenty defects put back one at a time into a copy of the script, all caught; the first round missed three, which added a test that only GitHub's table rules pass, a test for stale catalogs, and removed a `pre` check that did nothing.
- On a damaged copy of the real docs it found a heading faked inside a `~~~` block, a broken reference link, a wrong path in inline code and a stale doc path in a catalog.
- `roadmap.md` and `verification-log.md` are exempt from the inline path check: they are history and name paths that are gone. Their links are still checked.

## Installer on Fedora 45, 2026-10-31

- `scripts/tests/install-container.sh` in a fresh `fedora:45` container, with weak dependencies off to prove the manifest is explicit: `apply --profiles core,hardware,plugins` installs and links everything, a second `apply` says "Nothing to do", `ffmpeg-free` and `power-profiles-daemon` stay out, `check.sh` passes on Python 3.15 (223 Python tests, none skipped, 49 QML tests), and Hyprspace, hyprgrass, hyprglass and HyprCapture all compile against the `fc45` headers. Packages are from pre-release repositories. With `apps` as well: 1,389 packages from the vendor repositories, COPR and RPM Fusion, also repeated at nothing to do. GDM, the firewall, Flatpak and the plugin session were not exercised: a container has no systemd.
- `test_install.py`: 59 tests. Forty-eight defects put back one at a time into a copy of the script, all caught; the first round missed four, among them two refusal tests that passed only because this laptop is Fedora 44.
- The first real run failed in the preview, where `systemctl` was not installed yet: a missing tool is now an empty answer.
- Secret portal, each on a private bus: with `oo7-portal;gnome-keyring`, Fedora 44 still picks `gnome-keyring.portal` and Fedora 45 picks `oo7-portal.portal`; with the old line, Fedora 45 has no Secret backend at all. On Fedora 45 GDM's PAM files moved to `/usr/lib/pam.d`, and `gdm-password` carries both `pam_oo7` and `pam_gnome_keyring`. Unlocking at login is untested.
- `allow_vendor_change` is not set on Fedora 45.
- The pre-release `fedora:45` image has `updates-testing` on, until the upgrade step brings the final `fedora-repos`, which turns it off: what came from there is then newer than any repository. `dnf` downgraded 16 packages, `glibc` among them, and the transaction failed with `apps`. A released Fedora starts with it off, so the container test now does too.

## Installer in a VM with Fedora 45 Server, 2026-10-31

- QEMU with UEFI and the `45_RC-1.4` Server ISO, checksum verified, installed with a test kickstart and the guided layout: `/` of 15 GiB on LVM and XFS, `git` missing, Python, Wi-Fi packages and `iwlwifi-mld-firmware` present, `updates-testing` off, `sshd` and `cockpit.socket` on, zone `FedoraServer`, authselect `local`.
- The preview warned of 12 GiB free, and the command it printed grew `/` as it was. `apply` with all four profiles took 7 min 42 s, a second run said "Nothing to do", and the system used 29 GiB with SELinux enforcing. The repository was copied in, not cloned, and sudo needed no password. In this VM only, sshd was turned back on and the plugin guard accepted `fc45`.
- GDM came up with `hyprland-uwsm` preselected, and signing in by typing the password reached Hyprland, the bar and the dock. With software rendering the terminal opened by itself, `post` stopped at the hyprpm confirmation, built and loaded the four plugins, listed the manual steps and removed its autostart. After a reboot the plugins loaded and the terminal stayed away. The idle lock came up, and the password unlocked it through the new authselect profile.
- **Found and fixed:** `oo7-daemon.service` is disabled on Server, where no preset turns it on, and it has no D-Bus activation, so `org.freedesktop.secrets` did not exist and `pam_oo7` timed out at login. It is now enabled for every user. After the next login the collection was unlocked with no prompt, and `secret-tool` stored and read a value.
- **Limits of the VM, not of the desktop:** with the virgl GPU, kitty finds no EGL config and the transparent parts of the bar and dock layers are black; with software rendering, hyprpaper crashes, as hyprtoolkit cannot allocate a GBM buffer. Fedora 45's kitty and Mesa 26.2.3 in a container opened on the laptop's real Intel GPU with `background_opacity 0.94`, on this laptop's Fedora 44 Hyprland. Fedora 45's Quickshell and hyprpaper on real hardware are still to be seen.
- Not covered: Wi-Fi, fingerprint, rotation, audio hardware, touch, screen sharing and the final Fedora 45 repositories.

## Workspace scroll past the last pill, 2026-11-01

- `tst_workspace_model.qml` covers the new id and the scroll target, and `check.sh` passes.
- An isolated `qs` instance ran the real `scroll()` of `WorkspaceStrip`, without the pills: wheel and pixel deltas forward on an occupied last pill open the new id, half a pixel step does nothing, and an empty last pill, the first pill scrolling back and `scrollEnabled: false` all stay put.
- The session shell restarted on the new code with a clean log and a bar on both monitors.
- **Found:** the edits did not reload the running shell. Saving by writing a new file and renaming it over the old one gives the file a new inode, the watch on it is lost, and the log shows no new `Configuration Loaded`. `touch` on a file still watched did not reload it either. `desktop-shell restart` loaded the new code.
- This system has no tool to inject scroll events, so the owner tried it by hand on the live bar and confirmed that it works.

## Hyprland 0.57.0-2 and libheif 1.23.7, 2026-11-03

- `dnf upgrade` did nothing: `libheif-freeworld` 1.23.6 from RPM Fusion requires exactly `libheif` 1.23.6, Fedora shipped 1.23.7 (a high-severity security update, stable on 2026-11-01), and `hyprgraphics-devel` 0.6.0 needs `libheif-devel`, which exists only at 1.23.7, so the whole Hyprland stack was held back as well. `--allowerasing` does not help; `dnf do --action=remove libheif-freeworld --action=upgrade libheif libheif-ffmpeg` updated libheif alone. Reinstall `libheif-freeworld` once RPM Fusion rebuilds it for 1.23.7.
- The COPR rebuild `0.57.0-2` keeps the commit but moves to aquamarine 0.16 and hyprgraphics 0.6, which are part of the ABI hash (`_aq_0.16_hu_0.14_hg_0.6_hc_0.1_hlg_0.6`). After the upgrade and a reboot the session came up without plugins, as expected; the pin in `build.py` moved to `0.57.0-2`, the hyprpm cache was reset and the installer rebuilt and loaded all four plugins with no config errors. The installer needs a real terminal: `sudo` cannot ask for the fingerprint from Claude Code's `!` prompt.

## GTK 3 dark dialogs and Bluetooth volume, 2026-11-03

- File chooser opened through `org.freedesktop.portal.FileChooser.OpenFile` and captured with grim: tiled to the full workspace and light (`#f6f5f4`). A GTK 3 `FileChooserDialog` from Python was light too, even with `gtk-application-prefer-dark-theme`, while `GTK_THEME=Adwaita:dark` was dark: `Adwaita-dark` resolves to no theme on Fedora 44, so GTK 3 falls back to light Adwaita. `adw-gtk3-dark`, unpacked into a scratch `XDG_DATA_HOME` first and then installed, renders dark with the theme palette (`#191a1d`). With the `portal-file-chooser` rule the dialog floats, centered, 864×648 logical px on the 1728×1080 laptop panel. The keyring unlock prompt (`gcr-prompter`, GTK 3) was not opened again: it uses the same theme, so it should follow; to be confirmed at the next unlock.
- JBL TUNE760NC on A2DP (AAC): `wpctl set-volume` changed the route volume while `softVolumes` stayed 1.0 and the BlueZ transport `Volume` stayed at 96/127, so the level never reached the headset. That connection began with `bluetoothd` reporting "Hands-Free Voice gateway profile connect failed ... Operation already in progress". A rule with `bluez5.hw-volume = [ hfp_ag hsp_ag ]` made PipeWire scale the stream and worked, but once it was removed and WirePlumber restarted, hardware volume worked as well (transport 38, 76, 57 for 0.3, 0.6, 0.45; `softVolumes` 1.0), confirmed by ear by the user. The rule was dropped: the fault was that connection's state, not the headset. Not reproduced on purpose.

## Hyprland 0.57.1-1 and the Glass themes, 2026-11-03

- After the COPR moved to `0.57.1-1` (commit `acc1aa0`, ABI `acc1aa0…_aq_0.16_hu_0.14_hg_0.6_hc_0.1_hlg_0.6`) the session came up with no plugins: `hyprpm list` showed all four enabled, `hyprctl plugin list` none, and the guard in `plugins.py` had stopped on the stamp, still `0.57.0-2`. Working as intended.
- The four pinned revisions, the Hyprgrass patch included, were built in a scratch copy against the system 0.57.1 headers before the pin moved: all four compile, and Hyprspace, Hyprglass and HyprCapture embed the new commit. The pin in `build.py` moved to `0.57.1-1`.
- Glass and Glass Light: both render, pass `test_theme.py` (the first Glass Light accent, `#007aff`, failed the 4.5:1 text check at 4.0:1 and became `#006be0`), and `check.sh` passes. Graphite and the other themes render `glassStyle = "desktop"`, so their look is unchanged.
- With the plugins loaded, the first `liquid` preset read as plain blur: the Control Center card (55%) under its tiles (55%) stacked to about 85% opacity and hid the glass, while `hyprctl hyprglass stats` showed the layer drawn with `contour_build` running. Card fill down to 30%, tiles and hover as a 7–12% white veil, blur 0.7 → 0.45, lens rim 18 → 30 px with `edge_height` 44 and refraction 1.4, and a darker dark-mode backdrop: grim captures show the terminal text through the card and bent at its rim, with the panel text still readable. Glass Light got the same treatment and is not yet seen on screen.
- Owner's call after trying it: no grain and a stronger lens. `noise_strength` 0, rim 40 px with `edge_height` 60, refraction 1.8, chromatic aberration 0.5, `fresnel_reflection` 0.6; blur and fills unchanged. The grim capture shows the deeper rim bending the text behind the card.

## Glass settings and window gaps, 2026-11-03

- `theme.py glass --option refraction_strength --value 2.4` wrote `{"glass": {"glass": {"refraction_strength": 2.4}}}` and `refraction_strength = 2.4` into the rendered `glassTuning`; Hyprland reloaded with no config errors; `--reset` removed the entry and brought back 1.8. `window-style --gaps-in 8 --gaps-out 12` gave `hyprctl getoption general:gaps_in` 8 and `gaps_out` 12; the preferences were restored afterwards (4 and 4).
- The live Theming panel showed the Gaps and Screen margin rows and the glass-settings button on the Glass card; the glass page itself could not be opened over IPC (it is not a tab) and is still to be tried by hand. `test_theme.py` covers clamping, per-theme values, themes without liquid glass, dropped defaults, gaps, and that `GLASS_TUNING` matches the `liquid` preset.
- Dynamic palette styles: matugen 4.2.0 on the current wallpaper gives five different palettes, but the surfaces stay within a few steps of near-black and mostly the accent moves (expressive turns it green, fidelity the link orange). A change regenerates only while the dynamic theme is the current one; with another theme it is only saved.
- Glass page tried with a virtual absolute mouse on `/dev/uinput` (the user has an ACL on it; a throwaway script in the session scratchpad, not in the repo). The gear on the Glass card opens the page; Reset to defaults clears the entry; one drag on Refraction saved 1.5 on the first release and the slider stayed there; a plain click on the Colour fringe track saved 0.3; two drags 0.15 s apart (rim width, highlight) both saved. A commit (`theme.py glass`) takes about 0.3 s. Two earlier faults, both fixed: the card MouseArea covered the gear button (now `z: -1`), and on release the value Binding snapped the slider back before the commit compared it, so nothing was saved (the slider now holds its value from the first move until the saved one returns, and rows are indexed so they survive a refresh).

## Frozen backdrop under shell panels, 2026-11-03

- Reported with a screenshot: through an open panel the video behind did not match the rest of the screen, even with every glass slider at 0. A throwaway kitty window printing a counter every 50 ms under the panels (counter rows compared 0.7 s apart): with no panel the rows changed; under the Theming, Hints and Audio cards they did not, with any glass values, with `mask_mode` auto, alpha or contour, and `hyprctl hyprglass stats` counted only cache hits (about 140/0). With Hyprglass disabled, Hyprland's own layer blur showed the same frozen backdrop, `new_optimizations` off included; a minimal Quickshell overlay with no layer rules updated, and the same overlay with only `blur` barely did. Windows themselves kept rendering (the counter row outside the card advanced). Only `layers.force_live_resample = true` made the backdrop follow.
- `force_live_resample` is now on in `plugins.lua`. Under the Hints and Theming cards the counter advances through the glass (for example 51 → 66 in 0.7 s). Hyprland CPU went from about 12.4% to 13.8% in a short sample; battery watts update too slowly here to measure the power cost. Not reported upstream yet.
- The assistant console (`special:ai`) and any translucent kitty had the same fault on window glass: with a counter window behind, a static part of the console (its status line) and a translucent kitty on workspace 1 did not change, and `hyprctl hyprglass stats` counted only window cache hits (231/231, 270/270). So it is not the special workspace. With `windows.background_cache = false` the counter shows through both (195 changed pixels on the console's static rows; the digits visibly move through the terminal).

## Dynamic palette style removed, 2026-11-04

- The Palette chips, `--scheme`, `SCHEMES` and their catalog keys are gone; matugen always runs with `-t scheme-tonal-spot`, the style that was saved. `theme.py dynamic --mode dark` left `{"mode": "dark"}` in `preferences.json` (a saved `scheme` is dropped on the next save), `--scheme` is refused, and the restarted shell shows the Dynamic mode row alone with a clean log. `check.sh` passes.

## Shell radii and Glass notifications, 2026-11-04

- At rounding 20 (set for the test, then back to the owner's 0): a popup notification and the Control Center card show the same corner as the Zen window next to them, and their Hyprglass rim follows it (contour masks follow the drawn shape; window glass follows `decoration.rounding`). Before, top-level surfaces scaled 18, 12 and 10 from the design size, so at 16 a panel had 18 px and a toast 10 px.
- Glass popup notifications over a white page: with `raised` (white 12%) the body text vanished and the card stayed under the 0.2 glass mask threshold; with `shell.notice` `#1c1c1eb8` it reads clearly and gets its own glass rim. Other themes render `notice` equal to `raised` (Theme.qml fallback matches Graphite). `check.sh` passes.
- The dock still showed two borders at rounding 0: its square 1 px QML stroke and a rounded line inside it. With layer glass off (`layers.enabled = false`) the line went away; with `bevel_strength` 0 too; with `edge_thickness_px` 8 it hugged the corner. It is the Hyprglass bevel of contour glass, whose corner follows the smoothed contour (sigma 0.3 × rim width, at most 12 px, `Contour.hpp`), about 24 px at the 40 px default, so it only matched near rounding 20. Shell layers now use `liquid-surface` (liquid without the bevel): one border at the window radius, glass still drawn. Windows keep the bevel. Also found: a preset redefined with `hyprctl eval` does not reach layers already configured; tuning through `theme.py glass` (config reload) does.

## Theming options as drop-downs, 2026-11-04

- Bar style, window corners, border, gaps, screen margin, dynamic mode, font size and shell icons are `ChoiceCombo` drop-downs. In the restarted shell each shows its current value; with the virtual mouse the Gaps drop-down opened with 4 highlighted, choosing 8 gave `general:gaps_in` 8 and `gapsIn: 8` in `preferences.json`, the reopened list marked 8, and choosing 4 restored it. `check.sh` passes.
- **Found:** restarting the shell before `stow.py apply` left it down for about a minute (`ChoiceCombo is not a type`: the new file had no link in `~/.config` yet). A new QML file needs the stow step before the shell can load it, as the workflow says.

## Installer on the final Fedora 45 repositories, 2026-11-04

- `scripts/tests/install-container.sh` in the released `fedora:45` image (`fedora-repos-45-1`) with `PROFILES=core,hardware,plugins,apps` and `COMPILE=1`: the preview changed nothing, `apply` installed 1,402 packages, `ffmpeg-free`, `libavcodec-free` and `power-profiles-daemon` stayed out, a second `apply` said "Nothing to do", and `check.sh` passed with the same qmllint warnings as on Fedora 44.
- Versions: Hyprland and `hyprland-uwsm` 0.57.1-1.fc45, Quickshell 0.3.2-6 (git 9b0f339), kitty 0.50.0, matugen 4.2.0, GDM 51.0. Authselect `custom/desktop-tablet with-fingerprint`, `oo7-daemon` enabled for every user, `oo7-portal` the only Secret portal, `gdm-password` with both `pam_oo7` and `pam_gnome_keyring`, `allow_vendor_change` not set.
- Hyprspace, hyprgrass, hyprglass and HyprCapture compiled against `0.57.1-1.fc45` with no unresolved libraries; `scripts/hyprpm/build.py` now accepts that build next to the fc44 one, and the container script rewrites the new `VERIFIED` tuple.
- The `google-chrome-stable` scriptlet could not import its key while the transaction held the RPM keyring lock ("key 1 import failed"); the package installed. On real hardware, check `rpm -q gpg-pubkey --qf '%{SUMMARY}\n' | grep -i google` after the install.

## The laptop on Fedora 45, 2026-11-04

- Clean install (Everything netinstall, Minimal Install, then `install-desktop.py apply --profiles core,hardware,plugins`; `apps` was stopped halfway and is being reviewed).
- Working on the hardware: Wi-Fi, audio, touch, screen sharing, the transparency of the bar. The Chrome key check is no longer needed.
- Fingerprint: not enrolled yet.
- Rotation: not working. The HP firmware `ish_lnlm_12128606.bin` is in `/lib/firmware/intel/ish/`, but the kernel loaded the generic `intel/ish/ish_lnlm.bin` ("ISH loader: cmd 2 failed 10") at 22:54:51, from the initramfs. The initramfs was built at 22:06, before the firmware was copied at 22:51, so it does not contain it. With no accelerometer, `iio-sensor-proxy` exits and the Control Center shows no rotation lock.
- Fedora 44 dropped from `check.yml` and from `VERIFIED` in `scripts/hyprpm/build.py`. The plugins already built keep loading at login; the next `install-hypr-plugins.py` run needs `hyprpm remove dotfiles-desktop` first, as with every change in `scripts/hyprpm/`.

## Opt-in profiles and no user name, 2026-11-04

- The `apps` profile installed everything; it now holds Zen, 1Password, VS Code, Neovim, `gh`, `glab`, `uv`, `gcc`, `fzf`, zsh, `xclip`, `wev`, `unrar` and `fuse-libs`. New opt-in profiles: `containers`, `media`, `gaming`, `steam-hidpi`, `codecs`. Chrome (and its repository), GNOME Text Editor, FreeRDP and every Flatpak are gone from the manifest. `xclip`, Loupe and Papers are not called by the shell (checked with `rg`).
- New `swaps` key and step, before `packages`: `codecs` swaps `ffmpeg-free` for `ffmpeg` and `libva-intel-media-driver` for `intel-media-driver` (`dnf swap --allowerasing`), and `plugins` swaps `ffmpeg-free` too, since `ffmpeg-devel` conflicts with it on Workstation. `hardware` no longer needs RPM Fusion: aptX and the nonfree Intel driver moved to `codecs`.
- `steam.desktop` moved to the optional `steam-hidpi` Stow package (`stow.py --with steam-hidpi`); on this laptop the dangling link was removed and the new one created.
- No user name left: the desktop entries call `desktop-ai` and `desktop-steam` by name, the Bluetooth agent path is `/org/dotfiles/Desktop/BluetoothAgent`, and the installer warning about another home is gone. Quickshell ran with `PATH=/usr/local/bin:/usr/bin`, so `session.lua` now prepends `~/.local/bin` once: after a live reload and a second `hyprctl reload`, a command started by Hyprland saw `/home/angelo/.local/bin:/usr/local/bin:/usr/bin`, and the shell restarted from Hyprland loaded with the same `PATH`.
- `./scripts/check.sh` passed (70 installer tests). The dry-run with every profile on this laptop listed only `libva-intel-media-driver -> intel-media-driver` and `gstreamer1-plugin-libav`.
- GNOME apps in the launcher: GDM requires `gnome-shell`, which requires `gnome-control-center` and, with it, recommends `gnome-tour`, `malcontent-control`, `gnome-color-manager`, `gnome-remote-desktop` and `rygel`. Those five are now in `exclude` of `core` (passed to `dnf install --exclude`) and removed on this laptop. Settings stays installed but out of the launcher (`launcherHidden` in `Config.qml`), with OpenCASCADE Draw from `opencv-devel` and `uuctl` from uwsm; the shell reloaded cleanly. Calculator and Online Accounts stay in `core` and visible, by choice.
- Launcher wider than its card (Tokyo Night, Fira Code): the hint line had no width, so its 642 px implicit width widened the whole `ColumnLayout`, search field included, past the 560 px inside the card. Reproduced with `qmltestrunner` (offscreen): with `Layout.fillWidth` and `wrapMode` every child is 560 px and the hint takes two lines. The same fix went to the hints of the theming and calendar panels; the shell restarted cleanly.
- Nautilus override dropped: the user disabled `org.gnome.Nautilus.desktop` and Nautilus worked from the system entry; the session already exports `GDK_BACKEND=wayland,x11,*` to D-Bus activation (`systemctl --user show-environment`). Removed from `shell`, with its renamed link.
- After the cleanup script and a reboot: `dracut -f` put the HP firmware into the initramfs, the kernel logged "load firmware: intel/ish/ish_lnlm_12128606.bin … firmware loaded … FW base version: 5.8.0.7726", `iio-sensor-proxy` is active and the user confirmed rotation works. Chrome, Text Editor, FreeRDP, the five GNOME extras, `ffmpeg-free`, `libva-intel-media-driver` and every Flatpak app are gone; `intel-media-driver` and `gstreamer1-plugin-libav` are installed.
- Found: the swap step still listed `libva-intel-media-driver -> intel-media-driver`, because `intel-media-driver` provides that name and the check used `rpm -q --whatprovides`. Swaps now look the old package up by name (`fedora.installed`); the dry-run with every profile says "Nothing to do."

## Fingerprint on Fedora 45, 2026-11-04

- Enrolled (right index, Synaptics press sensor). sudo in kitty, polkit and `pkexec` accept it (the journal shows `grantors=pam_fprintd` for `polkit-agent-helper-1`).
- GDM asked only for the password after a reboot with the finger already enrolled: `gdm-password` authenticated at 23:45:18, and `fprintd` first started at 23:50. PAM is complete (`/usr/lib/pam.d/gdm-fingerprint`, authselect `with-fingerprint`, `enable-fingerprint-authentication` true, `enable-switchable-authentication` false). The cause is GNOME Shell 51 itself: in `gdm/authServicesLegacy.js` (from `libshell-51.so`), `_connectFingerprintManager()` returns unless `_reauthOnly`, so the login dialog never asks fprintd; only reauthentication offers the finger. Not changeable from the configuration.
- Keyring: the password at GDM unlocks oo7 through `pam_oo7` ("Retrieved stashed password", `oo7-daemon-login`), and the `login` collection reports `Locked false`. No prompt follows, so the keyring follow-up is closed.

## zsh as the login shell, 2026-11-05

- `core` now installs zsh, zsh-autosuggestions, zsh-syntax-highlighting, `git-core`, fzf, zoxide, eza and bat, sets `login_shell = '/usr/bin/zsh'` (new `shell` step, `usermod --shell`), and pins Powerlevel10k (`d05a1b0`, 2026-09-06; the newest commit was from that day, too new to pin) and zsh-autocomplete (`52ce817`, tag 26.08.04) as `clones` (new step after `stow`, as the user: `git init`, `fetch --depth 1` of the commit, `checkout`). New `zsh` Stow package: `~/.zshenv` (`ZDOTDIR`, `~/.local/bin` in `PATH`), `~/.config/zsh/.zshrc` and `p10k.zsh` (upstream lean 8-color config plus the clock).
- On this laptop, before the packages: `stow.py apply` linked the three files, and `clones_apply` of the installer fetched both clones (2.4 and 3.9 MiB); `clones_pending` was then empty. An interactive zsh in a pseudo-terminal (a Python `pty` driver; `script` is not installed) started without errors: `p10k` loaded with the lean prompt, `Ctrl + R` bound to `fzf-history-widget`, zsh-autocomplete functions present with `compdef` defined, `ZDOTDIR=~/.config/zsh`, `PATH` starting with `~/.local/bin`, history in `~/.local/state/zsh/history`. Powerlevel10k downloaded `gitstatusd-linux-x86_64` into `~/.cache/gitstatus` on first start (its installer checks the sha256 from `install.info`).
- `check.sh` runs `zsh -n` on the zsh files (CI installs zsh); 82 installer tests pass.

## The ISH firmware in the installer, 2026-11-05

- New `firmware` key of `hardware` (product, purpose, source, target, sha256, size) and `firmware` step after `files`; `--firmware DIR` names where to look. The blob is found by size and sha256, so the extracted SoftPaq works as well as a renamed copy: with `--firmware …/sp158489` the search returned `Driver/IshHeciExtension/FWImage/0003/ishC_0207.bin`. Fedora installs it as root with `restorecon`, then `dracut --force --regenerate-all`. Only the DMI product `HP OmniBook Ultra Flip Laptop 14-fh0xxx` gets it; a missing blob there is a warning, not a stop.
- On this laptop the target already holds the blob with the expected hash, so the dry-run shows neither the step nor the warning. The missing and copied cases, another model, the order (install, then initramfs) and the warnings are covered by tests: 92 installer tests pass, and `check.sh` passes.

## udiskie in the tray, 2026-11-05

- `tray: auto` and `appindicator: true` in the udiskie config; `libayatana-appindicator-gtk3` joins `core` (on this laptop the legacy `libappindicator-gtk3`, from `gnome-shell-extension-appindicator`, already provided the typelib). Restarted from Hyprland, udiskie logged nothing and registered `/org/ayatana/NotificationItem/udiskie` with the StatusNotifierWatcher.
- The bar tray showed every item, Passive ones too, which would have kept udiskie's icon there without devices; tray items with `Status.Passive` are now hidden (the StatusNotifierItem meaning of Passive). The shell restarted cleanly; the icon with a USB drive plugged in is still to be seen on screen.

## Guided installer, 2026-11-05

- `install-tui.py` driven in a 110x30 pseudo-terminal (a Python `pty` driver rendered with `pyte`, from the scratchpad; tmux and `script` are not installed): Welcome with system, model, free space and the `post` entry inside Hyprland; Profiles with toggling, `core` locked and the manifest summary; Review with the real checks of this laptop (16 steps, one with work: `libayatana-appindicator-gtk3`, added to `core` earlier today, was not installed yet), folding, and the apply confirmation answered no. Nothing was applied.
- The firmware screen was driven with `firmware_needed` stubbed, since this laptop already has the blob: a path that is not a directory, `Tab` completion, a directory without the blob, and an empty field that goes on with no `--firmware`.
- 27 new tests (`test_install_tui.py`) cover the choices, the review rows, completion, the screen flow, one sudo prompt before the first step and the reboot question; the 92 installer tests pass after the `preflight()` split.
- CI: Check and Install had failed since the zsh commit on `check-links.py` (`hypr/config/session.lua` named in two guides; the path is `hypr/.config/hypr/config/session.lua`). Locally `check.sh` skips the link check without `python3-cmarkgfm`. After the fix, the Check job replayed in a `fedora:45` container (same packages, user `ci`) passed `check.sh` completely, link check and the new tests included.
- The profile screen started from `core,hardware,plugins` whatever was installed. It now checks each profile's packages, swaps and Stow links (`profile_status`, rpm queries only) and starts from the installed ones once `core` is there. On this laptop all nine profiles showed `installed` and started on, `steam-hidpi` through its link; `--profiles core,media` kept that choice and `i` switched to the installed set. The review of all nine found only `upgrade` (pending dnf updates). 37 TUI tests pass.

## Plugins rebuilt at login, and uninstall, 2026-11-05

- The guided installer's "Finish the installation" ran `post` on a finished install; `install-hypr-plugins.py` stopped on "Packaging has changed" because `73932c1` had only edited `VERIFIED` in `build.py`, and told to run `hyprpm remove` in the live session, the swap that crashed Hyprland on 2026-10-30. Now `VERIFIED` lives in `scripts/hyprpm/bundle.py`, outside the digest; `desktop-plugins reload` at Hyprland start rebuilds a changed packaging or a verified Hyprland update in a terminal before anything loads; `install-hypr-plugins.py` refuses to replace loaded plugins and, with none loaded, removes the old repository or resets an ABI-mismatched cache itself; the TUI shows the plugin state and offers "Finish" only while the first-login autostart exists. On this laptop `bundle.status()` reports `packaging` (installed `76481377…`, repository `333f414c…`): the next login rebuilds them. 22 tests (`test_plugins.py`) cover the states, the login decisions, and that nothing is removed while plugins are loaded; the login itself is still to be seen.
- Uninstall: `apply` records each change and the value it replaced before the step runs; `--uninstall` undoes them in order (plugins, login, links and settings; PAM, shell, services before the packages; packages, swaps, repositories; the record kept, marked undone). Packages go through `dnf remove`, asked first with `--assumeno`: the preview is dnf's own answer, and what a package that stays still needs is kept and asked again without it.
- On this laptop (no record, reconstructed from `dnf history`, base = transactions 1-2, 582 packages): the preview lists 13 steps and 1278 packages, none of them from the base install (`python3`, `NetworkManager`, `sudo`, `dnf5`, `kernel-core`, `firewalld`, `fprintd-pam` stay; `git-core` is protected); zone back to `public`, shell to `/bin/bash`, multi-user target, GDM disabled. Nothing was applied here.
- Container (`fedora:45`, profiles core, hardware, plugins, apps, containers, media, codecs, with `ffmpeg-free` and `libva-intel-media-driver` installed first): install, second apply with nothing to do, check.sh, then uninstall. Found and fixed on the way: dnf refused the whole removal because the protected `systemd-udev` needs `kmod`, which needs `/usr/bin/pkg-config` (now kept and asked again); and a second uninstall, with the record deleted and a history without the system install, rebuilt a record that removed `ffmpeg-free` (now the record stays marked undone, and an unknown base removes no package). Final run: no package from before missing, swaps back, both COPR and file repositories gone, shell, authselect and target restored, no links left, a second uninstall with nothing to do; `pkgconf-pkg-config` kept, needed by `kmod`. 116 installer tests pass.

## Uninstall and plugin rebuild review, 2026-11-05

- A read-only review of the uncommitted uninstall found that every `apply` saved `{'profiles': [...]}` first, and `uninstall_plan` took that as a real record: on this laptop `install.json` held only the profiles, so the preview had dropped to plugins, stow, settings and the record, with no packages. A record that knows only the profiles is now rebuilt from the history, and an `apply` on a desktop installed before the record (Stow links or a plugin stamp) starts from the rebuilt one. The preview here is back to 1278 packages and 14 steps.
- Uninstall now undoes a file, login shell, firewall zone, session or target only while it is still the way apply left it (a note names the rest); keeps the installer's packages that a package installed by hand needs (`dnf repoquery --providers-of=requires --recursive`, marked `keep`); keeps a repository that packages staying still come from (`from_repo` against the ids in its `.repo` files; a release package updated from its own repository does not count); takes the base install as the first run of transactions without a typed command line, so a later PackageKit one no longer moves it; moves an unreadable record aside; and runs on a Fedora release the manifest does not list yet. On this laptop no package is kept and every repository goes: nothing outside the removal comes from them.
- Plugins: `bundle.status()` was `missing` after a rebuild stopped between `hyprpm remove` and a finished build, and the login then did nothing; it read `current` with a plugin marked `failed`. Both are now `incomplete`, which rebuilds at every login until one finishes. `hyprland` and `hyprland-devel` from different updates is `mismatched`: a notification, nothing loaded, no terminal opened at every login. Live state here: `current`.
- 123 installer and 25 plugin tests pass; `check.sh` passes.

## Review follow-ups: bugs and robustness, 2026-11-05

From the same read-only review (four areas: uncommitted installer work, Quickshell services, wrappers and config, missing features).

- Bugs, no change in what the user does: `.zshrc` sourced the upstream `p10k-lean-8colors.zsh` after `p10k.zsh` (a line `p10k configure` appends), which unset the HH:MM clock; removed, with a test that it stays out. A new `zsh -i` reads `POWERLEVEL9K_TIME_FORMAT=%D{%H:%M}` and has `time` on the right. `desktop-theme glass` was documented but not forwarded by the wrapper. The wallpaper picker logged `ReferenceError: files` (focus after the delegate was destroyed). `Updates.names()` threw on a malformed `updates.json`. Stopping a recording could hang on a wf-recorder that never finishes: it is now killed (whole process group) 15 s after Stop; a fake recorder that ignores SIGINT and keeps a child on stderr ended in 2 s with the test timeout, the file kept and an error reported. The Theming gallery dropped refreshes asked for while one ran (`refreshPack()` runs it once more). A new external monitor's brightness is read again 3, 6 and 9 s after it appears. Plain-text notification bodies lost the text between `<` and `>`, and bodies are cut at 4000 characters (`tst_notification_text.qml`). Thirteen binds (Theming, Do Not Disturb, Keep awake, Dock) were listed under "Other" in Hints. BlueZ errors reached the Bluetooth panel as raw English D-Bus text, a cancelled pairing included; they are translated, and a cancel is no error. `gaming.py` errors are in the catalogs and shown as a notification when no terminal reads them. Two quick `Super + A` presses no longer start two Claude sessions (a lock, closed for kitty, and a 10 s launch marker).
- Monitors that go away: the dock's menu, keyboard and touch screens and its per-screen maps, `ShellState.activeScreen` (an open panel closes) and the assistant console's monitor are cleared on `screensChanged`.
- Private state: `~/.local/state/desktop-shell` was 0755 with 0755 files (`notifications.json`, `osk-words.json`). `desktop-session` makes it 0700 and its files 0600 at every login (applied here by hand too), and `predict.py` writes its memory 0600 whatever mode it had (`write_atomic(mode=)`).
- Behavior changes (approved): the Sleep key suspended twice, from the bind and from logind (`systemd-inhibit --list` showed no `handle-suspend-key` holder). The session now takes that inhibitor (`desktop-sleep-key`), listed here as `Desktop … handle-suspend-key … block`. `desktop-session` starts hypridle, hyprpaper and udiskie as user units (restarted on failure, stopped at logout) and no longer stops at the first missing daemon or failed portal; it takes effect at the next login. `desktop-shell supervise` replaces `start` at login and brings Quickshell back: after `kill -9` of the shell here it was back within 3 s, one instance, `desktop-shell status` answering; `restart` pauses it so it never races the new instance. The lock path's three shell/compositor calls are bounded at 1 s each (they take 0.08 s and 0.015 s), under logind's 5 s sleep delay. Lid switch: with another monitor on, closing the lid turns the internal display off; the binds are registered (`switch:on:Lid Switch`) and the panel stays on with the lid open, but the clamshell itself still needs a physical test with an external monitor. Update checks keep the last list of a source that fails, retry 30 minutes later through a transient timer, and run on wall-clock times (`OnCalendar=00/6:00`) instead of time awake. The message language now takes the session locale before `/etc/locale.conf`, and dates and times follow `LC_TIME` (`I18n.region`, `I18n.timeFormat`; `tst_locale.qml`): unchanged here (`it_IT` throughout), an `en_GB` session gets a 24-hour clock and Monday-first weeks.
- `check.sh` passes (73 QML tests, all Python suites); the shell restarted with a clean log.

## Battery warnings, per-app volume and Alt + Tab, 2026-11-05

- Battery warnings (`services/Battery.qml`, `Config.batteryLow`/`batteryCritical`): the singleton loads (`batteryAlert` in `desktop-shell status`, 0 at 41% on battery). The notifications themselves are still to be seen at 20% and 10%.
- Per-app volume: Quickshell marks a playback stream `isSink` (a silent `paplay --volume=0` showed `isStream 1, isSink 1`), so the first filter (`!isSink`) listed nothing; with `isSink` the stream appears (`audioApps: ["MixerTest"]` in the status). The Audio panel section was not opened on screen.
- Alt + Tab (`panels/WindowSwitcher.qml`, a `switcher` submap in `binds.lua`): the binds load (`ALT + Tab`, `ALT + SHIFT + Tab`, and in the submap `Tab`, `Alt_L` on release, `Return`, `Escape`), the submap enters and resets through `hyprctl dispatch`, and the IPC answers. A quick tap can deliver the Alt release before the Tab that opens it: an early end is kept for a second and applied on opening. A switcher left open commits by itself after 10 s and resets the submap; with no window to show it leaves the submap at once. Not yet tried with the keyboard.
- Two back-to-back `desktop-shell restart` runs left the new instance without its polkit agent ("An authentication agent already exists"): the old one had not unregistered yet. A restart a few seconds later registered it normally. Not changed.
- `check.sh` passes; the shell runs with a clean log.

## Stylus battery, color picker, focus, screen area, launcher, cursor, 2026-11-05

- Stylus and peripherals: UPower reports the ELAN pen as a keyboard battery of the touchscreen controller (`hid-0018:04F3:4302…-battery-7`), present only while the pen is near; `Config.stylusBatteries` names it Stylus. The Battery panel lists present peripherals, and one under 15% warns once (kept while the pen is away). Not yet seen with the pen near.
- Color picker: `desktop-color` (hyprpicker, hex, copied, translated notification) on `Super + Shift + P` and in the assist System page; the bind loads, the message renders ("Colore #FF8800"). Not clicked here.
- Focus: a one-minute session from `desktop-shell focus start 1` turned Do Not Disturb on, showed 1 minute left, ended on time, put Do Not Disturb back off and posted "Sessione di concentrazione finita". A first try ended at once and left Do Not Disturb on: three `SessionState.set()` calls in a row each wrote the file, and an earlier write was read back over the later values; `SessionState.setMany()` writes once.
- Screen area: `desktop-area text` (tesseract, ita+eng, to the clipboard) on `Super + Shift + T`, `desktop-area ask` on `Super + Ctrl + A` (the image path typed at the Claude prompt through a remote-control socket that only the assistant's kitty opens, or the image copied for Ctrl + V with a console started before). tesseract is not installed yet; the binds load. Manifest: `hyprpicker`, `tesseract`, `tesseract-langpack-ita`, `tesseract-langpack-eng`, `qalculate`, `fd-find` in `core`.
- Launcher: a query with a digit asks `qalc -t` (first row, Enter copies), three characters or more ask `fd` for eight files in the home folder (after the apps, Enter opens). With the packages installed: in the Italian locale qalc read `3.5 h` as 35 hours and answered `5 km to mi` as `3 mi + 188 yd + 0,19 ft`, so the query is normalized (a comma between digits becomes a dot, qalc runs with `decimal comma off`, and a minus before the unit after `to` keeps one unit): `5 km to mi` 3.106855961 mi, `3,5 h to min` and `3.5 h to min` 210 min, `100 eur to usd` 116.48 $, `80 * 20%` 16, `-5+2` −3. `20% of 80` is not qalc syntax. fd takes 4 ms here and leaves hidden folders out (`~/.dotfiles` included).
- OCR with the packages installed: a generated image with "Perché è già così? Città, più" and "Hello world 1234" came back exactly with `ita+eng`, in 0.1 s. The area selection itself (slurp) is still to be tried by hand.
- Cursor: `desktop-theme cursor --size 32` set GSettings `cursor-size` 32, the X resource to 53 (×1.667), `cursorSize = 32` in the rendered `hyprland.lua` and the Hyprland cursor; `--default` put back 24 and 40, the other preferences untouched. 4 new tests in `test_theme.py`.
- Shell restarts: Quickshell crashed on exit (SIGSEGV in `IdleInhibitor::onWindowDestroyed`, seven core dumps since 12:27, all with Keep awake on), and its crash handler relaunched it under `/usr/bin/quickshell`, racing the instance `restart` started (polkit agent and notification server "already registered"; one crash report opened in a kitty window). Keep awake is now a logind idle inhibitor (`systemd-inhibit --what=idle … cat` on a pipe from the shell), which hypridle honours: two restarts and a `kill -9` later there was no crash, the old inhibitor went with the killed shell and the new one came up. `desktop-shell` reads instances from `qs list` and `restart` waits for the old process to exit; its supervisor keeps its lock out of `sleep`. Twice a new QML file was not stowed before a restart and the shell was down for about 10 s.
- `check.sh` passes.

## Alt + Tab focus, and Quickshell's crash handler, 2026-11-05

- Alt + Tab: with the windows on the same workspace, the keyboard stayed with the window under the pointer (reported by the user). The toplevel was activated while the switcher's full-screen surface was still mapped; unmapping it makes Hyprland refocus the window under the pointer (`follow_mouse = 1`). The switcher now closes first and focuses the window 60 ms later with `hl.dsp.focus({ window = "address:…" })`, which also moves the pointer onto it. Checked across workspaces with the IPC; the same-workspace case is for the user to try.
- Another exit crash, in `QQuickShortcut`'s destructor (the Theming panel's shortcuts), again followed by the crash handler's relaunch and a lost polkit agent. `desktop-shell` now starts every shell with `QS_DISABLE_CRASH_HANDLER=1`: four restarts in a row and a `kill -9` (back in about a second through the supervisor) left one instance, the polkit agent, the notification server and the Keep awake inhibitor in place.
- Alt + Tab, second report: the keyboard stayed in Hyprland's `switcher` submap (found that way here), so only its binds worked. The release bind on `Alt_L` never fired: by the time the release arrives Alt is no longer a held modifier. The release is now read from `hl.on("input.keyboard.key")` (left Alt, XKB keycode 64, state 0), arrows move too, `Return` and `Escape` work without Alt, and a `catchall` cancels on any other key (modifier presses are bound to `no_op`), so the submap cannot stay. Driven here with a second `osk.py` virtual keyboard: a quick tap, two Tabs, Escape, Return and a letter each left the submap at `default` with the expected window focused; with two test windows on one workspace the switch focused the other window, moved the pointer to its centre, and the next key typed reached it.


## Privacy, emoji, media, weather, accessibility, displays, 2026-11-05

- Privacy indicator: a silent `parecord` showed `microphone: ["PrivacyTest"]` in `desktop-shell status` and went with it; holding `/dev/video0` open showed `camera: ["python3"]`. Screen sharing (Hyprland `screencast` events) is for the user to see with a real share. `test_privacy.py` covers the `/proc` scan (wireplumber keeps `/dev/media*` open and is not counted).
- Emoji picker (`Super + .`, the assist Apps page): `emoji.py` builds the list from `unicode-emoji` and CLDR's `cldr-emoji-annotation` (added to the manifest): 1923 emoji in nine groups with Italian names and keywords, 50 ms the first time and 27 ms from the cache. The pick copies the emoji and sends Ctrl + V, or Ctrl + Shift + V when the target window's process is a terminal, through `hl.dsp.send_shortcut`. Driven with a virtual keyboard (search "cuore", Enter) into a test kitty window with its own class and into a GTK 4 entry: both received 😍. On the way: the window class could not tell a kitty with its own class from a GTK app; Shift + Insert pastes the primary selection in kitty, which is off here (`misc:middle_click_paste`, so `wl-copy --primary` copies nothing); and the toplevel's IPC data had no pid yet for a new window, so the pid now comes from `hyprctl clients`.
- Media: the bar shows what plays (a click plays or pauses, the wheel skips); `desktop-shell media now` gives the lock screen a now-playing line (stowed `hyprlock.conf` kept equal to Graphite's render). Not seen with a player running.
- Weather: GeoClue answered the client `desktop-weather` without an agent (IP-based, 25 km), Nominatim named it Santa Maria a Vico, Open-Meteo gave 17 °C clear; a city works too ("Cosenza"). `test_weather.py` covers the parse, a city, an unknown city and the offline cache.
- Accessibility: `Super + Alt + +` / `0` set `cursor:zoom_factor` to 1.25 and back to 1 (read with `hyprctl getoption`). A High Contrast theme passes the theme contrast tests. A shell-wide text scale was not done: 167 font sizes are literal in the QML.
- Displays (`Super + P`): with a headless output, Extend placed it at x 1728, Mirror mirrored the panel, Laptop only turned it off, External only turned the panel off, and every mode came back to Extend. Two fixes on the way: a monitor rule must say `disabled = false` and `mirror = ""`, or the previous mode stays (this also kept the panel off after a clamshell); and Hyprland's `FALLBACK` output, made when the last real one goes, counted as another monitor, so unplugging the external one in External only (or in a clamshell) left the panel off. Both fixed; the unplug case now brings the panel back by itself.
- `check.sh` passes.

## CI and the bar media title, 2026-11-05

- The Check workflow had failed since the plugin rebuild work: `test_plugins.py` reset a mocked cache and the installer then read the real `/usr/share/pkgconfig/hyprland.pc`, which the CI container has not got. `install-hypr-plugins.py` names it `HYPRLAND_PC` and the test points it at a temporary file.
- The Install workflow had failed since the uninstall work: `install-container.sh` asked `systemctl get-default` before the installer brought systemd into the `fedora:45` container. Until systemctl exists it takes Fedora's default, `graphical.target`, which is what systemctl reports once installed.
- The bar's media title kept its full width and ran over the battery: centred, `ActionButton`'s label is not limited by the button. It is left-aligned now, so it fills the button and ends with an ellipsis (seen with a Spotify title).

## Cursor packs, pinch zoom, emoji keyboard page, shell text scale, 2026-11-05

- Cursor packs: Fedora packages only Breeze, Oxygen and Bluecurve, so `breeze-cursor-theme` joins the manifest and Bibata Modern Classic / Ice (v2.0.7) and Phinger Dark / Light (v2.2) are pinned downloads in `theme.py`. `desktop-theme cursor --theme Bibata-Modern-Classic` fetched, checked and unpacked it in about 10 s and applied it (GSettings, X resources); Phinger Light then came from the same cached archive. Back to Adwaita afterwards; the two stay installed. A test unpacks only the chosen folder of a local archive and fetches again when the kept archive no longer matches.
- Pinch zoom: three-finger pinch out / in on the touchpad (`hl.gesture`, `pinchout` / `pinchin`) and on the touchscreen (Hyprgrass `kind = "pinch"`) run `desktop-shell zoom in / out`. The config loads without errors; the gestures themselves are for the user to try.
- Emoji page on the on-screen keyboard: `osk.py text` commits through `zwp_input_method_v2` (`commit_string`, then `commit` with the count of done events, covered by a test) and reports when no field is active, so the shell pastes instead. The page itself is for the user to try by touch.
- Shell text scale: 174 `font.pixelSize` values go through `Theme.textSize()` (the Theming previews and a size copied from another text are left out); `qmllint` reports the same 50 warnings as before. `desktop-theme text-scale 1.3` enlarged the bar text at once (the media title still ends with an ellipsis) and `1` brought it back.
- Follow-ups from the user: the pinch directions were the wrong way round (Hyprland's `pinchin` is the fingers moving apart), now apart zooms in. The cursor set is Adwaita, Breeze, macOS (apple_cursor v2.0.1, both variants) and Bibata (Classic, Ice), fetched in the background by `apply` when missing (20 s here for the four); Phinger left the catalog and its test copy was removed. The on-screen keyboard's extra-row button showed `extra` while terminals forced the row on, so in a terminal it looked off and did nothing; it now shows and toggles the row on screen. On the emoji page the extra row was still drawn under the grid (screenshot from the user): the key rows, extra row included, are hidden there now.

## KDE Store for cursor and icon themes, 2026-11-05

- The store's OCS API answers without an account (`autoconfig.kde.org/ocs/providers.xml` names `api.kde-look.org`): 1232 cursor themes (category 107), icon themes in 132, JSON with previews and md5-checked download links that redirect to a CDN and need no browser.
- In a sandbox `XDG_DATA_HOME`: Sweet cursors installed in under a second (md5 matched), installing it again replaced only its own folder, `remove` took it away and refused `hicolor`. Reversal's first file first failed: icon themes link to absolute paths and the data filter refused the whole archive, so unpacking now drops the refused members one by one; it then installed Reversal-black and its dark variant (91 MB), no absolute link left. `test_store.py` covers unsafe tar and zip members, finding themes, installing, the ledger, the checksum and the size limit.
- The Theming page (Icons tab, "Find online…") loads without errors; it is for the user to try.
- The store cards overflowed into their neighbours (screenshots from the user): the file selector, Remove and Install sat on one row wider than a card, and the selector's minimum width was its longest file name. The selector has its own row now and may shrink (the name ends with an ellipsis), the buttons sit below on the right, and the card clips. Opened through the new IPC `theming store-icons` (also `store-cursors`) and captured: Candy, Papirus, Tela and the rest fit their cards.

## Battery and resource use, 2026-11-05

Measured on battery, desktop idle, with `upower` energy-rate averages over 60 s and per-process CPU from `/proc/PID/stat`.

- Starting point about 10.4–12 W. 31 pairs of orphaned helpers (`brightness.py watch`, `bar_visibility.py`, …) and 30 pairs of `wl-paste --watch` were still running from earlier shell restarts: a killed Quickshell left its children behind. Long-lived commands now start through `setpriv --pdeathsig TERM --`; after a `desktop-shell restart` no helper of the old shell is left.
- The biggest cost was the bar's agent dot: its pulse animation kept the bar repainting at 120 Hz while an agent was working. Quickshell went from about 12% to 0.4% CPU, Hyprland from about 15% to 9%, power from about 12 W to 6.9 W. On battery the dot now blinks (700 ms, two repaints per period); on AC it pulses as before.
- `brightness.py watch` waits for sysfs notifications on `actual_brightness` (10 s fallback): no wake-ups at rest, brightness keys still update the OSD at once.
- `bar_visibility.py` asks Hyprland every 2 s at rest instead of every 100 ms (about 6 → 1 requests per 20 s idle) and speeds up while a bar is hidden or after a wake-up. The hot corner still hides the bar (reserved 38 → 0 → 38).
- Camera use: the 3 s `privacy.py` spawn (about 60 ms of CPU each) became a persistent `privacy.py watch` with inotify on `/dev/video*`; a test process holding `/dev/video0` showed up at once and went away on close.
- Tried and left as they were: VRR raised power (reverted); blur costs about 1.8% Hyprland CPU and 0.05 W (kept). The tuned profile is already `balanced-battery`.
- Refresh rate: 120 Hz 6.79 W, 48 Hz 5.75 W (the panel's only other mode). Not switched by itself: the battery panel lets the user choose (below).
- After the changes, at rest: Quickshell and its helpers 0.37% CPU, Hyprland about 9% (mostly the terminal used for these measurements), 6.9 W. `check.sh` passes.
- Display refresh choice (`desktop_refresh` in `config/tablet.lua`): VRR, 48 Hz, VRR, 120 Hz, VRR and back to the preferred mode, each checked with `hyprctl monitors`, and again after `hyprctl reload` with VRR and with 48 Hz saved. A monitor rule's `vrr` took effect only now and then (on with a config reload after a mode change, off only when the rule differed), so the choice sets `misc.vrr` instead, which applies at once; the fixed rate goes into the panel's rule as its mode.
- 60 Hz is not offered: the panel lists only 120 and 48 Hz (same pixel clock, longer vertical blank, EDID range 48–120). A modeline with the 48 Hz recipe at 60 Hz applied, but Hyprland 0.57.1 kept only the whole MHz of the clock (59.975 Hz), later rules for the listed modes kept the custom mode until a config reload, and a malformed modeline followed by a rule change aborted Hyprland in Aquamarine's `CDRMOutput::commitState` (`std::out_of_range`, crash report of 16:57; the session came back in safe mode). The battery panel therefore offers only the modes the display lists, plus VRR, which covers the range in between by itself.

## Lazy panels, auto Power Saver, refresh per power source, 2026-11-05

- Lazy panels: after a shell restart no panel is loaded (`desktop-shell status` → `loadedPanels: []`) and the shell uses 208 MB RSS (99 MB anonymous); with all 18 panels loaded it uses 274 MB (160 MB). Each panel was opened through IPC and closed again, with the user's OK: all 18 opened with no warning in the log and were reported open. Creating a panel adds about 0–80 ms to opening it (the Control Center is the slowest; an IPC call alone takes 75–90 ms); within a minute of closing it reopens as before. Panels were dropped a minute after closing, but the process keeps most of the freed memory for later allocations (275 → 265 MB), so the saving is in the panels never opened since the shell started.
- What a panel kept between openings still is: the Control Center's expanded sections and switch details, the open notification stacks, the recording options, the Theming tab, the wallpaper folder and selection (`ShellState.recall` / `remember`). A panel created open animates in and takes the focus like one already there. The Theming IPC (`theming store-icons`) reaches the panel it just created.
- Refresh per power source: the old single choice is read as both; `desktop_refresh("ac", …)` on battery saved the choice without touching the display, and `desktop_refresh_power()` applies only a choice that differs. The shell calls it when UPower's on-battery state changes; the user plugged and unplugged the charger and the display followed.
- Power Saver below 20%: on by default; it switches once per discharge (also after a shell restart, it does not switch again once it did), the notification then says so instead of offering the button, and the charger brings the previous profile back if Power Saver is still on. The real discharge is for the user to see.
- Fixed while there: the agent dot's `smooth` property overrode `Item.smooth` (qmllint `property-override`); renamed `animated`.

## Code review issues, 2026-11-05

Sixty findings of a code review, tracked as issues on the GitLab mirror; 59 fixed, one per commit (`Closes #N`), the VRR one (#40) waits for an external monitor.

- Checks: `check.sh` passes (Python suites, 78 QML tests, the new `test_tablet.lua`, `test_binds.py`, `test_panels.py`, `test_network.py`); every new test was run against the code before its fix and failed.
- Battery and Idle are created at startup again (the Keep awake inhibitor ran right after a restart without opening a panel).
- Theme names: a cursor name carrying Lua renders as one quoted string (`lua` loads it, `glassStyle` keeps its value); the eight files rendered for the current theme are byte-identical before and after.
- `theme.py` split into commands: `list`, `fonts`, `icons`, `cursors`, `wallpapers`, `tone`, `render`, the checks and every `--help` print the same; `apply` writes identical state files.
- Installer: `dry-run --uninstall` went from 48 dnf/rpm runs (15 s) to 21 (5 s) with the same output; the autostart line for `~/.dotfiles` is unchanged, an odd path passes `desktop-file-validate`.
- `ScriptModel` lists, checked in an isolated offscreen Quickshell: a reorder with an insert created one delegate and updated the others, a scrolled grid kept its position after an append.
- `tablet.lua` reads the power source once (popen count with a stub `hl`: 1 instead of one per rotation).
- Not seen on screen yet: the panels changed or split (Theming pages, Network sections, launcher, store, clipboard, polkit prompt on another monitor), the on-screen keyboard built on first show, a screen share, a real discharge.
- Shell restarts from Claude's sandbox gave the shell `NoNewPrivs`, so polkit refused to authenticate ("needs to be setuid root"); restarts now go through Hyprland (`hyprctl eval "hl.dispatch(hl.dsp.exec_cmd(...))"`). One restart left the shell down about 6 s when a new file missed an import; the supervisor brought it back.

## Arch Linux, 2026-11-05

Arch support in the installer and the runtime, decided with the user: official repositories, the three AUR apps built with makepkg at pinned commits, the plugins too, tablet sign-in later.

- Names: the 170 packages of the `[arch]` table resolve with `pacman -Si` in an `archlinux` container (core, extra, multilib), and the files the desktop calls were found with `pacman -F`: `hyprland-uwsm.desktop`, `hyprland.pc` (same `prefix=/usr/include` layout as Fedora) and the headers are in `hyprland`, `hyprpm` is a package of its own, `pactl` in `libpulse`, `qalc` in `libqalculate`, `checkupdates` in `pacman-contrib`, the CLDR annotations in `unicode-cldr-annotations` and the derived ones in `unicode-cldr`. Arch's `gdm` wires `pam_oo7` into `gdm-password` as Fedora's does, and `oo7-daemon.service` can be enabled for every user.
- pacman behaviours the module relies on, tried in the container: `pacman -T` prints what is not satisfied, provides included; `pacman -Q sh` answers `bash`, so installed and version checks compare the name; `pacman -Rsc --print` and `pacman -Si` need no root; the image's `pacman.log` starts with installs logged before any command.
- `calendar.py`: Arch has libical 4 (`ICalGLib-4.0`), Fedora 3. Every call the helper makes (built-in time zones, status, UID, summary, location, dates, `as_timet_with_zone`) gave the expected values with 4.0 (10:00 Europe/Rome as 09:00 UTC).
- On Fedora nothing changed: `check.sh` passes (new `test_install_arch.py`, 72 tests; a mutation of `repin`, `without_section` and the install command made 6 of them fail), zsh still loads autosuggestions, fzf's bindings and syntax highlighting, fastfetch's `small` logo prints byte for byte what `Fedora_small` did, the install hints and the update terminal read as before, the bar keeps `fedora-logo-icon` (hicolor), and the live shell reloaded Bar, Theming and ThemePage without errors. `install-desktop.py pins` against the AUR: every pin current.
- `build.py` changed, so the plugin bundle digest did too: this laptop rebuilds the plugins once at its next login.
- `install-container-arch.sh` in fresh `archlinux` containers, end to end with `core,hardware,plugins` and with `core,apps,gaming`: the preview changes nothing, apply, a second apply finds nothing to do; `hyprland-uwsm.desktop` installed, GDM enabled, oo7 enabled for every user with `pam_oo7` in GDM's PAM and oo7's Secret portal; the helpers load `ICalGLib` 4.0 and Geoclue, Tesseract has `ita` and `eng`, the CLDR files are there; `check.sh` passes on Arch; uninstall brings back the packages from before (only what the test itself installed for `check.sh` stays), `pacman.conf` byte for byte, and no links, AUR checkouts or record left; a second uninstall finds nothing to do. With `COMPILE=1` the four plugins compiled against `hyprland 0.57.1-1`, which `bundle.verify()` accepts.
- What the container runs found, now fixed: `hyprpm` is a package of its own; pacman picked `jack2` for ffmpeg's JACK library (now `pipewire-jack`); `checkupdates` needs `fakeroot`; `pacman -Q` answers for what provides a name (`tuned-ppd` for `power-profiles-daemon`), in the test as in the module; the image's `pacman.conf` has no commented multilib, so the section is added under a mark and removed whole; `-s` kept Steam's `lib32-systemd` and seven libraries it needs because `device-mapper` depends on a bare `libudev.so` that it also provides, so they go in a second transaction once `pacman -Rs --print` agrees nothing staying needs them.
- AUR: makepkg built and installed `zen-browser-bin` 1.24b-1, `1password` 8.12.44-33 (sources checked against 1Password's key) and `visual-studio-code-bin` 1.145.0-1 from their pinned commits, as the user. Their entries are `zen.desktop` (Fedora's is `zen-browser.desktop`, so the dock pins both; an ID without an entry is skipped), `com.microsoft.VSCode.desktop` as on Fedora, and `com.onepassword.OnePassword.desktop`.
- Not covered by a container: GDM and the session on screen, portals, the keyring unlocked at login, the plugins loaded, the HP firmware in a mkinitcpio initramfs, the laptop's hardware. Those need an Arch VM, then the laptop.

## Updates screen in the guided installer, 2026-11-05

**Check for updates** in `install-tui.py`: one line per source, checked ones applied together, the repository alone and first. Decided with the user: a pull only as a fast-forward on a clean tree, new pins written into the manifest for the user to commit.

- Unit tests: the default choice, a pull going alone, the rows, each source (the system and Flatpak lists from the bar's own `updates.py`, pins, a changed clone holding its pin, a remote that does not answer, the repository cases), the flow from the record's profiles, the apply order (manifest, `upgrade` then `clones`, Flatpak, the bar refreshed), the pull starting the screen again; clone pins (natural version order, annotated tags, tags or branch, the comment of the release in the manifest). `check.sh` passes.
- On this laptop, checked for real outside the screen in 9 s: one dnf update (`code`), Flatpak up to date, Powerlevel10k newer on its branch (`d05a1b0 -> 7ddd1b2`) but held, because `p10k configure` rewrote `config/p10k-lean-8colors.zsh` inside the clone on 2026-11-05, the repository up to date with `homelab/main`, and two steps the desktop still needs (`breeze-cursor-theme`, and `tailscale-systray.service` for every user). zsh-autocomplete is at its latest tag although its `main` moved on. `install-desktop.py pins` from Fedora: the same Powerlevel10k commit.
- The real screen in a pseudo-terminal rendered by `pyte`, opened with `--updates`, details unfolded, the cursor moved, back to the menu and out with "Nothing changed.". The first run showed "the desktop is not installed yet" on this desktop: `core` misses one package. The screen now takes the profiles from the install record (all nine here), and the desktop from its Stow links. Stray text after unfolding was `pyte` ignoring REP (`CSI n b`), which ncurses uses with `TERM=xterm`; with `vt100` the same steps draw clean, and kitty implements REP.
- `desktop-manager`, linked by `stow.py apply` (the only new link): `--help` reaches `install-tui.py`, and `desktop-manager updates` opened the updates screen in a pseudo-terminal and quit with "Nothing changed."; without a terminal it refuses as the installer does.
- Not yet: applying from the screen on this laptop (a system update and a pin) and a pull on the Arch machine.

## The bar's Update button opens desktop-manager updates, 2026-11-06

Decided with the user: **Update** in the updates panel opens the updates screen of the guided installer instead of running dnf (pacman) and Flatpak at once. `desktop-updates upgrade` still opens the floating `desktop-updates` Kitty window; its `run` now starts `desktop-manager updates` and waits for Enter (`updates.terminal.close`, or `updates.terminal.failed` when the installer exits with an error). The per-manager terminal messages left the catalogs.

- `check.sh` passes.
- `desktop-updates run` in a pseudo-terminal: the updates screen drew every source, `q` quit with "Nothing changed.", then "Premi Invio per chiudere." and exit 0 after Enter.
- Not yet: the button pressed on screen, and an apply from that window.

## README screenshots, 2026-11-06

Retaken on the live session with Tokyo Night and Omarchy's sunset-lake wallpaper, then Gruvbox, its wallpaper (same hyprpaper file as before), the volume and the Italian shell were put back.

- The shell ran in English for the shots: `desktop-shell restart` with `LC_MESSAGES` and `LC_TIME` set to `en_US.UTF-8` (the environment comes before `/etc/locale.conf`).
- Demo content only: fastfetch titled `demo@omnibook`, notifications from `notify-send`, a stand-in MPRIS player for the media card ("Winding Road"), a zenity note for the keyboard. The Wi-Fi name in the Control Center was painted over as "Home Wi-Fi"; in the console shot, the bar title (Claude Code names the window in the user's language) and a `/clear` line were edited out.
- Keys and taps came from small clients of the Wayland virtual keyboard (`osk.py run`) and virtual pointer protocols: the keyboard's suggestions (`desks`, `desktop`) appeared from real taps on its keys.
- Found: `install-tui.py` stops with `locale.Error: unsupported locale setting` when the environment names a locale that is not installed (here `LC_MESSAGES=en_US.UTF-8` on a system with only Italian locales): `locale.setlocale(locale.LC_ALL, '')` at startup. Fixed: `set_locale()` falls back to the environment's character set, then `C.UTF-8`. Three new tests in `test_install_tui.py` fail without it; `desktop-manager updates` with that `LC_MESSAGES` in a pseudo-terminal drew the updates screen and quit with "Nothing changed."; `check.sh` passes.

## Your own settings outside the repository, 2026-11-06

- `Config.qml` reads `~/.config/desktop/shell.json`: every option goes through `pick(name, default)`, the same 47 options with the same defaults. In the live shell, `{"dockIconSize": 60}` grew the dock icons at once and removing the file brought them back to 44; a list given as a string (`dockPinned`) kept the default with a warning in the log.
- `hyprland.lua` loads `~/.config/desktop/hypr.lua` last through `require`, so Hyprland watches it: touching it emitted `configreloaded` (with `dofile` it did not). A syntax error in it showed in `hyprctl configerrors` and left the other 116 binds working.
- The personal lines of `local.lua` (the AI language, Super + B for Zen, Super + Shift + Space for 1Password) moved to this laptop's `hypr.lua`: the two binds and `DESKTOP_AI_LANGUAGE=italian` in a process started by Hyprland are as before.

## Machine profiles and config/displays.lua, 2026-11-06

- `tablet.lua` split: `config/displays.lua` keeps the internal panel (rotation state, refresh per power source, display modes, lid) and `tablet.lua` only the touch devices that rotate with it, the tablet switch and `desktop_rotate`. The OmniBook's values moved to `config/machines/omnibook_ultra_flip.lua`, which `machines/init.lua` loads for the DMI product `HP OmniBook Ultra Flip Laptop 14-fh0xxx`; `local.lua` is gone and `monitors.lua` keeps only the rule for every monitor.
- A laptop without a profile gets its panel by name (`eDP`, `LVDS`, `DSI`) at the defaults, and its lid from `/proc/acpi/button/lid`; a desktop gets no modes, refresh or rotation at all, and the display picker says so instead of offering modes. A monitor seen for the first time in extend mode is left to its own rules (before, `arrange()` set it to preferred, auto, scale 1); extend and mirror give a monitor declared with `displays.monitor()` its own rule back.
- `test_displays.lua` (was `test_tablet.lua`): 21 checks, the new ones a panel found by name that rotates, a monitor left to its rules, internal turning the other monitor off, and a desktop whose monitors no mode, refresh or rotation touches.
- Live on this laptop: `Hyprland --verify-config` on a copy of the final configuration first; then, after each saved file, `hyprctl configerrors` empty, eDP-1 at 1.6667 and 120 Hz on mains (the saved choice), the tablet and lid switches bound, 118 binds as before, and `desktop_rotate(0)`, `desktop_refresh_power("ac")` and `desktop_display_mode("extend")` through `hyprctl eval` changing nothing.
- Found on the way: a module that is new to the repository needs `stow.py apply` before a file requires it. Saving `tablet.lua` before `displays.lua` was linked left Hyprland for a minute without the panel's rule (scale 1) and the switch binds, until the link was made.

## Touch only with a touchscreen, 2026-11-06

- `Tablet.touchscreen`: `hyprctl devices -j` lists a touch device (asked once at start), or tablet mode is on; in `desktop-shell status` too. The on-screen keyboard's helper runs as the input method only then (`Keyboard.autoShow`), and Hints lists the gestures only then.
- Found on the way: started from `onAutoShowChanged`, the helper ran without `--input-method`, the handler running before the command's binding had the flag; `Qt.callLater` fixed it. A hot reload of these singletons kept part of the old state, so the result was checked after a clean restart through the supervisor: `touchscreen: true`, `osk.py run --input-method` running, `inputMethod: true`, `ready: true`, as before on this laptop.
- Not checked live: a computer without a touchscreen (the false branch of the same parse).

## The tablet profile, 2026-11-06

- Manifest: `tablet` takes from `hardware` `iio-sensor-proxy`, `libwacom`, the sensor hub modules file, the ISH firmware and (Fedora) the tablet sign-in; `hardware` keeps firmware, video, cameras, power and `fprintd`. `default_profiles()` adds `tablet` on a 2-in-1, told by `/proc/bus/input/devices` (a tablet mode switch, `SW` bit 1, or a direct input device with absolute axes); on this laptop it answers `core,hardware,tablet,plugins`.
- Records from before: `bundle.migrate()` adds `tablet` after `hardware` when `profiles_version` is not 2, and `save_record()` writes 2 from now on. This laptop's record reads as `core, hardware, tablet, plugins, …` without being rewritten.
- Plugins: `bundle.selected()` builds Hyprgrass only with `tablet` (all four without a record); `install-hypr-plugins.py` writes a `hyprpm.toml` of the selection into the packaging repository and enables only it. With all four the digest is the same as before (`afc956cf2eb4654c` here, `bundle.status()` still `current`), so this laptop rebuilds nothing; without Hyprgrass it is another digest, rebuilt at the next login.
- Tests: selection, migration, digest and filtered manifest in `test_plugins.py`; detection from sample `/proc/bus/input/devices` blocks (switch, touchscreen, a lid and a touchpad that are not) in `test_install.py`; the fresh preselection with and without a 2-in-1 in `test_install_tui.py`. The install workflow and the container scripts now run `core,hardware,tablet,plugins`.
- Not tried: a login that builds the three-plugin set, on a machine without `tablet`.

## Updates screen for other installs, 2026-11-06

- The pin lines (AUR packages, zsh plugins) only with `git config desktop.maintainer true` in the repository, set in this laptop's clone so it keeps them; any other clone gets the pins with **Repository**, and **Desktop** lists what they need.
- After a pull (`after_pull`): with changed files, `stow.py apply` with the plan's optional packages; in a Hyprland session also `hyprctl reload` when `hypr/` changed and `desktop-shell restart` through `hyprctl eval` (the supervisor's environment, as the memory rule requires) when `quickshell/` changed. Unit tests for each case, the order (links first) and a pull that brought nothing.
- Not tried live: a pull with new files from the screen (this clone is up to date).

## Keyboard layout from the system, 2026-11-06

- `input.lua` reads `XkbLayout` and `XkbVariant` from `/etc/X11/xorg.conf.d/00-keyboard.conf` (what `localectl set-x11-keymap` writes on Fedora and Arch), else `KEYMAP` of `/etc/vconsole.conf` without its suffix, else `us`. On this laptop: `kb_layout` `it`, `kb_variant` empty, the keyboards on the Italian keymap, as before.

## Screen-capture indicator, 2026-11-06

- Cause: a screencopy client (`wf-recorder`, also behind the shell's own recorder) makes Hyprland send `screencast>>1` and `screencast>>0` for every frame it copies: 157 of each in a 3-second capture of eDP-1, read from socket2. The bar's monitor icon followed each one and flickered.
- `Privacy.qml` now turns the indicator on at once and off only after 1.5 s without a new `1`. A 4-second `wf-recorder` capture sampled through `desktop-shell status` every ~100 ms: `privacy.sharing` false, then true in one run for the whole capture, then false once.
- Not tried: a portal share (XDPH), which also counts through its PipeWire stream and is unaffected by the delay apart from the 1.5 s at its end.

## Cursors tab, 2026-11-06 (#5)

- `theme.py cursors` now gives each installed theme five preview shapes (arrow, hand, text, busy, resize). On this laptop: all seven themes (Adwaita, Bibata Modern Classic and Ice, Breeze Dark and Light, macOS, macOS White) found every shape; 35 PNGs in 0.2 s the first time, 0.06 s from the cache. A montage of them checked by eye: transparency and colours right (premultiplied ARGB unpremultiplied), animated shapes on their first frame.
- Tests: an XCursor file built by hand (largest fitting size, unpremultiplied pixels, broken files), the X11-name fallback, a broken shape, the cache and its invalidation on change, and a hyprcursor theme from synthetic `.hlc` archives (PNG by size, SVG). No hyprcursor theme is installed here, so that path is tested only that way.
- Live, on eDP-1 with the user's permission: `theming cursors` opens the new tab with the five chips, the list, previews at 24 px and the chosen theme highlighted; `theming store-cursors` keeps the Cursors chip and its back button says Cursors; `theming store-icons` goes back to Icons; the Icons tab keeps only the shell icons and the packs. No errors in `qs log`. The cursor itself was not changed.
- `stow.py apply` linked the new `CursorsPage.qml` before the shell restart. `check.sh` passes; its warnings are the same as on main.

## Reduce effects, 2026-11-06 (#3)

- `desktop-theme reduce-effects on` on the live session (with the user's permission): Hyprland reloaded with `animations:enabled`, `decoration:blur:enabled` and `decoration:shadow:enabled` false and `plugin:hyprglass:enabled` and `plugin:hyprglass:layers:enabled` 0; `quickshell.json` had `reduceEffects: true`; `hyprctl configerrors` empty. The Theming panel showed **Effects: Reduced** and an opaque panel. `off` put all five options back to true/1, and `preferences.json` came back byte for byte as before.
- `Hyprland --verify-config` passes with a rendered `hyprland.lua` that has `reduceEffects = true`, and without one (defaults).
- Tests: the choice reaches both rendered files (and a hand-edited non-boolean does not), only `true` is saved, `toggle` flips it, Hyprland reloads each time; the Graphite fallbacks in `Theme.qml` and `theme.lua` match the rendered defaults, now `bool` properties included.
- The assistant's pulsing dot already honoured `reduceMotion` (the issue said otherwise); it now follows `Theme.reduceMotion`, like the workspace pills, the OSD and Alt + Tab, which used `Config.reduceMotion` directly.
- Not tried: the look of every theme with Reduce effects on (checked with Gruvbox); an automatic mode is not part of this change.

## Settings, phase 1, 2026-11-06 (#8)

- Live on eDP-1, with the user's permission, through `desktop-shell` and the IPC: `toggle settings` opens Settings (sidebar with Appearance, the section on the right, in Italian); `toggle theming` with Appearance on screen closes it, and again opens Settings → Appearance; `toggle settings appearance` opens without toggling; `theming store-cursors` and `theming font` reach the KDE Store page and the Font tab inside Settings; an unknown section falls back to Appearance; a malformed section name is refused by `desktop-shell` (exit 2). No errors in `qs log`. `Super + I` is bound (checked with `hyprctl binds`); not pressed.
- The first hot reload after removing `ThemingPanel.qml` failed ("SettingsPanel is not a type") because the new files had no Stow links yet; Quickshell kept the previous configuration running. `stow.py apply` linked `SettingsPanel.qml`, `ThemingView.qml` and the `.desktop` entry, the dangling `ThemingPanel.qml` link was removed by hand, and the restart through the supervisor came up clean.
- `test_panels.py` now also requires the aliases of `ShellState.aliases` in `desktop-shell toggle` and nowhere among the panels. `desktop-file-validate` passes on `desktop-settings.desktop`.
- Not tried: the compact layout (both screens are wider than its threshold), and launching **Settings** from the launcher.

## Settings, phase 2, 2026-11-06 (#8)

- Live on eDP-1, with the user's permission (no `shell.json` before): the five new sections render with their groups, switches, sliders with value and unit, choices and hints. From the keyboard (`wtype`): Space on "Show what is playing" wrote `{"barMedia": false}` and the bar dropped the media item at once, with **Reset** shown; ↓↓ → wrote `minimumWorkspaces: 3`, ← removed it again; Space back on the first row left `{}`. A deliberately broken `shell.json` showed the warning, disabled the controls, and Space left the file untouched. `shell.json` was deleted afterwards, as it was.
- Found on the way: Tab never reached the controls inside a section, so the keyboard model is arrows + Space/Enter, like the rest of the shell.
- `test_settings.py`: every schema option exists in `Config.qml` with the same default, its default fits its limits and step (or its choices), and every section, group, label and hint is in both catalogs, with no hint text left without an option.
- Not tried: a missing `~/.config/desktop` folder (the first write creates it with `mkdir -p`), text and time fields from the keyboard, the compact layout.

## Settings, phase 3 (devices), 2026-11-06 (#8)

- The Network, Bluetooth, Displays and Sound panels became a frame (card, header, Back/Close) around a view that Settings shows too. Live on eDP-1, with the user's permission: the four sections render in Settings (the Wi-Fi list fills after the scan starts, a few seconds), the four quick panels look as before plus **Settings…**, Esc closes Settings when no network details are open. No connection, pairing, volume or display mode was changed.
- A restart failed once: `escape` is not a legal QML method name (a JavaScript global) and `NetworkView.qml` did not load, so the shell was down for about a minute until it was renamed `goBack` and restarted. `qmllint` with the categories `check.sh` disables does not report it.
- Not tried: opening a network's details inside Settings and Esc back from them (no way to click without a pointer tool here), the **Settings…** links themselves (they call `ShellState.openSection`, exercised through the IPC in phase 1).

## Settings, phase 3 (system), 2026-11-06 (#8)

- Live on eDP-1, with the user's permission: Settings → Assistant shows the state, usage and console button of the assistant panel; System → About lists Fedora Linux 45, HP OmniBook Ultra Flip Laptop 14-fh0xxx (vendor once), Intel Core Ultra 7 258V with 8 threads, 30.8 GiB, the kernel, Hyprland 0.57.1, Quickshell 0.3.2 and the commit with "local changes"; `toggle settings updates` lands on System → Updates; System → Advanced shows Open the folder and Open hypr.lua (no shell.json here), "No errors." and a disabled Reset (nothing set). The Control Center, assistant and updates panels show **Settings…**. Nothing was reset, installed or opened.
- Found and fixed: on the first opening after a restart, a tab asked for (`system/advanced`) was lost because the section page did not exist yet; it is now kept (`requestedTab`) and applied when the page loads. The same path now runs Appearance's `activate()` on that first opening, which phase 1 skipped.
- `test_about.py`: vendor named once, firmware placeholders left out, processor with threads, memory, distribution, a folder without git.
- Not tried: the Reset confirmation and the open buttons (`xdg-open`), clicking the **Settings…** links.

## Desktop menu, 2026-11-06 (#8, phase 4)

- `hyprctl layers` after the restart: one `desktop-menu-catcher` per monitor on the Bottom level, full size (1728×1080 logical on eDP-1, 1920×1080 on DP-1).
- Live on eDP-1, with the user's permission, through `desktop-shell desktop-menu` and the keyboard: the menu shows Applications, Settings, a separator and Session…; Down + Enter opened the launcher, then Settings, then the session menu (closed with Esc, nothing chosen); Esc closes the menu itself.
- Found and fixed: opened from the IPC the menu landed in the top left corner, because the layer had no size yet when the middle was computed; the middle is now a binding.
- Follow-up the same day: group labels in the Settings sidebar (Connections, Devices, Personalization, Input, System; Power moved next to Sound, Privacy next to System), and in the desktop menu the labels Open and Session, monochrome glyphs (`PopupMenu` entries take `glyph`, drawn with `Icon`, red when destructive) and the session actions themselves. Live on eDP-1, with the user's permission: both screenshots as intended; Restart… opened the session menu with `powerPending` "reboot" and its confirmation, Esc cancelled and a second Esc closed it; nothing was run.

## Settings, phase 5, 2026-11-06 (#8)

- `hyprsettings.py render` live, with the user's permission: a `settings.lua` with one shortcut (`SUPER + F12`, notify-send) was loaded by Hyprland (`hyprctl binds`), no config errors; rendering `{}` removed the file and the bind. The first try did not load: Hyprland only watches files it loaded at the last reload, so a new or removed `settings.lua` was not noticed; `render` now runs `hyprctl reload` when the file changed.
- `Hyprland --verify-config` passes with a generated `settings.lua` (layout, environment, bind) and without one.
- Tests: rendering, validation (layouts, variants, languages, keys with their modifiers), Lua string escaping, writing only on change and removing when empty, reading from `shell.json`; the rendered Lua run by `lua` with a stub `hl` gives back exactly the layout, variable and bind. `test_panels.py` now also checks that every singleton of `services/` is in `services/qmldir`.
- Settings → Keyboard (Physical keyboard with the system's `it` shown, Your shortcuts) and → Assistant (Language) on screen. Typing into the fields was not tried (no pointer tool here). The user's `hypr.lua` sets `DESKTOP_AI_LANGUAGE` itself, which wins over Settings, as documented.
- Unrelated, found on the way: `hyprctl configerrors` showed `console.lua:59` refusing `set_special_workspace({})` after an outside click on the console (#14).
- Follow-up after the user tried it (shortcuts were never saved): `qs log` showed `ReferenceError: root is not defined` from the shortcut rows. Editing a field reassigned the array the `Repeater` showed, which rebuilt every row, the one running the edit included, so its save never ran. The rows are a `ListModel` now (a field changes its row in place) and the edits run on the section itself. Asked for at the same time: a row whose keys are already bound says so (**Already taken by: …**, from `hyprctl binds`, outside submaps, not counting the bind the row itself saved), and one repeated among your own rows too. The key logic moved to `services/BindKeys.js`, tested by `tst_bind_keys.qml`. The Settings page loaders no longer warn of a binding loop (`visited` kept on the panel). Typing into the fields is again for the user to try.
- Second round of feedback on the same PR (issues #16–#19), live on eDP-1 with the user's permission. Network: the connectivity on the right, seven networks then a scrolling list, Other network below. Power: the profile and the automatic Power Saver below the battery warnings, the battery panel unchanged. Appearance: the Layout tab with the window drop-downs in a column (Bar, Effects and Dynamic mode on Theme, as the user asked after a first version that moved them all); the tab loaders lost their binding-loop warnings (a list of tabs seen, updated before the tab changes).
- Displays (#17): `displays.configure` tested in `test_displays.lua` (another monitor takes a whole rule with defaults for what is not said; the panel takes scale and position but keeps the refresh of its power source; rotation and extend keep them; malformed calls change nothing), and `hyprsettings.py` refuses a mode the connected monitor does not list, an unknown position, a scale outside 0.5–3 or not a number, a malformed name. Live: a rule identical to the current DP-1 (1920×1080@60, 100%, automatic) was accepted with no config errors and nothing moved; removed again. Found: settings.lua replaced `package.path` while loading, so `require("config.displays")` failed on a machine without a profile (checked with `--verify-config` on a copy without the OmniBook entry); the user folder now comes first instead. Found: the form showed 100% for the panel, because `onSelectedChanged` ran before the bindings of the selected monitor; `fill()` looks them up itself now. Not tried: a real change and the countdown (for the user).

## Console closed by an outside click, 2026-11-06 (#14)

- Cause: `desktop_console_hide()` cleared the special workspace with `monitor:set_special_workspace({})`, which Hyprland 0.57.1 refuses ("expected a workspace object or selector", shown by `hyprctl configerrors`), so a click or tap outside the console did not close it.
- Tried live with the user's permission, on the console open on eDP-1: `set_special_workspace(nil)` hides it with no error. With the fix, `hyprctl eval 'desktop_console_hide("eDP-1")'` (what the shell runs when the catcher is pressed) closed it and left `configerrors` empty; `desktop_console_show()` brought it back each time.
- `scripts/tests/test_console.lua` (run by `check.sh`): a stub monitor that refuses anything but nil or a selector, as 0.57 does; the console's monitor is cleared, one showing another special workspace is left alone, and without a name every monitor showing the console. It fails with the old line.

## Any coding agent through herdr, part 1, 2026-11-07 (#2)

- herdr-core 0.1.18 and herdr-app installed by the user in `~/.local/bin`; this very session runs in herdr (`t1`, `claude --continue` in `.dotfiles`).
- `hc ls --json` gives each live terminal's `agent`, `status` (a word) and `where`; `hc events --json` gives full terminal records with `status: {app, state, kind?, msg, progress?}` and `status_ms`. `Agent.qml` takes membership and state from `ls` and the message from the latest event; the shell's status then reported `herdr: true`, state `working` and the agent `Claude Code · .dotfiles / 1` with herdr's message. A first version read `status.app` from `ls` too and found no agent: the two outputs differ.
- `desktop-ai`, `console.lua` (the console classes) and the `desktop-ai-herdr` rule: Hyprland reloaded them with no config errors; `test_console.lua` still passes. Not tried here: `Super + A` moving the running Herdr window into the console, the notifications and the panel list (the user to try), and a session without herdr (the probe and `desktop-ai` keep the old path).

## The Herdr app follows the desktop theme, 2026-11-07 (#2)

- `desktop-theme apply` on this laptop (Gruvbox) wrote `~/.config/herdr-app/themes/desktop.json` and added `theme`, `font` (Fira Code), `font_size` (15, from 11 pt) and `ui_font` to Herdr's `settings.json`, keeping `zoom`, `sounds`, `font_ligatures` and `minimum_contrast`; a copy of the file was kept first. No `*.error` file from Herdr.
- The shown layout was **Terminals**, which sets its own theme and fixed colors (`colors.background: #131619` and others), so `herdr-app shot` still measured `#131619`, also after `herdr-app do app.theme '{"name":"desktop"}'` (with the user's permission). A copy made with `layout.clone` (`desktop`), without `colors` and `background` at its root and with `theme: "desktop"`, measured Gruvbox's `#282828`. Switching the desktop to Tokyo Night made it `#1a1b26` within 2.5 s, and back `#282828`; the desktop was put back on Gruvbox with the user's wallpaper.
- Tests: a complete Herdr theme for every desktop theme, only unset or own keys changed in `settings.json`, nothing written without `~/.config/herdr-app`, a `settings.json` with a comment left untouched.
- Not changed: Herdr's `telemetry` (on by default), which is the user's to decide.

## Modular coding agents, 2026-11-07 (#2)

- `agents.py` on this laptop: `claude` in `~/.local/bin` is the primary (`primary`, `argv claude` gives its path); `codex` and `agy` are not installed and Codex reports `npm` as present, so its Install is enabled. `image antigravity` gives `@PATH`.
- `scripts/tests/test_agents.py` (run by `check.sh`): the three shipped descriptors are valid and ordered, invalid ones are left out, the user's own file wins by id, the primary follows the order, `aiPrimary` (only when installed) and `DESKTOP_AI_AGENT`, `install` refuses when a needed program is missing and otherwise opens a Kitty `desktop-updates` window with the installer.
- The shell restarted with the new Settings group and `Agent.qml` with no warnings in `qs log`; `hyprctl configerrors` empty after the new bind description. The installers were not run here (Claude Code is already installed).

## Installer profile for herdr, 2026-11-07 (#2)

- Release manifests read on releases.herdr.dev: herdr-core 0.1.18 and herdr-app 0.1.13, with their x86_64 and aarch64 sha256 (Apache-2.0). The x86_64 archives were downloaded and matched their sha256; the layout follows `releases.herdr.dev/app/install.sh` and `core/install.sh`, read but not run.
- The `archives` step on a scratch home, from those two downloads: `~/.local/bin/herdr-core` (byte-identical to the one installed on this laptop), the `hc` link, `~/.local/share/herdr-app`, the `herdr-app` link, the icon and a launcher entry identical to the one herdr's installer wrote here; nothing pending afterwards. No downloaded program was run.
- Tests: `ArchiveTests` in `test_install.py` (pending only while missing, what is there stays, a wrong sha256 installs nothing, no build for the machine is a warning, uninstall removes only what apply made, newer releases become pins with their hashes, a moved download URL is refused, `repin` moves both distributions); `theme.py herdr` in `test_theme.py`.
- The first CI run failed in both containers: releases.herdr.dev answers 403 to urllib's default User-Agent (`Python-urllib/3.x`), 200 with one of its own; the installer now sends `install-desktop.py (dotfiles)`. `install-desktop.py`'s `newer_pin` against the live manifests: both pins at their latest.
- Not tried: Herdr's first start with the theme written beforehand.

## The repository in the update check, 2026-11-07 (#26)

- `repository_updates()` on this clone: the work branch has no upstream, so no repository line (`{}`). On a scratch clone of GitHub reset three commits back: `origin/main`, behind 3, ahead 0, clean, the three commits with their hashes and subjects, the upstream head `76ab712`.
- `scripts/tests/test_updates.py` (`RepositoryTests`): new commits, commits of its own and local changes, no upstream or no clone (no git run), a failed fetch is an error that keeps the last state and the other lists, `check repository` asks only the repository and keeps the other lists, their errors and the time of the last check, git never prompts. `test_install_tui.py`: a pull checks the repository again for the bar.

## Removing installer profiles, part 1, 2026-11-07 (#28)

- `install-desktop.py dry-run --remove` on this laptop for `media`, `gaming`, `steam-hidpi` and `containers`: the Steam launcher link for `steam-hidpi`, the Tailscale tray unit for `containers`, and the record line. Nothing else, because this laptop's record holds only `breeze-cursor-theme`: its packages were installed on 2026-11-04 by an installer without a record, and an apply on 2026-11-06 started one with only what it added, so neither a profile removal nor the full uninstall would remove them.
- `scripts/tests/test_install.py` (`ProfileRemovalTests`): only what no profile that stays names (a shared package and repository stay), settings and swaps with the last profile that has them, no record of profiles keeps every other one, `core` refused, a run undoes it and the record forgets it, a package of a profile that stays is not taken as a dependent, only the profile's own Stow links go, the plugin builds only with `plugins`, which needs a console. `test_install_tui.py`: the menu entry and `--remove` lead to the review, `plugins` refused inside Hyprland, `--add` checks the profile over the installed ones, the run.
- CI (`install-container*.sh`), on Fedora 45 and Arch: `tablet`, `herdr`, `steam-hidpi` and `media` removed after a full install. The first run expected `iio-sensor-proxy` gone and failed: the installer kept it and `libwacom`, rightly, since dnf would remove GDM, Hyprland and Quickshell with them (checked here with `dnf remove --assumeno`). Now: Loupe, Papers and Showtime gone with what only they needed (15 packages, 48 MiB on Arch), the sensor hub file, Herdr and the steam-hidpi links gone, authselect back (Fedora); `fprintd`, `iio-sensor-proxy`, `libwacom`, Hyprland and the core links kept; the record without the four; a second removal finds nothing to do; then all added back before the full uninstall test.
- Found while writing that check: a second removal would have listed the kept packages again. Only profiles the record still has are undone now, and packages that only stay are no work.

## Glassed surfaces after a rotation, 2026-11-08 (#32)

- Reproduced on the built-in panel with `hyprctl eval 'desktop_rotate(1)'` and the Control Center open: the `desktop-overlay` layer had the new size (1080×1728) but the card stayed in the old orientation, sideways; a toggled tile repainted in place, still sideways. Closing and reopening drew it upright.
- A minimal Quickshell layer on four edges (scratchpad config) rotated correctly as `qtest` and `desktop-bar`, and stayed in the old orientation as `desktop-overlay` and `desktop-osd`, the namespaces Hyprglass glasses. `WAYLAND_DEBUG`: Qt acked each configure and always sent `set_buffer_transform(0)`. No socket2 event on a rotation. The dock did not show in portrait either.
- The fix through a temporary IPC call of `Tablet.remapIfTurned()` (removed afterwards) with the Control Center open: 0 → 90 upright, 90 → 180 upside down, 180 → 270 and → 0 upright. A panel opened fresh at 180 is upside down too, at 270 upright: 180 stays a Hyprglass bug.
- The user, in tablet mode with the accelerometer: a panel open during a rotation follows the screen.
- Not tried: the dock and the on-screen keyboard after the fix, keyboard focus of a remapped panel. `check.sh` passes.

## Hyprgrass on upstream hold_touches, 2026-11-08

- Pin `578e984` (main after hyprgrass #433 and #437), `hyprgrass-touch-as-pointer.patch` = `git diff 578e984 b6e42ad -- src`, the head of the closed #435 merged with that main. The commit after it, `6a03d08`, stops warping the pointer on touch, which the click of `touch_as_pointer` relies on, so the pin stays before it.
- Built against Hyprland 0.57.1 (`0.57.1-1.fc45.x86_64`) both from a plain checkout and through `build.py hyprgrass` in a scratch directory: compiles cleanly, and `plugin:hyprgrass:hold_touches` and `plugin:hyprgrass:touch_as_pointer` are registered by the library. The build is now in `~/.cache/dotfiles/hyprpm-build/`, so the rebuild at the next login reuses it.
- Not tried in a session: the running one keeps the old build until the next login, and the nested touch test harness went with the Fedora 45 reset. Not loaded, not tried by touch. `check.sh` passes.
- After the rebuild at the next login, the user tried the new build by touch and confirmed it works.

## One build cache key per plugin, 2026-11-08

- Before: one key for all four plugins, made from the Hyprland build and the whole text of `build.py` and the patch. After #34 moved only the hyprgrass pin, Hyprspace, hyprglass and HyprCapture compiled again at login (22:43–22:44), and four old key directories held 4.4 GB.
- `build.py <plugin>` for all four from the branch, in a scratch directory, against Hyprland `0.57.1-1.fc45`: compiled in 25 s (Hyprspace), 15 s (hyprgrass), 40 s (hyprglass) and 156 s (HyprCapture). The cache became `<plugin>/<key>` with one entry each, and the old layout was removed: 1.1 GB left.
- A second run of all four copied from the cache in about 50 ms per plugin, with no fetch or compile.
- Unit tests (`test_plugins.py`, 36 tests): moving one pin changes only its key, the patch counts only for hyprgrass, another Hyprland or other build steps change every key, pruning keeps the current entry and the other plugins, and a cached build is copied without running anything. `check.sh` passes.
- Not tried: a real login with the new bundle. It needs the merge; hyprpm then copies all four from this cache.

## Radio panel review (#48), 2026-11-09

- Found in review:
  - `stop` and `play` sent `quit` to every `mpv-*.sock` in the runtime folder, which the global mpv script gave to every mpv, so a station closed any other mpv;
  - `mpv_ipc` sent each command to every socket, because it only returned on an error;
  - a URL from a result or the panel reached mpv without `--` or a scheme check.
- Reworked:
  - one socket, with replies matched by `request_id`;
  - streams, YouTube links and files only, after `--`;
  - the MPRIS bridge and `shell/.config/mpv/scripts/desktop-mpris.lua` replaced by the `mpv-mpris` package (Fedora `fedora`, Arch `extra`), and `mpv`, `mpv-mpris`, `yt-dlp` (and `ytfzf` on Arch) added to the media profile;
  - the stations moved to `shell/.local/share/desktop/radio/stations.json`, with the user's own in `~/.config/desktop/radio.json`;
  - English-only `.desktop` entry, errors and kind labels through i18n.
- `test_radio.py` (22 tests): the parsing tests of the PR, plus:
  - a stand-in mpv on a real socket: toggle, next and stop reach only the radio's socket, and another mpv socket gets nothing;
  - the live title, pause and video;
  - options and other schemes refused, and `--` before the URL;
  - the user's stations replace or add, and saving keeps them.
- Not tried on screen: mpv is not installed here (the media profile adds it).
- Asked by the user after trying it (2026-11-09):
  - **Video in the panel**, via Qt Multimedia (`panels/radio/RadioVideo.qml`, loaded only with video on).
    - The first version paused mpv and played one stream with sound and picture. It failed: YouTube no longer serves such a stream (`yt-dlp -F` on a DJ set lists audio-only and video-only formats only).
    - Now the panel plays the picture alone (`radio.py video`: H.264 up to 720p) muted, and follows mpv's position and pause, which keeps the sound.
    - Checked offscreen: the 720p video-only stream loads in Qt Multimedia, seeks to 10 minutes and buffers. `radio.py video` on the playing DJ set gave the stream and the position, with mpv still playing.
    - mpv now always plays sound only. The earlier mpv video window never showed a picture: started with `--no-video`, mpv's yt-dlp hook fetched the audio alone.
  - **Layout:** header (title, video, close), content (list or video), controls always at the bottom, footer.
  - Tests: `test_radio.py`, 28 tests.
    - On screen (2026-11-09, by Claude at the user's request): Blue Note Hours, then `desktop-radio video` (new: `radioVideo` over IPC). The 720p picture showed in the panel with the controls below, and the bar showed the track through mpv-mpris. Over two seconds the frames stayed identical with mpv paused (`desktop-radio toggle`) and changed while it played. A first `desktop-radio video` came before the `Radio` singleton had read the state: `requestVideo()` now waits up to 5 s for it.

## Installer profiles in parts (#49, step 1), 2026-11-09

- Manifest:
  - Fedora and Arch have the same 34 units (`test_both_distributions_have_the_same_units`);
  - every part says `default` (true, false, or `intel`, `camera`, `fingerprint`);
  - every repository is used by some unit.
- Detection on the OmniBook: Intel, camera (IPU) and fingerprint reader (Synaptics `06cb`) found, so the default is every `hardware` part with `tablet`. Tested against a fake `/sys`: an Elan touchscreen (`04f3:2513`) is not a reader, an Elan `0c..` is, and an Intel IPU is a camera.
- Record version 3:
  - this machine's record (version 2: `core,hardware,tablet,plugins,apps,containers,media,gaming,codecs,steam-hidpi`) is read as the units that hold them;
  - `profiles.py list` on it shows every profile and part installed but `gaming.steam-hidpi` (its links point to the live clone, not the worktree) and `assistant` (Herdr installed by hand, not recorded).
- Preview of every step but stow, verify and boot, against this system: nothing to do for the defaults, or for `core,apps.vscode,gaming,utils.wev`. `--remove gaming.steam` would only note it in the record, since Steam stays for nothing else here.
- Tests:
  - `test_install` (parts, units, detection, defaults, `load_plan`);
  - `test_install_tui` (93: toggling with default parts, the accordion);
  - `test_profiles` (listing with parts, `plan change`, `run`);
  - `test_plugins` (migration of a version 2 record);
  - `check.sh` passes.
- Not tried: the TUI and the Settings tab on screen, and an install in a container (CI runs it).

## Plugins as parts (#49, step 2), 2026-11-10

- Build dependencies, from the plugins' own build files in the cache:
  - Hyprspace and hyprglass build with make against Hyprland's headers (plus pangocairo and lua);
  - hyprgrass builds with meson;
  - HyprCapture alone is CMake, and needs Qt (svg, wayland, layer-shell), OpenCV, PipeWire, PulseAudio, FFTW, FFmpeg, x265 and libde265.
- The packages split that way: the plugins profile keeps the tools and the headers, and `plugins.hyprcapture` gets the rest.
- Record version 4: a version 3 record with `plugins` gets every plugin part, and version 2 maps `plugins` the same way. `bundle.selected()` builds the plugins of the recorded parts, plus Hyprgrass with `tablet`. The full set keeps its digest, so no rebuild.
- `install-desktop.py` writes `~/.local/state/dotfiles/units` with the record, and removes it with an uninstall.
  - `config/installed.lua` reads it (`test_installed.lua`), and `binds.lua` sets the screenshot keys only with `plugins.hyprcapture`.
  - `services/Installed.qml` reads it: the bar corner, the Overview and screenshot actions of the assist button, the overview gesture of the hints, and the glass settings button follow it.
  - Without the file, everything shows, as before.
- Tests:
  - `test_plugins` (each plugin with its part, version 3 records);
  - `test_install` (the units file);
  - `test_install_tui` (a plugin part is installed once its plugin is built);
  - `check.sh` passes.
- Not tried on screen: this machine has no units file until the installer next saves its record.

## The AI Assistant and the radio hidden without their profiles (#49, step 3), 2026-11-10

- Units:
  - `assistant`: Super + A, Super + Shift + A and Super + Ctrl + A (`binds.lua`), the bar icon, the Assistant section of the Settings sidebar (the page stays, for links to it), the Assistant and "Ask about a screen area" actions of the assist button, and the `desktop-ai` launcher entry.
  - `radio`: Super + M, the Control Center button and the `desktop-radio` launcher entry.
- Settings installs keep the units that are there without a record (`present_units`, as the TUI's preselection does). Herdr installed by hand on this machine therefore gets recorded, and the units file never drops the AI block.
- Tests: `test_profiles` (what is present is kept). `check.sh` passes, including `--verify-config` with the guarded binds.
- Not tried on screen: with no units file here, everything shows.


## README pictures, and a stray units file (#49, step 4), 2026-11-10

- Shot on this machine with the shell in English (`desktop-shell restart` with `LC_MESSAGES` and `LC_TIME` set to `en_US.UTF-8`), the Tokyo Night theme, the cursor hidden (`cursor:inactive_timeout` 1 for the session) and the assistant console out of sight; afterwards the theme, the language, the cursor and the console were put back, and the sound unmuted.
- `settings.webp`: one `grim` still per section (`qs ipc call desktop settings <section>`), put together with fixed durations. wf-recorder only writes a frame when the screen changes, so a recording of instant section changes came out shorter than it ran.
- `radio.webp`: a wf-recorder take of the Radio panel: `dream` typed into the filter (no prefix of it matches a personal saved entry), cleared at once, then the video. The six seconds of `Loading the video…` before the picture are cut. Sound muted while recording.
- `installer.webp` and `settings-profiles.webp`: the guided installer in kitty (`LC_ALL=en_US.UTF-8`, quit without changes) and the Profiles tab with the hardware and apps parts open (the starting `expanded` changed for the shot only, then restored).
- Found while recording: with the Radio panel open, `desktop-radio video` closed it, since `ShellState.show()` toggles; fixed in #54 (`ShellState.open()`, also for the updates notification).
- Found while recording: `~/.local/state/dotfiles/units` held only `core`, `plugins` and the plugin parts (written 00:45, while the record is still version 2), so Super + A, Super + M, the Assistant section and the radio button were gone. No test writes it now (each `scripts/tests/test_*.py` run against the file's mtime), so it most likely came from a test run in a worktree before the sandbox lines; removed, `hyprctl reload`, and the binds and the shell are back.
- Settings → System → Plugins and the installer say the installed Hyprland (0.57.2-1.fc45; the session still runs 0.57.1) is not verified for the pins: until it is, the plugins stay off at the next login.

## Hyprland 0.57.2-1, 2026-11-10

- The COPR moved to `0.57.2-1.fc45` (commit `11cbc6c`, tag v0.57.2), `hyprland-devel` and `hyprland-uwsm` with it; the session still ran 0.57.1. The installer and Settings → System → Plugins reported the build as not verified, so the next login would have come up without plugins. Working as intended.
- Upstream v0.57.1...v0.57.2 is 22 bug fixes. Headers a plugin can see: `CWindow::markUrgent()` and `CLayerSurface::isHiddenByFullscreen()` added (non-virtual members, no layout change), `CXDGActivationToken` and `CXDGActivationProtocol` reworked, `NInit::gainRealTime()` removed; none is used by the four plugins.
- The four pins, the Hyprgrass patch included, built with `build.py` against the installed 0.57.2 headers: no errors, no unresolved libraries, and Hyprglass, Hyprgrass and HyprCapture embed the new commit. The builds are in `~/.cache/dotfiles/hyprpm-build/` under 0.57.2 keys, so the rebuild at the next login copies them instead of compiling.
- In a nested 0.57.2 (no seat, `HYPRLAND_NO_SD_VARS`, `HYPRLAND_NO_SD_NOTIFY`, a private bus, temporary XDG directories; the runtime directory under `/run/user/1000`, since a socket path in the scratch folder is over the 108-byte limit): `hyprctl plugin load` of the four `.so`, then a reload with the real `appearance.lua` and `plugins.lua`. No config errors; `plugin:overview:panelHeight` 200, `plugin:hyprgrass:sensitivity` 4, `touch_as_pointer` and `hold_touches` true; the overview opened and closed through `hl.plugin.overview.toggle()`; `hyprctl hyprglass stats` counted frames; the compositor exited cleanly.
- `VERIFIED` now has `0.57.2-1.fc45.x86_64` next to `0.57.1-1.fc45.x86_64` (a downgrade stays possible) and Arch's `0.57.1-1`; Arch's 0.57.2 is not compiled yet. Still to see: the rebuild at the next login on the machine, and the plugins in daily use.

## README pictures, second pass, 2026-11-10

- Asked by the user: the opening animation still showed the old Theming panel, the radio belongs in the table, and the launcher, Themes and AI console pictures were out of date. The KDE Store picture left the table (the Themes caption names the store).
- `themes.webp`: Settings → Appearance → Theme, with each theme applied from the panel itself (arrow keys and Enter, as a user would), one `grim` still about 4.5 s after each, joined with 0.4 s crossfades and duplicate frames dropped (960 × 600, 18 s, under 1 MB), ending on the first frame so the loop is seamless.
- Found while shooting: a theme set from outside the panel (`desktop-theme set`) while the Theme tab is open leaves the **Current** label on the old card; applied from the panel it follows. Not fixed here.
- `radio.webp`: the earlier take, now the whole screen (800 × 500) like the other pictures in the table.
- `console.webp`: a separate Herdr space, `demo`, made with `herdr-app do space.new` (Claude Code with `--settings '{"language":"english"}'` and one question about Settings → System → Profiles), shown with `terminal.show`, then closed (`space.close`). The working session's space was never on screen.
- `launcher.webp` and `theming.webp`: the launcher with nothing typed (a short query matched three apps, a sum left the panel empty), and the Theme tab on Tokyo Night. Afterwards Gruvbox, the Italian shell, the cursor and the console were put back.

## Theme tab follows a theme set elsewhere (#58), 2026-11-10

- `services/Theming.qml` watches `current.json` and `preferences.json` in the theme state directory, which `theme.py` rewrites with each theme and each window, glass or dynamic setting, and lists the themes again when either changes, once the panel has listed them a first time (before that, nothing shows the list).
- Live, Italian shell: with Settings → Appearance → Theme open, `desktop-theme set catppuccin-mocha` and then `everforest` from a terminal moved **Attuale** to Catppuccin Mocha and then Everforest. The theme was put back to Gruvbox. A window-style and a dynamic-mode change from outside the panel (same path, through `preferences.json`) tried by the user afterwards.

## Hyprland 0.57.2-1 on Arch, 2026-11-10

- Arch's `extra` has had `hyprland 0.57.2-1` since 2026-11-09, while `VERIFIED` accepted only `0.57.1-1` there, so an updated Arch would have run without plugins.
- `install-container-arch.sh` with `COMPILE=1` in a fresh `archlinux:latest` (hyprland `0.57.2-1`), with `0.57.2-1` added to `VERIFIED`: install, `check.sh`, the four plugins compiled with `build.py` (Hyprspace, hyprgrass with its patch, hyprglass, HyprCapture) with no unresolved libraries, then the uninstall back to the packages from before. The only `error:` line is a pacman hook that needs systemd, which the container has no use for.
- The first run stopped at HyprCapture's CMake configure: since #51 its build dependencies belong to the part `plugins.hyprcapture`, and the default profiles of both container scripts and of `install.yml` named `plugins` without its parts. They now list `plugins.hyprspace`, `plugins.hyprglass` and `plugins.hyprcapture`, so the CI install covers those packages too.
- As for 0.57.1 on Arch, only compiled: not loaded in an Arch session. The same upstream release loads in a nested 0.57.2 on Fedora (above).

## Tried by hand, 2026-11-10

Reported by the user after the merges of the day:

- Agent installs from Settings → Assistant (#37, step 4): tried by GBSpada; they work.
- **Remove profiles** in the guided installer, with the fix of #62.
- The Theme tab (#59): a window-style and a dynamic-mode change from outside the panel move the page too.
- The glass settings page by hand, and Glass Light on screen.
- Power Saver turning on by itself at 20% on a real discharge.

## A file in the way of Stow (#69), 2026-11-10

- `stow.py dry-run` printed `Will back up on apply` for each file in the way and then exited with the status of `stow --simulate`, which aborts on them (exit 1). The installer previews each step before applying it and stops on that exit, so `stow.py apply`, which backs them up, never ran: with one regular `~/.config/kitty/kitty.conf` the install stopped at the stow step every time.
- The dry-run now passes Stow one `--ignore=^<path>` per file in the way. Stow matches it against the path relative to the target with `\z` appended, so only that path is left out (`kitty.conf.tpl` still links).
- Against a throwaway target holding a regular `kitty.conf` and a GTK `settings.ini` linked elsewhere: dry-run exit 0 with both listed, nothing changed; `apply` moved both to the backup folder and linked them; a second dry-run had nothing to back up. The dry-run of the real home is unchanged.
- `scripts/tests/test_stow.py` covers both runs with the real Stow (it fails without the fix); `stow` is now installed by `check.yml` on both distributions, so the test does not skip there. Both container installs now start with a `kitty.conf` of the user's own and check that apply backs it up and links it, and that the uninstall puts it back (run by `install.yml` on this PR).
- `check.sh` passes.
## Settings saves while rendering (#70), 2026-11-10

- `HyprSettings.save()` wrote `shell.json` every time but started `hyprsettings.py render` on a plain `Process`, which ignores a new command while it runs: two quick edits left `settings.lua` on the first one. The renderer is now a `CoalescedProcess` (`request()`).
- A throwaway Quickshell config (no windows) with two `CoalescedProcess`, one with an `onExited` of its own as the renderer has: a request made while the first run was going ran once more after it with the newer command, in both, and the instance handler ran next to the base one. Two requests in the same tick, before the process starts, make one run with the newer command.
- The live shell reloaded with no errors. `check.sh` passes.
## Keep awake inhibitor restarts (#71), 2026-11-10

- The inhibitor (`systemd-inhibit --what=idle … cat`) was bound to `keepAwake`: once it exited, nothing ran it again while the switch still said On. `Idle.qml` now starts and stops it on `keepAwakeChanged`, starts it again after an exit while Keep awake is on (`Backoff`: 2 s, doubled after each run shorter than a minute), and sends its stderr to `qs log`.
- Live, Keep awake on: after the reload the inhibitor was listed by `systemd-inhibit --list` ("Resta attivo"). Killed by pid, a new one was listed about 4 s later (the run had lasted less than a minute, so the wait had doubled).
- `check.sh` passes.
## Display revert outlives the Settings window (#72), 2026-11-10

- The countdown after Apply in Settings → Displays, and the monitors from before, moved from `MonitorSettings.qml` to `services/HyprSettings.qml` (`tryMonitor`, `keepMonitors`, `revertMonitors`, `trying`, `secondsLeft`). The page shows the same bar from there, and lists the monitors again on `monitorsReverted`. A Settings window dropped during the 15 seconds (`panelKeepSeconds` below 15, or a page rebuilt) no longer stops the revert, and a Settings window opened again during the countdown shows it.
- Not tried on screen: applying a mode changes the display, and the shell has no IPC into HyprSettings. The live shell reloaded both files with no errors; `check.sh` passes.
## One owner for Wi-Fi scanning (#73), 2026-11-10

- Each `NetworkView` bound `scannerEnabled` of every Wi-Fi device to its own `shown`. With the panel closing (it stays loaded for a minute) and Settings → Network opening, the panel wrote `false` last and the Settings page stayed without scanning. `NetworkInfo` now keeps the views on screen (`watch(view, shown)`, on show, hide, creation and destruction) and is the only one to bind `scannerEnabled`, to "any view on screen and Wi-Fi on".
- The live shell reloaded with no errors (one intermediate save had two `onShownChanged` handlers; the final file has one). Not tried on screen: it needs the panels opened. `check.sh` passes.

## Answers of killed searches (#79), 2026-11-10

- A throwaway Quickshell config (no windows) showed the order when a running `Process` is set to `running = false` and started again in the same tick with a new command: the killed run's collector finishes with its partial output, then it exits (code 15), then the new run starts. Store and the launcher set the query a run answers before that, so the killed run's output passed the check (the Store showed "unavailable" and stopped its spinner; the launcher showed files for the older text).
- `Store.qml` (`searcher`) and `LauncherSearch.qml` (`calculator`, `finder`) now keep the query in `pending` and copy it to `asked` in `onStarted`. The same throwaway config with that pattern accepted only the new run's output.
## Clipboard history without the poll (#92), 2026-11-10

- cliphist writes `~/.cache/cliphist/db` (a bbolt file, 8 MB here) in place at each copy. A throwaway Quickshell config showed that a `FileView` with `preload: false` and `watchChanges` reports those in-place writes without loading the file (`loaded` stays false), and only while `watchChanges` is true: writes before it is set and after it is cleared were not reported.
- `Clipboard.qml` now lists the history when the panel opens (as before) and on each change of the database while it is open, instead of every second; the listing is a `CoalescedProcess`, and an output equal to the last one leaves `entries` alone.
- The live shell reloaded with no errors; `check.sh` passes.

## One Watcher for the long-lived helpers (#104), 2026-11-10

- `services/Watcher.qml` is a `Process` with `wanted`: started and stopped with it, started again after an exit while still wanted, after `Backoff` (3 s, doubled after each run shorter than a minute, up to a minute), with its stderr in `qs log` under `name`. A throwaway Quickshell config with a helper that prints to stderr and exits at once: restarts 0.4 s then 0.8 s apart (base 200 ms for the test), the stderr lines logged, the instance's own `onExited` run too, and no restart once `wanted` went false.
- Live, after the reload: `bluetooth_agent.py` and both `wl-paste --watch` clipboard watchers running; rotation and hyprsunset not, as tablet mode and Night shift were off. The text watcher, killed, was running again a few seconds later with a new pid.
- `check.sh` passes.
## theme.py in modules (#103), 2026-11-10

- `theme.py` was split by a script that moves top-level statements verbatim and rewrites every reference to a name now in another module into `module.name`, found with `symtable` so that a local sharing a moved name stays as it is. Modules depend in one direction only: `theme_paths` ← `theme_core` ← `theme_apps`, `theme_wallpapers` ← `theme`; `theme_assets` stands alone. `test_theme.py` reads and patches each name in its module (`theme_paths.STATE = …`, `mock.patch.object(theme_apps, 'apply_btop')`).
- Against `main`'s `theme.py`, from the same machine: `list`, `icons`, `cursors`, `fonts`, `wallpapers`, `dynamic` and `tone` print the same bytes, and `render` writes the same eight files for Graphite, Gruvbox, Catppuccin Mocha and the dynamic theme.
- `test_theme.py` now sets `XDG_STATE_HOME` and `XDG_CACHE_HOME` to a temporary folder before importing the modules. A copy without those two lines, run with the real environment, wrote nothing under the theme, session, cache, icons, desktop, btop, Code or Herdr folders.
- The new modules were linked (`stow.py apply`) before the live panel ran `theme.py` again. `check.sh` passes.
## The installer in modules (#101), 2026-11-10

- `install-desktop.py` was split by the same script as `theme.py` (#103): top-level statements moved verbatim into `scripts/install/install_*.py`, every reference to a name now elsewhere rewritten as `module.name` (scope-aware, with `symtable`). Two cycles were cut by placement: `desktop_present` went to `install_undo` with the other uninstall checks, and `run_steps` with the messages around a run to `install_run`. `REPO` in `install_paths.py` is `parents[2]` from its new place.
- The guided installer and the three installer test files use the modules directly; every `installer.X`, `patch.object(installer, 'X')` and sandbox assignment points at the module that defines `X` (`install_paths.RECORD = …`). Each test file sets `XDG_STATE_HOME` to its temporary folder before importing.
- Against `main` from the same machine: `dry-run` (apart from the stow lines, which a second checkout cannot compare), `dry-run --uninstall`, `dry-run --remove radio`, `dry-run --profiles core,apps` and `--help` print the same; `profiles.py run dry-run - radio` too, and `profiles.py list` gives the same 37 units but `gaming.steam-hidpi`, whose only item is a Stow link the second checkout does not own. `profiles.py` (Settings → System → Profiles) and `test_profiles.py` use the modules as well. `install-tui.py --help` runs.
- `test_install` (197), `test_install_arch` (79) and `test_install_tui` (97) pass. Copies without the `XDG_STATE_HOME` line, run with the real environment, wrote nothing under `~/.local/state/dotfiles`, autostart, the caches, the zsh clones, Herdr, `~/.local/bin`, the desktop config or the theme state. `check.sh` passes.

## VS Code keyring (#161), 2026-11-11

- Reported: VS Code 1.146 under Hyprland showed *An OS keyring couldn't be identified* and offered weaker encryption. `oo7-daemon` owned `org.freedesktop.secrets`, the `default` alias pointed to `collection/login`, and its `Locked` property was `false` after the GDM sign-in.
- `electron.py apply` rewrote `~/.local/share/applications/com.microsoft.VSCode.desktop`: both `Exec` lines now carry `--password-store=gnome-libsecret` after the Wayland and IME flags, and `electron.py status` reports the entry current. `"password-store": "gnome-libsecret"` was also added to the user's `~/.vscode/argv.json`, outside the repository.
- `check.sh` passes (including `test_electron.py`). After a full VS Code restart from the launcher the user confirmed the keyring dialog no longer appears.

## Selection, state and primary action look different (#163), 2026-11-11

- `ActionButton` gained `tone` and `Theme` the derived `active` (accent at 22 %) and `selection` (text at 12 %). The 45 `highlighted` uses that were a keyboard selection or a state now say so; the 11 primary actions keep the accent fill. `ChoiceChips`, `ToggleTile` and the Launcher highlight use the same tokens. No behaviour changed.
- Seen on the external monitor (theme Dynamic, it_IT) after the live reload: Launcher, Clipboard, Radio and Calendar show a neutral selection; the Control Center, Network, Battery, Settings → Sound, Power and Appearance (Theme, Font) show tabs, sidebar row, current device and chosen font as an accent tint with accent text; `Apri console`, `Applica` and `Aggiorna` are the only accent fills. Not seen: the light themes, Recording, the share picker, Bluetooth with a connected device.
- `check.sh` passes.

## UI review, first fixes (#227, #201, #205, #193, #199, #226, #216, #183), 2026-11-11

- After the merges and a shell restart through Hyprland (`NoNewPrivs: 0`, "Configuration Loaded"), seen on the external monitor in it_IT: Settings → System → Plugins shows the rebuild log with no escape sequences and one line per step; the usage footer reads `Ultima lettura sab 16:10. Invia un messaggio nella console per rileggerli` while the 5-hour window has lapsed; Updates shows `Aggiornato alle 18:37` without the stop; Hints is titled `Suggerimenti · Scorciatoie da tastiera`; the power menu and the desktop menu both read `Sospendi… / Esci… / Riavvia… / Spegni…`; the Cursors tab offers `Apri la cartella dei cursori`; the Sound footer is one sentence; the shortcuts help quotes the literal key syntax.
- #203 was closed as not a bug: both places render `AgentView` from `Agent.consoleOpen`.
- `check.sh` passes on the merged `main`.

## One look for what is on (#164), 2026-11-11

- `ControlSwitch` on is the accent tint with an accent knob, off is grey on grey; a checked `ToggleTile` keeps the tint and the accent icon without the accent border; the row with the keyboard in an options page is `Theme.selection` without a border. Seen live in Settings → Desktop, the Control Center and Network. Not seen: light themes, tablet sizes.
- `check.sh` passes.

## One panel header (#166), 2026-11-11

- `PanelHeader` gained `settingsSection` / `showSettings`: the `Impostazioni…` link at the bottom of the Control Center, Network, Bluetooth, Agent, Updates and Displays is now a button in the header, next to close. Audio, Hints, the Wallpaper picker and the Calendar use `PanelHeader` too, so their `Chiudi` buttons at the bottom are gone and Audio goes back with the arrow at the top left like Network and Bluetooth.
- Seen live on the external monitor: the ten panels above open, show the header, and close; `qs log` has no error. Not done here, still open in #166: Audio and Displays stay centred dialogs, and the panel widths are unchanged. Settings gets its close button with #214.
- `check.sh` passes.

## Key hints in one wording (#167), 2026-11-11

- The six footers (Launcher, Clipboard, Radio, Calendar, power menu, Appearance) follow the one the option pages had: `KEY action · KEY action`, arrows as `↑↓` and `←→`, in both catalogs. Seen live in it_IT for five of them; the Calendar one was not in the capture. Still open in #167: keys drawn as keycaps, and a footer on the pages that have none.
- `check-i18n.py` passes.

## Text buttons have a shape (#168), 2026-11-11

- `ActionButton` gained `outlined` (a 1 px `Theme.stroke` border at rest, kept when disabled); 56 standalone text buttons set it: the actions of Settings (System, Appearance, Keyboard, Displays, Assistant), the Wallpaper picker, Calendar, Network, Clipboard, notification actions and the Cancel / Close buttons of the dialogs. List rows, tabs, chips and icon buttons are unchanged.
- Seen live: System → Advanced, Profiles, Plugins, Appearance → Cursors and Font, Keyboard, Calendar, the Wallpaper picker. Not seen: the authentication and pairing dialogs, Network details, notification actions.
- `check.sh` passes.

## One section heading (#169), 2026-11-11

- `Heading` gained `section`: muted, 12 px, demi-bold, the look the option pages already had for their groups. Audio (`Uscita`, `Applicazioni`, `Ingresso`), Battery, the usage title of the assistant, the two Font lists (no longer uppercase, in both catalogs) and the Network labels (`Connessione attuale`, `VPN`, `Hotspot personale`) use it.
- Seen live: Settings → Sound, Network, Assistant and the Battery panel. Not captured: Appearance → Font. Still open in #169: which pages group their rows in cards.
- `check.sh` passes. `qs log` repeats one warning that predates this work, `SettingsPanel.qml[249:29]: Unable to assign [undefined] to QString` (the sidebar rows that are sections have no `label`).

## Settings close, tabs, width, About and Profiles (#214, #215, #170, #229, #228), 2026-11-11

- Settings has a close button (`PanelIconButton`, `close`) anchored to the top right of its card, over the sidebar (compact) and every section. The tabs of Appearance and System are on their own row under the section title, left-aligned. `SettingsPanel.readableWidth` (720 px) caps the sections of option rows and lists (left-aligned); Appearance, Displays and System → Profiles and Plugins keep the whole width. System → About has **Copy** (`wl-copy`, one `label: value` line per row) and opens the repository folder from its path. Profiles draws **Remove** as an outlined button; the danger colour stays on the Apply of a removal plan. The sidebar warning `SettingsPanel.qml[249:29]` is gone from the code (group label bound with `?? ""`).
- Written in a worktree, not seen live. `check.sh` passes.
