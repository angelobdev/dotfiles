# Troubleshooting

[← Docs](../README.md)

## Diagnostics

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

## Common problems

**A login comes up without plugins after a Hyprland update.** No gestures, overview or glass, and a notification asks for a rebuild. This is on purpose: plugins are built for one exact Hyprland. Reset the cache and rebuild, from a terminal in that session:

```sh
sudo rm -rf /var/cache/hyprpm/$USER
./scripts/install-hypr-plugins.py
```

`scripts/hyprpm/build.py` accepts only the Hyprland builds it lists, so a new version needs new pins first: see [Hyprland plugins](plugins.md#verification-and-updates). The installer warns about this before you reboot.

**The installer stops on a full disk.** Fedora Server's guided partitioning gives `/` only 15 GiB on LVM. Grow it with the command the installer printed, `sudo lvextend -r -l +100%FREE /dev/mapper/<root volume>`, then run `./scripts/install-desktop.py apply` again: it picks up where it stopped.

**The desktop comes back bare after a crash.** `start-hyprland` restarts Hyprland with `--safe-mode`: no user config, no plugins, no shell. Save anything open and log in again. Reports are in `~/.cache/hyprland/` and `coredumpctl list`.

**Do not swap a plugin inside a running session.** `hyprctl plugin unload` and `load` crashed the compositor here. To try a build, replace its file with `install`, which leaves the running copy alone, and log in again; [the verification log](../development/verification-log.md#tablet-follow-ups-2026-10-30) has the details.

**A QML edit does not show up.** Look for "Reloading configuration" in `qs log -p ~/.config/quickshell/desktop`. If it is missing, make an in-place change to `shell.qml`, as [Conventions](../development/conventions.md) describes.

**The keyboard offers no suggestions.** The word lists download on first use: run `~/.local/libexec/desktop/predict.py fetch`. Suggestions stay away from terminals, passwords and URLs by design.

## References

[Hyprland Lua](https://wiki.hypr.land/Configuring/Start/), [Quickshell](https://quickshell.org/docs/v0.3.0/types/), [PopupAnchor](https://quickshell.org/docs/v0.3.0/types/Quickshell/PopupAnchor/), [IdleInhibitor](https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/IdleInhibitor/), [Hyprshot](https://github.com/Gustash/Hyprshot), [DDC/CI brightness](https://www.ddcutil.com/command_getvcp/), [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/), [hyprlock](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/), [hyprpaper](https://wiki.hypr.land/Hypr-Ecosystem/hyprpaper/), [Hyprland portal](https://wiki.hypr.land/Hypr-Ecosystem/xdg-desktop-portal-hyprland/), [Electron Wayland](https://www.electronjs.org/blog/tech-talk-wayland), [cliphist](https://github.com/sentriz/cliphist), [wf-recorder](https://github.com/ammen99/wf-recorder), [Kitty](https://sw.kovidgoyal.net/kitty/conf/).
