# Hyprland + Quickshell

Custom desktop for Fedora 44, with Hyprland Lua, a Quickshell interface, and GNU Stow packages. The repository manages the bar, launcher, Control Center, notifications, calendar, clipboard, screenshots, recording, lock screen, and wallpapers.

NetworkManager, BlueZ, PipeWire/WirePlumber, UPower, and Polkit provide the backends. All panels use Quickshell, without external applets.

## Getting started

- [Installation, packages, and updates](.claude/docs/installation.md)
- [Hyprland plugins: overview, touch gestures, glass, and screenshots](.claude/docs/plugins.md)
- [Interface and shortcuts](.claude/docs/interface.md)
- [Configuration, language, theme, brightness, and wallpapers](.claude/docs/configuration.md)
- [Lock screen, fingerprints, XWayland, Steam/gamescope, screen sharing, and iPhone](.claude/docs/integrations.md)
- [Troubleshooting and verification status](.claude/docs/troubleshooting.md)
- [Roadmap](.claude/ROADMAP.md)
- [Contributor and agent guidance](.claude/CLAUDE.md)

## Updating the configuration

After installing the dependencies listed in the guide:

```sh
cd ~/.dotfiles
./scripts/stow.py dry-run
./scripts/stow.py apply
./scripts/check.sh
hyprctl reload
desktop-session start
desktop-shell restart
```

Do not run Stow with sudo. `apply` backs up conflicting files before linking them to the repository. Run `apply` again after adding files.

The top-left corner toggles Hyprspace; the bar releases its reserved space and input during the overview. HyprCapture follows the pointer across monitors: `Super + Shift + S` or `Print` opens area capture with the editor; `Super + Shift + Alt + S` or `Alt + Print` captures the monitor with the editor. Hints shows the active session's bindings, grouping screenshots and recordings under “Screen capture”.

The shell supports Italian and US English, selected from `/etc/locale.conf`; text, calendar, and clock follow the system language. Nested JSON catalogs with semantic keys such as `clipboard.deleteItem` live in [`desktop/i18n/`](quickshell/.config/quickshell/desktop/i18n); see [Interface language](.claude/docs/configuration.md#interface-language). Documentation, code, comments, and default labels are in English; Italian text belongs only in `i18n/it_IT.json`.

Kitty includes a complete reference with commented defaults; Fastfetch uses a Fedora layout with a neutral palette.

Main settings are in [`Config.qml`](quickshell/.config/quickshell/desktop/Config.qml), the palette in [`Theme.qml`](quickshell/.config/quickshell/desktop/Theme.qml), and machine overrides in [`local.lua`](hypr/.config/hypr/config/local.lua).

Quickshell is organized by function (`bar`, `controlcenter`, `panels`, `notifications`, `session`, `osd`), with shared components and services. The [directory layout](.claude/docs/configuration.md#quickshell-layout) explains where to make changes. The local Files/Nautilus launcher prefers Wayland; see [XWayland and text clarity](.claude/docs/integrations.md#xwayland).

Removable drives are automounted by udiskie without an external tray icon; notifications appear in Quickshell. iPhones use GVfs/AFC in Files after device trust is granted. See [removable drives and iPhone](.claude/docs/integrations.md#removable-drives-and-iphone).

Steam uses a monitor-aware launcher with 1:1 XWayland rendering for clearer HiDPI text. Gamescope is available per game through `desktop-gamescope -- %command%`; see [Steam and gamescope](.claude/docs/integrations.md#steam-and-gamescope) for setup and scaling options.
