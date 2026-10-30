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
- **`session.json`** `{"keepAwake", "quiet", "rotationLock", "oskFloating", "oskExtra", "oskTouch", "nightShiftMode", "nightShiftTemperature"}`: Keep awake, Do Not Disturb, rotation lock and the on-screen keyboard form (`services/SessionState.qml`). A missing file means all off.
- **`notifications.json`** `{"entries": [...]}`: the notification history (app name and icon, summary, body, arrival time, and `live` for copies of notifications that were open). On load, live copies wait 1.5 s for the server to restore its notifications after a config reload: a copy that matches one (id, app, summary and body, as ids restart at 1 in every Quickshell process) is dropped and gives back its arrival time; one that does not was open in a process that has gone and joins the archive. Duplicates are dropped. It is rewritten 500 ms after a notification arrives or closes and after Delete or Clear all. Entries are capped at 50 and dropped after 7 days on load. Icons a notification served itself (`image://`) are not kept.
- **`dock.json`**: dock pins.
- **`updates.json`**: the last update check (`updates.py check`, see integrations.md).
- **`agent-usage.json`**: the assistant's model, context and subscription limits, written by its status line (`agent.py statusline`, see integrations.md); the live state is in `$XDG_RUNTIME_DIR/desktop-shell/agent.json`.

Delete a file to reset it. `desktop-shell keep-awake|dnd|rotation-lock toggle|on|off` sets the switches from scripts.

## On-screen keyboard

See [On-screen keyboard](../features/on-screen-keyboard.md#configuration).

## Tablet mode and rotation

See [Tablet and touch](../features/tablet-and-touch.md#configuration).

## Dock configuration

In `Config.qml`: `dockEnabled: true`; `dockPinned`, the default pins as desktop-entry IDs (file names without `.desktop`): Kitty, Zen, Files, VS Code and Steam, with unknown IDs skipped; the AI assistant is never in the dock, as a pin or as a running window (`Dock.hiddenApps`), since its console has its own icon in the bar; `dockIconSize: 44` (logical px); `dockMagnification: 1.4`, the peak scale under the pointer (1 turns it off); `dockTriggerHeight: 3`, the height of the reveal strip (1 px can round away at fractional scales); `dockRevealDelay: 120` ms of hover before it slides up.

The first pin change (menu, drag, launcher) writes `~/.local/state/desktop-shell/dock.json` (`{"pinned": [...]}`, atomic write); from then on it replaces `dockPinned`. Pins of apps that are not installed stay in the file but are not shown. Delete the file to return to `dockPinned`; the shell picks up edits to it live. The layer namespace is `desktop-dock` (blurred like the panels, Hyprglass, no compositor animation); its surface is 190 px tall to draw a pin being dragged off, but input only reaches the reveal strip and the dock body. The context menu uses the `desktop-tray-menu` namespace; keyboard mode maps a transparent full-screen `desktop-dock-keys` surface whose input region excludes the dock, so an outside click ends keyboard mode.

## Control Center configuration

Edit `quickshell/.config/quickshell/desktop/Config.qml`. Configuration is declarative, with no UI editor:

```qml
readonly property var controlCenterModules: ["network", "bluetooth", "brightness", "audio", "media", "switches"]
readonly property int controlCenterWidth: 400
readonly property bool expandMonitors: false
readonly property bool expandAudioDevices: false
readonly property var dnsPresets: [{ name: "Cloudflare", servers: ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"] }, …]
readonly property string primaryMonitor: "eDP-1"
readonly property var brightnessDevices: ({})
```

`dnsPresets` lists the DNS choices in the network details view (Cloudflare, Quad9, Google, and AdGuard by default); each preset gives IPv4 and IPv6 servers. Applying a preset or custom servers sets `ipv4/ipv6.dns` with `ignore-auto-dns` on the saved NetworkManager profile and reapplies it to an active device without disconnecting; **Automatic** restores the router's DNS.

Removing a name disables its module; reordering the list changes the layout. `switches` is the 2×2 grid of Do Not Disturb, Keep awake, Rotation lock and Night shift; the full-width rows `doNotDisturb`, `idle` and `rotation` remain available instead. `rotation` and the Rotation lock tile hide themselves where there is no accelerometer.

Night shift (`services/NightShift.qml`) runs `hyprsunset -t <K>` while it is on and stops it to turn it off (the compositor drops the gamma ramp of a client that goes). A temperature change while on goes through `hyprctl hyprsunset temperature`. `Config.qml` sets `nightShiftTemperature` (4000, until changed in the Control Center), `nightShiftStart` and `nightShiftEnd`; `session.json` keeps `nightShiftMode` and `nightShiftTemperature`. It needs `sudo dnf install hyprsunset` (same COPR as Hyprland); without it the tile says so. Unknown and duplicate names are ignored. Each module has its own file in `controlcenter/`. Network and Bluetooth each occupy half a row; other modules occupy a full row. The panel scrolls when expanded sections exceed the available space. If the primary monitor is disconnected, the first connected display is used.

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

See [Theming](../features/theming.md#wallpapers).

## Application theme

See [Theming](../features/theming.md#application-theme).

## Themes

See [Theming](../features/theming.md#themes).

## Motion

Animations are restrained: quick ease-out entrances, quicker accelerating exits, and no overshoot. Hyprland (`appearance.lua`) defines the curves `out`, `accel`, and `inout` plus a critically damped spring `move`. Windows pop in from 87% with a fade (about 220 ms) and pop out to 92% (about 150 ms); tiling reflow, dragging, and resizing use the spring; workspaces slide with a fade over 18% of the width (special workspace vertically); focus, dim, shadow, border, layer, and popup fades take 140–250 ms. `speed` is in deciseconds. A layer rule in `rules.lua` turns compositor animations off for `desktop-overlay`, `desktop-osd`, `desktop-dock`, `desktop-notifications` and `desktop-osk`, which Quickshell animates itself (the keyboard is not animated, and its re-map over a panel must not fade).

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
