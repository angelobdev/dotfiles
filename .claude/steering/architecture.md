# Architecture

[← CLAUDE.md](../CLAUDE.md)

## Session startup

1. Hyprland loads `hypr/.config/hypr/hyprland.lua`, which sets `package.path` from `$XDG_CONFIG_HOME/hypr` (fallback `~/.config/hypr`) and `require`s modules in a fixed order: `monitors`, `appearance`, `input`, `plugins`, `binds`, `rules`, `xwayland`, `session`, then `local`. `hl.config` merges per key, so one option section can be split across modules; later monitor rules and values override earlier ones.
2. `config/session.lua` registers a `hyprland.start` callback that runs `desktop-plugins reload`, imports environment into D-Bus/systemd, then `desktop-session start` and `desktop-shell start`.
3. `desktop-session start` (flock-serialized) refreshes the activation environment, applies `desktop-theme`, starts portals and the GVfs AFC monitor, ensures the wallpaper link, and starts one each of `hyprpaper`, `hypridle`, `udiskie` (logs in `~/.local/state/desktop-session/`).
4. `desktop-shell start` runs `qs -p ~/.config/quickshell/desktop --no-duplicate --daemonize`.

Hyprland's `exec` PATH does not include `~/.local/bin`, so Lua always calls wrappers by absolute, quoted path (`'"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'`).

## Keybinding → panel flow

```
binds.lua  bind("SUPER + SHIFT + C", exec(desktop-shell toggle controls), "Control Center")
   └─ desktop-shell toggle NAME     (validates NAME against its allow-list)
        └─ qs ipc call desktop toggle NAME
             └─ shell.qml IpcHandler "desktop" → ShellState.toggle(NAME, screen)
                  └─ ShellState.panel = NAME   (one panel at a time; activeScreen = focused monitor)
                       └─ Overlay { panelName: NAME } becomes visible, focuses, emits opened()
```

The IPC target also exposes `media(action)` (MPRIS through `services/Media.qml`), `dock(action)` and `dockLaunch(index)` (`desktop-shell dock …`, through `services/Dock.qml`), `close()` and `status()` (a JSON debug snapshot used for verification).

## Quickshell structure

- `shell.qml`: `ShellRoot` with one `Bar` and one `DockWindow` per screen (`Variants`) and exactly one instance of every panel, the OSD, notification popups/center and session prompts. It references some services through `property var` so they load eagerly (`Notices` owns the notification D-Bus name).
- `share.qml`: a separate root launched by `portal_picker.py` for XDPH screen sharing; input through `DESKTOP_SHARE_*` environment variables, answer written to a file, then `Qt.quit()`.
- Singletons: root `qmldir` (Theme, ShellState, Config, I18n) and `services/qmldir` (Audio, Notices, Brightness, Idle, Osd, Clipboard, Recording, Media, BluetoothAgent, Calendar, BarVisibility, NetworkInfo, Apps, Dock). Each file has `pragma Singleton` *and* a qmldir line.
- `Config.qml` is constant (`readonly` properties); editing it hot-reloads the whole shell.
- Panels are `components/Overlay.qml` (full-screen layer-shell window, namespace `desktop-overlay`, exclusive keyboard focus, Esc/backdrop click close) containing a centred `Card` (dialog-style) or a `SidePanelCard` (top-right side panels with `PanelHeader`).
- The dock is not a panel: `dock/DockWindow.qml` is a bottom `PanelWindow` (namespace `desktop-dock`, no exclusive zone, no keyboard focus) that stays mapped and switches its input `mask` between a reveal strip and the dock body; `services/Dock.qml` builds the items (pins from `~/.local/state/desktop-shell/dock.json` through `FileView` + `JsonAdapter`, falling back to `Config.dockPinned`; then `Hyprland.toplevels` grouped by `DesktopEntries.heuristicLookup`) and holds per-monitor requests, peeks, the open menu and keyboard mode. `dock/DockMenu.qml` is the context menu (a full-screen Overlay layer like tray menus, built on the shared `components/PopupMenu.qml`, which the launcher pin menu also uses); `dock/DockKeyboard.qml` holds the keyboard after `Super + D`: a full-screen Overlay layer mapped only in keyboard mode, with exclusive focus and an input region that excludes the dock body, so an outside click ends keyboard mode and clicks on the dock still reach it (the dock window itself never takes focus: Qt replayed a stale hover on activation). Layout maths (resting offsets, magnification, drop slot, drag shifts) lives in `dock/DockModel.js` and is tested by `scripts/tests/tst_dock_model.qml` (qmltestrunner, run by `check.sh`). `services/Apps.qml` launches desktop entries for both the launcher and the dock.
- Control Center modules are files in `controlcenter/` selected by name from `Config.controlCenterModules` through the `moduleSources` table in `Controls.qml`.

## Services ↔ Python helpers

Services spawn `python3 ~/.local/libexec/desktop/<helper>.py …` through Quickshell `Process`, with the path in a `readonly property string helper`.

| Pattern | Helpers | Protocol |
| --- | --- | --- |
| Long-lived watcher | `bar_visibility.py`, `brightness.py watch`, `clipboard.py watch-*`, `recording.py` | One compact JSON document per line on stdout (`flush=True`), parsed by `SplitParser` |
| Two-way agent | `bluetooth_agent.py` | JSON lines on stdin (`pair`/`cancel`/`reply`) and stdout (`status`/`prompt`/`error`/`operation`) |
| One-shot | `calendar.py`, `brightness.py read/set`, `clipboard.py list/…`, `wallpaper.py`, `xwayland.py` (apply/status, `aseprite` launcher), `network.py` (details, profile, set, set-dns, set-ipv4, set-mac, add-hidden with the password on stdin, vpn/vpn-up/vpn-down, hotspot/hotspot-on/hotspot-off, tailscale/tailscale-up/tailscale-down, extras (one poll for VPN, hotspot and Tailscale), secret, copy-secret, qr) | One JSON document collected by `StdioCollector`; errors as `{"error": …}` or translated stderr |

Crashed watchers restart through a `Timer` whose `running` is `<enabled> && !process.running`. Treat argv and stdout formats as a byte-exact contract between QML and Python.

## Compositor plugins

Hyprspace, Hyprgrass, Hyprglass, hypr-hot-edge and HyprCapture are built by hyprpm from the pinned packaging in `scripts/hyprpm/`. `config/plugins.lua` guards every block (`local plugins = hl.plugin or {}`; `if plugins.X then … end`) so `--verify-config` and plugin-less startup work. Actions that need a plugin (screenshots) check `hl.plugin` at press time because plugins load after `hyprland.start`. `desktop-plugins reload` refuses to autoload after a compositor update until the build is re-verified.

Bar hiding during Hyprspace: `bar_visibility.py` polls `desktop-bar` layer alpha over Hyprland IPC; `BarVisibility.hidden(screen)` drops the bar's exclusive zone and input mask while keeping the surface mapped (it carries the idle inhibitor).

## Stow packages

`scripts/stow.py` stows an explicit `PACKAGES` tuple with `--no-folding`: directories in `$HOME` are real, files are symlinks. A new file therefore does not exist in `$HOME` until `stow.py apply` runs. `.claude/`, `scripts/` and top-level files are never stowed.
