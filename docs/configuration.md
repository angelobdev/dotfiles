# Configuration

[← README](../README.md)

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
| `services/` | State and backend connections; `assets/icons/` contains icons. |

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

- [`it_IT.json`](../quickshell/.config/quickshell/desktop/i18n/it_IT.json)
- [`en_US.json`](../quickshell/.config/quickshell/desktop/i18n/en_US.json)

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

## Control Center configuration

Edit `quickshell/.config/quickshell/desktop/Config.qml`. Configuration is declarative, with no UI editor:

```qml
readonly property var controlCenterModules: ["network", "bluetooth", "brightness", "audio", "media", "doNotDisturb", "idle"]
readonly property int controlCenterWidth: 400
readonly property bool expandMonitors: false
readonly property bool expandAudioDevices: false
readonly property string primaryMonitor: "eDP-1"
readonly property var brightnessDevices: ({})
```

Removing a name disables its module; reordering the list changes the layout. Unknown and duplicate names are ignored. Each module has its own file in `controlcenter/`. Network and Bluetooth each occupy half a row; other modules occupy a full row. The panel scrolls when expanded sections exceed the available space. If the primary monitor is disconnected, the first connected display is used.

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
```

The picker starts at home and supports moving to parent directories, entering a path, and opening the wallpaper collection. It supports PNG, JPEG, WebP, JXL, AVIF, BMP, and TIFF. ImageMagick converts the selected file into a managed JPEG, applies EXIF orientation, and preserves the original. Preview support depends on Qt decoders; a JXL without a preview can still be converted and applied.

Selection lives in `~/.local/state/desktop-session/wallpaper/`: `selection.json` stores the original path and `current.jpg` points to the converted copy. Hyprpaper uses that link in the Stow configuration and restores the selection at login; the repository is not rewritten on each wallpaper change. `desktop-session start` initializes the Fedora wallpaper link only when missing. Failed conversion or application preserves the previous selection. The local copy remains usable if the original moves.

State data is excluded from Git and follows this repository's standard XDG layout. The script serializes concurrent requests, passes paths as arguments, and normalizes the name sent through IPC, including spaces, commas, and special characters.

## Application theme

Dark glass theme: translucent graphite surfaces in Quickshell, Hyprland blur, and opaque text. Shell surfaces use the native palette's RGB values (`#191a1d`, `#202226`, `#292b30`) with separate alpha. Selected elements use opaque dark text for contrast. Kitty uses a 94% opaque background, Adwaita Mono, and matching ANSI colors; text stays opaque. Hyprland window borders remain disabled and inactive window opacity stays at 0.92.

The palette uses graphite gray, neutral primary `#d4d6dc`, light text, Adwaita Sans, and Papirus-Dark icons. GTK, Qt, and hyprlock share the palette; GSettings uses the slate accent. GTK 3 uses Adwaita-dark and CSS colors; GTK 4/libadwaita receives the dark preference through GSettings/the portal and named colors. Qt Widgets uses Fusion and custom palettes for both generations. The installed qt6ct plugin also accepts `qt5ct`, so `QT_QPA_PLATFORMTHEME=qt5ct` covers Qt 5/6. Qt Quick Controls uses Basic; applications with their own styling may ignore these preferences.

`desktop-theme` applies GSettings and imports Qt variables into D-Bus/systemd; on its first run it saves previous values to `~/.local/state/dotfiles/interface-before-theme.ini`. Restart open applications to adopt the theme; the next login also applies the full environment. Flatpak applications depend on sandbox runtimes/themes and may not follow every CSS override.

The shell uses dark translucent surfaces with blur and thin neutral borders. Hyprland draws no window borders: active/fullscreen opacity 1, inactive opacity 0.92, and blur enabled. These values are in `hypr/.config/hypr/config/appearance.lua`. Active windows retain full readability.

## Media and calendars

The Control Center's `media` module uses native Quickshell MPRIS: title/artist, previous, play/pause, next, and position when exposed by the player. With multiple players, select the desired one. Buttons follow the application's published capabilities; `playerctl` is not required.

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
