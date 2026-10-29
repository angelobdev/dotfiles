# Configuration

[← README](../../README.md)

## Quickshell layout

Under `quickshell/.config/quickshell/desktop/`, `shell.qml` is the desktop entry point and `share.qml` is the sharing picker's entry point. `Config.qml`, `Theme.qml`, `ShellState.qml`, and the `I18n.qml` singleton remain at the root.

| Directory | Contents |
| --- | --- |
| `bar/` | Bar, workspaces, and bar buttons; `tray/` contains tray menus. |
| `controlcenter/` | Control Center panel and modules loaded from configuration. |
| `panels/` | Launcher, network, Bluetooth, audio, battery, calendar, Hints, clipboard, recording, and wallpapers. |
| `notifications/` | Notification center, popups, and notification-specific components. |
| `session/` | Power menu and Polkit/Bluetooth authentication prompts. |
| `osd/` | Temporary volume and brightness indicators. |
| `i18n/` | Italian/US English JSON catalogs, locale selection (`Locale.js`), and source-label adapters (`Sources.js`). |
| `components/` | Shared buttons, sliders, cards, and other reusable elements. |
| `services/` | State and backend connections; `assets/icons/` contains icons, exported from the Figma file [Desktop Icons](https://www.figma.com/design/FYQsa6b0razfxqGI4Q9rG5) (components `icon/<name>`; re-export as SVG with `white` fills and strokes). |

Function-specific components stay beside their callers; components used by several panels remain in `components/`. The generic `modules/` directory has been removed.

## Interface language

The language is read from `/etc/locale.conf`, without executing the file as a script. `LC_MESSAGES`, when present, takes precedence over `LANG`:

```ini
LANG="en_US.UTF-8"
# Keep the other system formats while using Italian interface messages:
# LC_MESSAGES="it_IT.UTF-8"
```

Italian variants use `it_IT.json`; English variants use `en_US.json`. Unsupported languages, `C`, and `POSIX` fall back to US English. If the file is missing or has no usable settings, environment variables `LC_ALL`, `LC_MESSAGES`, and `LANG` are consulted in that order. File settings take precedence over the environment inherited from the session.

`I18n.qml` watches the system file and catalogs: declarative text and formats update when they change. Python helpers read the same setting when producing a message; existing errors and history retain the text they received. `desktop-shell status` exposes the selected language in the `language` field. No additional packages are required.

Translations cover panels, controls, tooltips, Hints, the sharing picker, and messages owned by the helpers. The calendar uses localized names and the locale's first weekday (Monday for Italian, Sunday for US English), with 24/12-hour time formats; decimal numbers follow the same language. Application-supplied names and content, received notifications, events, tray entries, and service authentication prompts retain their source text. Known bind descriptions are translated in Hints; unknown custom descriptions remain as written in Lua.

Both catalogs share the same keys:

- [`it_IT.json`](../../quickshell/.config/quickshell/desktop/i18n/it_IT.json)
- [`en_US.json`](../../quickshell/.config/quickshell/desktop/i18n/en_US.json)

Catalogs are nested JSON objects grouped by function, with English camelCase keys independent of the translated text:

```json
{
  "clipboard": {
    "title": "Clipboard",
    "deleteItem": "Delete item"
  }
}
```

To add text, add the same path to both files and use `I18n.tr("clipboard.deleteItem")` in QML or `tr('clipboard.deleteItem')` in Python helpers. Parameters use `%1`, `%2`, etc., for example `I18n.tr("bindings.moveToWorkspace", [4])`. For singular/plural messages, use `I18n.plural("bluetooth.connectedCount.one", "bluetooth.connectedCount.other", count)`: `%1` receives the count. A missing key falls back to the English catalog, then to the path itself to help identify omissions. Do not use source sentences as keys or translate internal identifiers, commands, or protocol names.

`i18n/Sources.js` maps English Hyprland bind descriptions and network status labels to semantic paths. These strings are API input data; catalogs and `tr()` calls use only semantic keys. Unknown custom descriptions are preserved. Keep all source code, comments, documentation, and default labels in English; Italian text belongs only in `i18n/it_IT.json`. Tests read Italian expectations from that catalog rather than duplicating translations in fixtures.

`python3 scripts/check-i18n.py`, included in `./scripts/check.sh`, checks locale selection, nested key structure/parity, parameters, fallback, and QML/Python/command/adapter references. Run Stow after adding files; restart the shell after changing singleton code.

## Saved shell state

`~/.local/state/desktop-shell/`:
- **`session.json`** `{"keepAwake", "quiet", "rotationLock", "oskFloating", "oskExtra"}`: Keep awake, Do Not Disturb, rotation lock and the on-screen keyboard form (`services/SessionState.qml`). A missing file means all off.
- **`notifications.json`** `{"entries": [...]}`: the notification history (app name and icon, summary, body, arrival time). It is rewritten 500 ms after a notification arrives or closes and after Delete or Clear all. Entries are capped at 50 and dropped after 7 days on load. Icons a notification served itself (`image://`) are not kept.
- **`dock.json`**: dock pins.

Delete a file to reset it. `desktop-shell keep-awake|dnd|rotation-lock toggle|on|off` sets the switches from scripts.

## On-screen keyboard

- **Layout:** `osk/layouts/<Config.oskLayout>.json` (`it`): pages of rows, each key an evdev code with its label, optional modifier mask (Shift 1, Ctrl 4, Alt 8, AltGr 128) and Shift label; rows are 10 units wide. `accents` lists the long-press variants and `extra` the optional row. `test_osk.py` checks every label against what the key types in the XKB keymap.
- **Typing:** `libexec/desktop/osk.py run`, started the first time the keyboard opens and then kept, creates a `zwp_virtual_keyboard_v1` with the keymap of Hyprland `input:kb_layout`/`kb_variant`/`kb_options` (compiled by libxkbcommon), so keys mean what the physical keyboard would. The shell writes `key CODE MODS` lines to it. It speaks the Wayland wire protocol directly: no packages beyond Python and libxkbcommon. `osk.py check CODE MODS` prints what a key types.
- **Automatic opening:** with `Config.oskAutoShow` the helper starts with the shell as `osk.py run --input-method` and also binds `zwp_input_method_v2`, only as a signal: activate, deactivate and the content purpose (applied on `done`) become `{"event": "activate", "purpose": ...}` / `{"event": "deactivate"}` lines. Text still goes through the virtual keyboard, which works in every app. It needs no IBus or fcitx; if another input method holds the seat, the protocol reports `unavailable` and the keyboard opens only by hand. A field change waits 300 ms before closing, so moving between fields does not flicker.
- **Surfaces:** layer namespace `desktop-osk`, blurred like the panels. Docked it is a Top layer anchored to the bottom with an exclusive zone; floating, a full-screen Overlay layer whose input region is the keyboard. Neither takes keyboard focus.

## Tablet mode and rotation

- **Touch scale:** `Theme.hit(n)` is `n × Theme.touchScale`, which is `Config.touchScale` (1.25) in tablet mode and 1 otherwise; `Theme.barHeight` is `hit(38)`. Components size their hit targets through it.
- **Posture:** `hypr/config/tablet.lua` binds `switch:on/off` of the tablet mode switch to `desktop-shell tablet on|off`. The switch is named in `local.lua` (`require("config.tablet").switch("Intel HID switches")`, as `hyprctl devices` lists it). `services/Tablet.qml` keeps the posture in `$XDG_RUNTIME_DIR/desktop-shell/tablet.json`, so a shell restart keeps it and a new session starts in laptop mode until the switch reports. The switch binds are left out of Hints.
- **Sensor:** `libexec/desktop/rotation.py watch` claims the iio-sensor-proxy accelerometer over D-Bus only while tablet mode is on and rotation is unlocked, and prints its orientation as a Hyprland transform (normal 0, left-up 1, bottom-up 2, right-up 3; flat keeps the last one). `rotation.py probe` tells the shell whether there is an accelerometer.
- **Rotation:** `rotation.py apply N` writes `~/.local/state/desktop-session/rotation.lua` and runs `hyprctl eval 'desktop_rotate(N)'`. `monitors.lua` declares the built-in display through `require("config.tablet").monitor({...})`, which applies the saved transform, so a config reload (a theme change, for one) keeps the rotation. `input.touchdevice` and `input.tablet` get the same transform and are mapped to that output.

## Dock configuration

In `Config.qml`: `dockEnabled: true`; `dockPinned`, the default pins as desktop-entry IDs (file names without `.desktop`): Kitty, Zen, Files, VS Code, ChatGPT, the AI assistant and Steam, with unknown IDs skipped; `dockIconSize: 44` (logical px); `dockMagnification: 1.4`, the peak scale under the pointer (1 turns it off); `dockTriggerHeight: 3`, the height of the reveal strip (1 px can round away at fractional scales); `dockRevealDelay: 120` ms of hover before it slides up.

The first pin change (menu, drag, launcher) writes `~/.local/state/desktop-shell/dock.json` (`{"pinned": [...]}`, atomic write); from then on it replaces `dockPinned`. Pins of apps that are not installed stay in the file but are not shown. Delete the file to return to `dockPinned`; the shell picks up edits to it live. The layer namespace is `desktop-dock` (blurred like the panels, Hyprglass, no compositor animation); its surface is 190 px tall to draw a pin being dragged off, but input only reaches the reveal strip and the dock body. The context menu uses the `desktop-tray-menu` namespace; keyboard mode maps a transparent full-screen `desktop-dock-keys` surface whose input region excludes the dock, so an outside click ends keyboard mode.

## Control Center configuration

Edit `quickshell/.config/quickshell/desktop/Config.qml`. Configuration is declarative, with no UI editor:

```qml
readonly property var controlCenterModules: ["network", "bluetooth", "brightness", "audio", "media", "doNotDisturb", "idle", "rotation"]
readonly property int controlCenterWidth: 400
readonly property bool expandMonitors: false
readonly property bool expandAudioDevices: false
readonly property var dnsPresets: [{ name: "Cloudflare", servers: ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"] }, …]
readonly property string primaryMonitor: "eDP-1"
readonly property var brightnessDevices: ({})
```

`dnsPresets` lists the DNS choices in the network details view (Cloudflare, Quad9, Google, and AdGuard by default); each preset gives IPv4 and IPv6 servers. Applying a preset or custom servers sets `ipv4/ipv6.dns` with `ignore-auto-dns` on the saved NetworkManager profile and reapplies it to an active device without disconnecting; **Automatic** restores the router's DNS.

Removing a name disables its module; reordering the list changes the layout. `rotation` hides itself where there is no accelerometer. Unknown and duplicate names are ignored. Each module has its own file in `controlcenter/`. Network and Bluetooth each occupy half a row; other modules occupy a full row. The panel scrolls when expanded sections exceed the available space. If the primary monitor is disconnected, the first connected display is used.

Brightness uses hardware control: a single eDP/LVDS/DSI panel backlight is detected automatically and controlled through `brightnessctl`. Brightness keys retain control of the built-in backlight. For multiple backlights or external monitors, explicitly associate the name returned by `hyprctl monitors` with a device:

```qml
readonly property var brightnessDevices: ({
    "eDP-1": { "type": "backlight", "device": "intel_backlight" },
    "DP-1": { "type": "ddc", "bus": 6 }
})
```

Bus `6` is an example: use the actual bus shown by `ddcutil detect`. For DDC/CI, optionally install `sudo dnf install ddcutil`, enable DDC/CI on the monitor, and check the package's `/dev/i2c-*` permissions. The shell does not run sudo. After the initial installation, apply permissions to already connected devices: `sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=i2c-dev && sudo udevadm trigger --subsystem-match=drm`. A monitor without a backend or hardware access shows a disabled slider and an explanation. The expandable section lists only other connected monitors; hotplug and values update while the Control Center is open. The slider and percentage immediately follow the selected value; writes are sent about every 70 ms during dragging, coalesced and serialized. Hardware readings are reconciled afterward without restoring stale values. The minimum is 1% to avoid accidentally turning off the backlight. Software opacity is not used to simulate brightness.

Audio and Bluetooth use native Quickshell APIs. Bluetooth also uses a Python/Gio helper registered as a BlueZ `KeyboardDisplay` agent: PINs, confirmations, and authorizations require an explicit response, with a 120-second timeout. Scanning stops when the panel closes; pairing does not automatically trust a device. Select the device after pairing to connect it. Hints sections are inferred from real binding keys/descriptions: unrecognized custom bindings remain searchable under Other.

## Volume and brightness OSD

OSDs update when system levels change, including through multimedia keys or external commands. Volume and mute follow PipeWire; the microphone has its own indicator. Backlight brightness is read from sysfs every 150 ms by one persistent helper, without starting a command for each reading. Configured and available DDC/CI monitors use the existing periodic readings (about 3 seconds, depending on the monitor).

The indicator appears on the monitor whose brightness changed, or on the focused monitor for audio. It disappears 1.7 seconds after the last update. It is suppressed on initial device readings and while the Control Center is open; audio indicators are also suppressed in the Audio panel, where the level is already visible. Do Not Disturb silences notifications and leaves OSDs available. No new packages are needed.

Configuration lives in `quickshell/.config/quickshell/desktop/Config.qml`:

```qml
readonly property bool osdEnabled: true
readonly property int osdTimeout: 1700
readonly property int osdWidth: 320
readonly property int osdBottomMargin: 96
```

Dimensions and margins are in logical pixels; the timeout is in milliseconds. Disabling `osdEnabled` hides OSDs and stops the backlight watcher while retaining panel controls. Only actual changes are shown: pressing a key again at the limit does not create a new OSD.

## Persistent wallpapers

```sh
~/.local/bin/desktop-wallpaper                     # open the QML picker
~/.local/bin/desktop-wallpaper /path/to/image.png
~/.local/bin/desktop-wallpaper --reset             # restore Fedora wallpaper
~/.local/bin/desktop-wallpaper --next              # next wallpaper of the current theme (Super + Ctrl + W)
```

The picker starts at home and supports moving to parent directories, entering a path, and opening the wallpaper collection. It supports PNG, JPEG, WebP, JXL, AVIF, BMP, and TIFF. ImageMagick converts the selected file into a managed JPEG, applies EXIF orientation, and preserves the original. Preview support depends on Qt decoders; a JXL without a preview can still be converted and applied.

Selection lives in `~/.local/state/desktop-session/wallpaper/`: `selection.json` stores the original path and `current.jpg` points to the converted copy. Hyprpaper uses that link in the Stow configuration and restores the selection at login; the repository is not rewritten on each wallpaper change. `desktop-session start` initializes the Fedora wallpaper link only when missing. Failed conversion or application preserves the previous selection. The local copy remains usable if the original moves.

### Wallpapers per theme

Each theme has its own set of wallpapers:
- **Graphite** uses the images in `~/.local/share/wallpapers` and `~/Pictures/Wallpapers` (`wallpaperDirectories`).
- **The other four** list eight each in their `theme.json` (`wallpapers`). Each entry has a file name, a raw GitHub URL pinned to a commit, a sha256 and its source.

Downloads:
- They are fetched only when needed into `~/.local/share/desktop/wallpapers/<theme>/` and never committed.
- A file is kept only when its sha256 matches. A failed or mismatched download is discarded, and the other entries still download.
- `python3 ~/.local/libexec/desktop/theme.py fetch <theme>` downloads a whole set ahead of time.
- `theme.py wallpapers [<theme>]` prints the set as JSON.

Switching theme also switches the wallpaper:
- `desktop-theme set` first remembers the current wallpaper (`selection.json` source) under the theme being left, in `~/.local/state/desktop-theme/wallpapers.json`.
- In the background it then applies the new theme's remembered wallpaper, or its first one, downloading the set if needed (log in `wallpapers.log` there).
- Wallpapers picked with `Super + Shift + W` or `Super + Ctrl + W` are remembered the same way.
- `Super + Ctrl + W` cycles through the current theme's set in order. If nothing is downloaded yet, it starts the download and shows a notification.

Sources:
- Omarchy's theme backgrounds (`basecamp/omarchy`, MIT);
- `zhichaoh/catppuccin-wallpapers` (MIT);
- `AngelJumbo/gruvbox-wallpapers` and `Apeiros-46B/everforest-walls`.

The last two declare no licence; their images are fetched for personal use and not redistributed. To change a set, edit `wallpapers` in the theme: a removed entry stays on disk until deleted from `~/.local/share/desktop/wallpapers/`.

State data is excluded from Git and follows this repository's standard XDG layout. The script serializes concurrent requests, passes paths as arguments, and normalizes the name sent through IPC, including spaces, commas, and special characters.

## Application theme

Dark glass theme: translucent graphite surfaces in Quickshell, Hyprland blur, and opaque text. Shell surfaces use the native palette's RGB values (`#191a1d`, `#202226`, `#292b30`) with separate alpha. Selected elements use opaque dark text for contrast. Kitty uses a 94% opaque background, Adwaita Mono, and matching ANSI colors; text stays opaque. Hyprland window borders remain disabled and inactive window opacity stays at 0.92.

The palette uses graphite gray, neutral primary `#d4d6dc`, light text, Adwaita Sans, and Papirus-Dark icons. GTK, Qt, and hyprlock share the palette; GSettings uses the slate accent. GTK 3 uses Adwaita-dark and CSS colors; GTK 4/libadwaita receives the dark preference through GSettings/the portal and named colors. Qt Widgets uses Fusion and custom palettes for both generations. The installed qt6ct plugin also accepts `qt5ct`, so `QT_QPA_PLATFORMTHEME=qt5ct` covers Qt 5/6. Qt Quick Controls uses Basic; applications with their own styling may ignore these preferences.

`desktop-theme` applies GSettings and imports Qt variables into D-Bus/systemd; on its first run it saves previous values to `~/.local/state/dotfiles/interface-before-theme.ini`. Restart open applications to adopt the theme; the next login also applies the full environment. Flatpak applications depend on sandbox runtimes/themes and may not follow every CSS override.

## Themes

The palette above is the **Graphite** theme. Four more ship with the dotfiles, all dark:

| Theme | Accent | GSettings accent | VS Code |
| --- | --- | --- | --- |
| `catppuccin-mocha` | mauve `#cba6f7` | purple | Catppuccin Mocha |
| `tokyo-night` | blue `#7aa2f7` | blue | Tokyo Night |
| `gruvbox` | yellow `#fabd2f` | yellow | Gruvbox Dark Medium |
| `everforest` | green `#a7c080` | green | Everforest Dark |

Graphite uses VS Code's own Default Dark Modern. Their surfaces and terminal colours come from each project's published palette and Kitty port.

A theme is one `theme.json` with:
- `mode`, `fonts` and `system` (GTK, icon and cursor theme, GSettings accent);
- `shell` (the `Theme.qml` tokens);
- `palette` (the semantic colours the application templates use);
- `ansi` (16 terminal colours), `terminal.opacity`;
- `hyprland` (shadow, Hyprglass tint).

- `vscode` (`theme`, optional `extension`).

Only `palette` (bg, base, raised, border, fg, muted, dim, accent, accentFg, link, danger, success, warning) and `ansi` are required. `theme.py` derives any missing value from them, and explicit values always win:
- the `shell` tokens, with Graphite's alphas;
- the Qt bevel shades;
- the Hyprland shadow and glass tint.

Colours are `#rrggbb` or `#rrggbbaa`. Shipped themes live in `~/.local/share/desktop/themes/<id>/` (from `shell/.local/share/desktop/themes/`). Themes in `~/.config/desktop/themes/<id>/` take precedence.

`desktop-theme` (run at every login) renders the current theme with the templates in `~/.local/share/desktop/templates/` into `~/.local/state/desktop-theme/`. It writes:
- `quickshell.json`, `hyprland.lua`, `kitty.conf`, `gtk.css`, `qt-colors.conf` and `hyprlock.conf`;
- the GSettings values, and `current.json` (`{"theme": "<id>"}`).

The stowed configs only point at those files:
- `Theme.qml` watches `quickshell.json`, so the shell changes live.
- `config/theme.lua` loads `hyprland.lua` on every Hyprland reload.
- `kitty.conf` ends with an `include`.
- `gtk.css` is a single relative `@import`.
- qt5ct/qt6ct: `qtct.conf.tpl` is rendered to `~/.config/qt5ct/qt5ct.conf` and `~/.config/qt6ct/qt6ct.conf`; they are no longer stowed. The rendered file sets the fonts, icon pack, Fusion style and `color_scheme_path` to `qt-colors.conf`. Settings saved from the qt5ct/qt6ct GUI land in that file and are replaced on the next theme change; set fonts and icons in the Theming panel instead.
- `desktop-power lock` passes `--config` to hyprlock when the themed file exists.

Each consumer keeps Graphite as its fallback, so a missing state directory changes nothing. GTK is the exception: it falls back to plain Adwaita-dark until the next `desktop-theme` run.

Other applications:
- **VS Code:** `desktop-theme set` replaces (or adds) `workbench.colorTheme` and the preferred theme for the mode in `~/.config/Code/User/settings.json`. The preferred key is `workbench.preferredDarkColorTheme` or `workbench.preferredLightColorTheme`; VS Code uses it instead of `colorTheme` while `window.autoDetectColorScheme` is on, as it is here. The edit is targeted and leaves the rest of the file alone, and VS Code applies it live.
  - It is skipped when the theme's extension is not installed or the file is not valid JSON.
  - The four extensions are Catppuccin.catppuccin-vsc, enkia.tokyo-night, jdinhlife.gruvbox and sainnhe.everforest.
  - Before the themes, `workbench.colorTheme` was unset (Default Dark Modern).
- **btop:** every theme, Graphite included, is written to `~/.config/btop/themes/desktop.theme`. `btop.conf` gets `color_theme = "desktop"`, and a running btop reloads on `SIGUSR2`.
  - The main background stays empty, so the translucent Kitty background shows through.
  - btop rewrites `btop.conf` on exit, so it is not stowed. Set `color_theme = "Default"` to go back.
- **Zen and other portal-aware apps** follow the `color-scheme` that `mode` sets (all shipped themes are dark; the dynamic one can be light).

Preferences: `~/.local/state/desktop-theme/preferences.json` holds what is chosen in the Theming panel, or with these commands:
- `desktop-theme font --sans F --mono F --size N --unified on|off` (`--default` clears them). `--unified on` makes the interface use the monospace family.
- `desktop-theme icon-theme NAME|default`.
- `desktop-theme shell-icons desktop|pack`: the shell glyphs from `assets/icons`, or the icon pack's symbolic icons mapped in `components/IconNames.js`.
- `desktop-theme bar-style shade|transparent|toggle`.
- `desktop-theme window-style --rounding N --border N` (`--default` clears them). Hyprland `decoration.rounding` and `general.border_size`, defaulting to 16 and 0. The border colours (`general.col.active_border` / `inactive_border`) are the theme's accent and border colours, rendered into `hyprland.lua` and applied with `hyprctl reload`. The same rounding reaches Quickshell as `rounding` in `quickshell.json`: `Theme.corner(n)` scales each design radius by rounding/16, and `Theme.radius` is `corner(18)`. Radii under 6 (dots, tracks) are not scaled. hyprlock gets `rounding = 26 × rounding/16` for its password field. The border width and both colours reach Quickshell as `borderSize`, `activeBorder` and `inactiveBorder`. While `borderSize` is above 0, `Theme.frameWidth` and `Theme.frameActive` frame `Card` (every panel), `PopupMenu` and the tray menu, and `Theme.frameInactive` frames the dock, the OSD and notification popups. At 0 they keep a 1 px `stroke`, and popups none.

The bar style and shell icon source reach Quickshell through `quickshell.json` (`barStyle`, `iconSource`).

`theme.py tone` measures the strip under the bar on the current wallpaper. It crops the wallpaper to the focused monitor's logical size as hyprpaper does (cover), takes the mean grey of the top 4%, and caches it in `tone.json`.

Text and icons then use whichever of the current theme's two text colours (`shell.text`, `shell.accentText`) has the higher WCAG contrast with that strip. The bar background stays transparent. `services/BarStyle.qml` runs it whenever the wallpaper or the bar style changes.

They are merged over every theme before rendering, and an unset key keeps the theme's value. `theme.py fonts` and `theme.py icons` print the choices the panel offers:
- fonts from `fc-list :lang=en`, with script-specific, symbol, serif and URW families left out;
- icon themes with at least two sample icons of their own, resolved through `Inherits`. This list is cached in `icons-cache.json` until an icon directory changes.

Commands:
- `desktop-theme set <id>` switches theme. It renders everything before writing anything, reloads Hyprland and Kitty (`SIGUSR1`), and sets GSettings.
- GTK and Qt applications adopt the new palette when restarted.
- `desktop-theme list` prints the themes as JSON.
- `python3 ~/.local/libexec/desktop/theme.py render --theme <id> --out <dir>` previews the output without applying it.

### Dynamic theme

`desktop-theme generate [--image PATH]` (the Dynamic card in the Theming panel) runs `matugen image PATH --json hex --dry-run --source-color-index 0` on the current wallpaper by default, and writes `~/.config/desktop/themes/dynamic/theme.json`. It then applies it like `desktop-theme set dynamic` and remembers the image as the theme's wallpaper.
- **Palette** from the Material roles: bg = `surface`; base = `surface_container_lowest` (dark) or `surface_container_low` (light); raised = `surface_container_high`; border = `outline_variant`; fg = `on_surface`; muted = `on_surface_variant`; dim = `outline`; accent = `primary`; accentFg = `on_primary`; link = `tertiary`; danger = `error`.
- **ANSI, success and warning** use the standard terminal hues (red, green, yellow, blue, magenta, cyan), each turned at most 15° toward the primary, as Material harmonizes custom colours. matugen's base16 is not used, because it holds the image's own colours in no hue order. Their HSL lightness is then moved away from bg until they reach 3:1 (normal colours) or 4.5:1 (bright colours, which are also success and warning). Black and white come from the surfaces.
- **System:** Adwaita or Adwaita-dark, Papirus-Dark or Papirus-Light, the GSettings accent nearest to the primary hue (slate when it is grey), VS Code Default Dark Modern or Default Light Modern.
- **Light mode:** the bar shade uses bg at 60%/53% instead of black, so its dark text stays readable. This applies to any theme with `"mode": "light"` that does not set `barShadeTop`/`barShadeBottom`.
- `wallpaperDirectories` is the image's folder, so `Super + Ctrl + W` cycles it.

`desktop-theme dynamic --mode auto|dark|light --scheme tonal-spot|vibrant|expressive|fidelity|neutral` stores `dynamic` in `preferences.json` (matugen `-m smart|dark|light` and `-t scheme-…`) and regenerates when the dynamic theme is current. `services/DynamicTheme.qml` watches `current.json`, the wallpaper selection and the generated theme: while the theme is `dynamic` and the wallpaper is not its `source`, it runs `theme.py generate`, one run at a time.

Templates use `{{ path }}` or `{{ path | filter }}`, with the filters `hex`, `rgba[:aa]`, `qt[:aa]`, `hypr` and `hexrgba`. A key the theme lacks is an error, never an empty value.

The shell uses dark translucent surfaces with blur and thin neutral borders. Hyprland draws no window borders: active/fullscreen opacity 1, inactive opacity 0.92, and blur enabled. These values are in `hypr/.config/hypr/config/appearance.lua`. Active windows retain full readability.

## Motion

Animations are restrained: quick ease-out entrances, quicker accelerating exits, and no overshoot. Hyprland (`appearance.lua`) defines the curves `out`, `accel`, and `inout` plus a critically damped spring `move`. Windows pop in from 87% with a fade (about 220 ms) and pop out to 92% (about 150 ms); tiling reflow, dragging, and resizing use the spring; workspaces slide with a fade over 18% of the width (special workspace vertically); focus, dim, shadow, border, layer, and popup fades take 140–250 ms. `speed` is in deciseconds. A layer rule in `rules.lua` turns compositor animations off for `desktop-overlay` and `desktop-osd`, which Quickshell animates itself.

Quickshell panels share the same curves through `Theme.easeOut`/`Theme.easeIn` and the durations `Theme.motionFast` (120 ms), `motionNormal` (220 ms), and `motionSlow` (320 ms). Side panels slide 10 px down from the bar and scale from 97% while fading in; centred dialogs scale from the middle. Closing reverses it in 120 ms, during which the panel no longer takes keyboard focus or clicks. Moving between the Control Center and its sub-panels (Network, Bluetooth, Audio tiles; Back) pushes sideways instead: the new panel enters from the direction of travel and the old one leaves the other way (`ShellState.push()`/`back()`); the network list and details view slide the same way. Notification toasts slide in from the right, leave to the right, and the stack moves smoothly to fill gaps; the OSD rises 8 px while fading in. `desktop-notifications` is also excluded from compositor layer animations. Smaller touches: Control Center sections (audio devices, other displays) grow and fade open with a rotating chevron; buttons sink slightly while pressed (by at most about 6 px, so wide rows barely move); the launcher selection glides between rows; notification-center entries fade in, leave to the right, and the list closes the gap; icons cross-fade when they change (mute, Wi-Fi strength, play/pause, battery level). Set `reduceMotion: true` in `Config.qml` to turn the shell's animations off; turn Hyprland's off with `animations = { enabled = false }` in `config/local.lua`.

## Media and calendars

The Control Center's `media` module uses native Quickshell MPRIS: title/artist, previous, play/pause, next, and position when exposed by the player. With multiple players, select the desired one. Buttons and XF86 transport keys follow the application's published capabilities; `playerctl` is not required. `desktop-shell media {play-pause|play|pause|next|previous|stop}` routes commands through the shell's native MPRIS service and respects the selected player. Unknown actions are rejected by the wrapper, and unavailable/unsupported actions produce no playback change.

`calendarSources: []` in `Config.qml` includes all enabled EDS calendars. To limit them, supply source UIDs, for example `calendarSources: ["system-calendar"]`. Names can change; UIDs identify sources. Configure accounts using the existing GNOME tools; the panel uses the same credentials and events without storing passwords in the repository. EDS expands recurrences. The calendar refreshes events on opening, month changes, every minute while open, and with **Refresh**. Errors show the cause and preserve already loaded events in memory for the unavailable source.

To list local UIDs:

```sh
python3 - <<'PY'
import gi
gi.require_version('EDataServer', '1.2')
from gi.repository import EDataServer
registry = EDataServer.SourceRegistry.new_sync(None)
for source in registry.list_enabled('Calendar'):
    print(source.get_uid(), source.get_display_name())
PY
```

## Philips FTV display: verification results

On October 12, 2026, Hyprland exposed the HDMI-connected display as `DP-1`, I²C bus 14. After installing `ddcutil` and applying udev rules, EDID and connector information were readable, but `getvcp 10` and `capabilities` did not respond correctly; reads also failed with initial checks disabled and longer timings. No hardware value was written. Physical hotplug was verified: the monitor and controls disappear on disconnection and return on reconnection.

GNOME's built-in control can use software brightness through Mutter, especially in HDR: see the [GNOME developer's explanation](https://blog.sebastianwick.net/posts/gnome-49-backlight-changes/). This may explain the different behavior; it does not prove that the Philips exposes DDC/CI. This desktop controls hardware backlight/DDC without automatically introducing a software dimmer. A successful read/write/restore DDC test requires a display that responds to the protocol.

## Removable media

The `udiskie` Stow package manages `~/.config/udiskie/config.yml`. `desktop-session start` launches one udiskie process alongside hyprpaper/hypridle, with logs in `~/.local/state/desktop-session/udiskie.log`; repeated startup does not create duplicate processes. `desktop-session status` includes udiskie.

Automatic mounting and notifications are enabled, the tray icon is disabled, and system-internal disks are ignored. Notification browsing opens Nautilus; Quickshell displays the notifications using its existing notification server. Mounted drives normally appear under `/run/media/$USER/` and in Files. Use Files' eject control before unplugging a drive, or run `udiskie-umount --detach "/run/media/$USER/DRIVE_LABEL"` for a specific USB drive. Close files on the drive first.

After changing the udiskie configuration, restart only that daemon:

```sh
pkill -x udiskie
desktop-session start
```

Udiskie manages UDisks block devices. iPhones use the separate GVfs/AFC backend; see [iPhone access](integrations.md#removable-drives-and-iphone).
