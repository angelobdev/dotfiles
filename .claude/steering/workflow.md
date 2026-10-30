# Workflow

[← CLAUDE.md](../CLAUDE.md)

## Live reload

The running desktop reads files through symlinks into this repository:

- **Hyprland** reloads Lua on save. Run `XDG_CONFIG_HOME="$PWD/hypr/.config" Hyprland --verify-config -c hypr/.config/hypr/hyprland.lua` before relying on an edit, and `hyprctl configerrors` after.
- **Quickshell** reloads QML on save and keeps the previous instance if the new one fails. A multi-file change can briefly fail mid-write; confirm the final state with `qs log -p ~/.config/quickshell/desktop | tail` ("Configuration Loaded") and `desktop-shell status`.
- Singletons and catalogs are watched too; restart with `desktop-shell restart` when state looks stale.
- hypridle, hyprpaper and udiskie do not reload: restart the daemon after editing its file.

**Adding a file** (a new Lua module, QML component or helper) does nothing until `./scripts/stow.py apply` links it. Do not make an existing, already-linked file depend on a new file until it is stowed, or the live reload breaks. New QML files in a directory imported by path are picked up after stowing; singletons also need a `qmldir` line.

## Sync points (change together)

| Change | Also update |
| --- | --- |
| New panel | `ShellState.qml` allow-list, `desktop-shell` usage/allow-list, an `Overlay` instance in `shell.qml`, a bind in `binds.lua`, `docs/interface.md` |
| New layer namespace | Hyprglass/blur rules in `config/plugins.lua` and `config/rules.lua` |
| New/renamed bind description | `i18n/Sources.js` mapping + both catalogs (Hints translation) |
| New user-visible string | Both `en_US.json` and `it_IT.json`, same path and placeholders |
| New helper or argv/stdout change | The QML service that parses it (byte-exact contract) |
| New Stow package | `PACKAGES` in `scripts/stow.py`, package table in `docs/installation.md` |
| Anything in `scripts/hyprpm/` | Changes the bundle digest: requires `hyprpm remove dotfiles-desktop` and a reinstall; new files also go in `BUNDLE` in `install-hypr-plugins.py` |
| Moved docs | Links in `README.md`, `.claude/**`, and the doc paths quoted in the `capture.errors.pluginMissing` / `plugins.errors.rebuildRequired` catalog strings |

## Verification

1. `./scripts/check.sh` must pass (it is fast).
2. For QML: confirm the live reload succeeded and inspect `desktop-shell status`. Prefer isolated instances (`qs -p <dir>` with mock data, nested/headless Hyprland, private D-Bus buses) for anything that would touch the user's real devices, accounts, notifications or open applications.
3. Behavior or visual changes: describe what was verified physically versus in isolation, and record it in `docs/troubleshooting.md`.
4. Never leave test state behind (temporary preloads, debug ports, test symlinks, fake devices).

## Reporting

Keep cleanups and behavior changes apart. When a fix would change behavior (even a bug fix), propose it with evidence and let the owner decide; add accepted-but-pending items to `ROADMAP.md`.
