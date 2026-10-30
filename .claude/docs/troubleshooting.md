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

## XWayland scaling verification

Cursor captures over floating zenity windows showed the X11 pointer as the X server's blocky fallback arrow while Wayland windows used Adwaita; naming the theme and a 40 px size fixed it. After `desktop-xwayland apply` (eDP-1, scale 1.667 → `Xft.dpi` 160, `Xcursor.theme` Adwaita, `Xcursor.size` 40), an X11 zenity started without `XCURSOR_SIZE` showed the Adwaita arrow at the Wayland size and normal-size text, and `qt6ct` on `xcb` rendered identically to its Wayland instance. `Hyprland --verify-config` accepted `hl.on("monitor.added"/"monitor.removed")`. The Aseprite ini edit was tested on copies (only `screen_scale` changed; missing section or file handled), and the wrapper started a test command without `XCURSOR_SIZE`. `steam_command` now yields `-forcedesktopscaling 1.667` on eDP-1; the user confirmed Steam. Aseprite first received 2 (the nearest whole number to 1.667), which looks like 1x because X11 draws in physical pixels; the wrapper now multiplies its 200% base by the monitor scale, giving 3 on the built-in panel. Its default pixel cursor then became huge: laf builds custom X cursors at surface size × scale, while native cursors come from the X theme (`XCreateFontCursor`, themed by libXcursor at `Xcursor.size`), so the wrapper enables `use_native_cursor` (default `false` in Aseprite's `pref.xml`) only when the key is absent. The previous Steam settings are in `~/.config/desktop/steam.json.bak-before-fractional`. `XCURSOR_SIZE` stays in the current session's environment until the next login; the Steam and Aseprite wrappers already drop it.

## Steam and gamescope verification

The user confirmed improved text clarity with 1:1 XWayland rendering, but changing `-forcedesktopscaling` from 1.667 to 2 did not visibly enlarge the interface. Exporting `STEAM_FORCE_DESKTOPUI_SCALING` to both client and web helper also left the header unchanged. Steam's Interface HiDPI switch was already on. SDL reported content scale 1 through Wayland and 2 through X11 with its hint, but that alternate backend did not change the desktop UI either. Those diagnostics establish that startup arguments and environment alone are insufficient for this installed build.

The renderer initialization workaround was then verified with cropped menu screenshots: the same 500×95 logical region showed visibly doubled labels and controls after setting the CEF scale to 2 at initialization. A subsequent restart through the permanent runtime wrapper retained the enlarged rendering. `/proc` checks confirmed the managed library in all eight web-helper processes and absent from the main Steam client's preload environment; temporary test preloads were removed by the clean restart. No Steam binaries or startup scripts were edited, no debugger remains attached, and no debugging port was enabled. See [Steam and gamescope](integrations.md#steam-and-gamescope) for implementation and disabling the workaround.

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
- `check-i18n.py` now finds the keys after every `i18n.py` call in `shell/.local/bin/desktop-*` and `hypr/config/*.lua` (desktop-power, desktop-ai, binds.lua today), and the shared-catalog test uses `network.passwordFor` with a `$&` argument.
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

