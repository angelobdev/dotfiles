# Dotfiles: Hyprland + Quickshell desktop (Fedora 44)

Personal desktop managed as GNU Stow packages: Hyprland configured in Lua, a Quickshell (QML) shell that provides every panel, small Bash wrappers and Python helpers. The repository is the source of truth; `$HOME` only holds symlinks to it.

## Hard rules

- **Behavior is the contract.** Refactors must not change what the user sees or does unless explicitly asked. Separate "cleanup" from "behavior change" in plans, commits and reports.
- **The live session runs from this repo.** Hyprland and Quickshell hot-reload symlinked files on save. A broken edit breaks the running desktop immediately; see [workflow](../docs/development/workflow.md#live-reload).
- **English everywhere** (code, comments, docs, default labels). Italian text lives only in `quickshell/.config/quickshell/desktop/i18n/it_IT.json`.
- **Every user-visible string goes through i18n**: `I18n.tr()` / `I18n.plural()` in QML, `tr()` in Python helpers, with the key added to *both* catalogs.
- **Never run Stow with sudo**, never `git add -A` blindly (state and backups live outside the repo but check `git status`), never edit `scripts/hyprpm/` casually (it changes the plugin bundle digest and forces a rebuild).
- Commit only when asked; message style is `type: summary` (`chore:`, `fix:`, …).

## Map

| Path | What |
| --- | --- |
| `hypr/` | `hyprland.lua` + `config/*.lua` modules (`local.lua` = machine overrides, loaded last), `xdph.conf` |
| `quickshell/.config/quickshell/desktop/` | Shell: `shell.qml` (entry), `share.qml` (screen-share picker), singletons `Config`/`Theme`/`ShellState`/`I18n`, `services/`, `bar/`, `panels/`, `controlcenter/`, `components/`, `notifications/`, `session/`, `osd/`, `i18n/` |
| `shell/.local/bin/desktop-*` | Bash entry points (session, shell IPC, power, theme, wallpaper, steam, gamescope, …) |
| `shell/.config/systemd/user/` | User units started by `desktop-session` (`desktop-updates.timer`) |
| `shell/.local/libexec/desktop/*.py` | Python helpers spawned by QML services and wrappers; `i18n.py` shares the QML catalogs |
| `hypridle/ hyprlock/ hyprpaper/ gtk/ kitty/ fastfetch/ portals/ udiskie/ electron/` | Plain config packages |
| `docs/` | User guides (`guide/`), one page per area (`features/`), developer docs (`development/`) |
| `scripts/` | `install-desktop.py` with `install/manifest.toml` (the only package list) and `install/fedora.py`, `stow.py` (explicit package list), `check.sh`, `check-i18n.py`, `check-links.py`, hyprpm plugin packaging |
| `.github/workflows/` | CI: `check.yml` runs `check.sh` on Fedora 44 and 45 on pushes to `main` and pull requests; `install.yml` runs the installer in a fresh Fedora 45 when it changes |

## Commands

```sh
./scripts/check.sh              # bash -n, Python compile, i18n tests, doc links, cc, desktop-file-validate, qmllint, Hyprland --verify-config
./scripts/stow.py dry-run       # then: ./scripts/stow.py apply (needed after ADDING files)
./scripts/install-desktop.py    # preview of a full install on a fresh system; refuses this Fedora 44 laptop
hyprctl configerrors            # live Hyprland config state
qs log -p ~/.config/quickshell/desktop | tail   # live shell reload result
~/.local/bin/desktop-shell status               # JSON snapshot of every service
```

## Development docs

- [Architecture](../docs/development/architecture.md): how session startup, IPC, services, helpers and panels connect.
- [Conventions](../docs/development/conventions.md): style rules per language, i18n and theme usage.
- [Workflow](../docs/development/workflow.md): making changes safely, sync points, verification.
- [Roadmap](../docs/development/roadmap.md): current direction, completed work, open items and review follow-ups.

## User documentation

The index is [docs/README.md](../docs/README.md); each area of the desktop has its page in `docs/features/`.

[Installation](../docs/guide/installation.md) · [Plugins](../docs/guide/plugins.md) · [Interface & shortcuts](../docs/guide/interface.md) · [Configuration](../docs/guide/configuration.md) · [Integrations](../docs/guide/integrations.md) · [Troubleshooting](../docs/guide/troubleshooting.md)

Keep these guides accurate when behavior changes; record verification results in `docs/development/verification-log.md` and progress in `docs/development/roadmap.md`.
