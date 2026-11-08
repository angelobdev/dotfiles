# Workflow

[← Docs](../README.md)

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
| New panel | `ShellState.qml` allow-list, `desktop-shell` usage/allow-list, an `Overlay` instance in `shell.qml`, a bind in `binds.lua`, `docs/guide/interface.md` |
| New layer namespace | Hyprglass/blur rules in `config/plugins.lua` and `config/rules.lua` |
| New/renamed bind description | `i18n/Sources.js` mapping + both catalogs (Hints translation) |
| New user-visible string | Both `en_US.json` and `it_IT.json`, same path and placeholders |
| New helper or argv/stdout change | The QML service that parses it (byte-exact contract) |
| New Stow package | `PACKAGES` in `scripts/stow.py`, package table in `docs/guide/installation.md` |
| `build.py`, `hyprpm.toml` or the patch in `scripts/hyprpm/` | Changes the bundle digest: the plugins are rebuilt at the next login, in the background behind one prompt (Settings → System → Plugins shows it); new files of the build also go in `FILES` in `bundle.py`. `bundle.py` itself (the accepted builds) is outside the digest |
| Moved docs | Links in `README.md`, `docs/**`, `.claude/CLAUDE.md` (`scripts/check-links.py` finds the broken ones), and the doc paths quoted in the `assistant.errors.claudeMissing`, `capture.errors.pluginMissing` and `plugins.errors.rebuildRequired` catalog strings |
| Tool needed by `check.sh` | The package list in `.github/workflows/check.yml`, and its list of required tools when `check.sh` skips that tool if missing |
| New runtime dependency | `scripts/install/manifest.toml`, the only list of packages; `[verify]` too if the desktop cannot start without it |
| New Fedora release | `versions` in the manifest, the accepted builds in `scripts/hyprpm/bundle.py`, the matrix in `check.yml`, the image in `install.yml` |
| New runtime dependency on Arch | The `[arch]` table of the manifest, with the name checked with `pacman -Si` (`pacman -F` finds the package of a file); `scripts/tests/install-container-arch.sh` installs it for real |
| Newer AUR package | `./scripts/install-desktop.py pins`, review the PKGBUILD changes it links, then `pins --update` |
| Hyprland update on Arch | Its `pacman -Q hyprland` build in `VERIFIED` of `scripts/hyprpm/bundle.py`, once the plugins are checked against it |

## Verification

1. `./scripts/check.sh` must pass (it is fast). GitHub runs it too, in a `fedora:45` and an `archlinux` container, on every push to `main` and every pull request (`.github/workflows/check.yml`). The doc check needs `python3-cmarkgfm` and is skipped without it, so install it to catch broken links before pushing.
   The installer has its own proof: `scripts/tests/install-container.sh` runs it for real in a fresh `fedora:45` container, and `install-container-arch.sh` in a fresh `archlinux` one (`PROFILES=core,apps` builds the AUR packages, `gaming` enables multilib), as their headers show, and `.github/workflows/install.yml` runs both when the installer changes. Set `COMPILE=1` to build the plugins too. A container has no systemd, so the login, firewall and Flatpak steps need a VM, and a VM cannot show everything: with virgl kitty does not start and layers lose their transparency, and with software rendering hyprpaper crashes ([verification log](verification-log.md#installer-in-a-vm-with-fedora-45-server-2026-10-31)).
2. For QML: confirm the live reload succeeded and inspect `desktop-shell status`. Prefer isolated instances (`qs -p <dir>` with mock data, nested/headless Hyprland, private D-Bus buses) for anything that would touch the user's real devices, accounts, notifications or open applications.
3. Behavior or visual changes: describe what was verified physically versus in isolation, and record it in `docs/development/verification-log.md`.
4. Never leave test state behind (temporary preloads, debug ports, test symlinks, fake devices).

## Reporting

Keep cleanups and behavior changes apart. When a fix would change behavior (even a bug fix), propose it with evidence and let the owner decide; add accepted-but-pending items to `docs/development/roadmap.md`.
