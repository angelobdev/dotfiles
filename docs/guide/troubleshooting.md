# Troubleshooting

[← Docs](../README.md)

## Diagnostics

Your own Hyprland settings go in `~/.config/desktop/hypr.lua` and shell options in `~/.config/desktop/shell.json` ([configuration](configuration.md#your-own-settings)); a supported model's settings are in `hypr/.config/hypr/config/machines/`. The QML palette is in `Theme.qml`, icons in `assets/icons`, and GTK CSS/Qt colors in their respective packages. Quickshell and Hyprland reload their configurations; restart hypridle/hyprpaper after changing their files. Autostart runs at login; `desktop-session start` and `desktop-shell start` avoid duplicate processes. `desktop-shell restart` waits for the previous instance to exit before starting another.
```sh
~/.local/bin/desktop-shell status
~/.local/bin/desktop-session status
qs log -c desktop
hyprctl configerrors
hyprctl getoption xwayland:enabled
xprop -root _NET_SUPPORTING_WM_CHECK
readlink -f ~/.local/state/desktop-session/wallpaper/current.jpg
journalctl --user -b -u hypridle -u hyprpaper -u desktop-udiskie
journalctl --user -b -t desktop-shell   # the shell's supervisor and the lock
./scripts/check.sh
```

## Common problems

**A login comes up without plugins after a Hyprland update.** No gestures, overview or glass. This is on purpose: plugins are built for one exact Hyprland. For a [verified build](plugins.md#verification-and-updates) the shell rebuilds them in the background right after login, behind one password or fingerprint prompt; the result is a notification, and the log is in Settings → System → Plugins. If it stopped (offline, prompt dismissed), **Rebuild** in that tab or the next login tries again. A notification instead means the build is not verified yet (`scripts/hyprpm/bundle.py` accepts only the builds it lists, so a new version needs new pins first), or that `hyprland` and `hyprland-devel` came from different updates: finish it with `sudo dnf upgrade` and log in again.

**The installer stops on a full disk.** Fedora Server's guided partitioning gives `/` only 15 GiB on LVM. Grow it with the command the installer printed, `sudo lvextend -r -l +100%FREE /dev/mapper/<root volume>`, then run `./scripts/install-desktop.py apply` (or `./scripts/install-tui.py`) again: it picks up where it stopped.

**The desktop comes back bare after a crash.** `start-hyprland` restarts Hyprland with `--safe-mode`: no user config, no plugins, no shell. Save anything open and log in again. Reports are in `~/.cache/hyprland/` and `coredumpctl list`.

**The bar disappears for a moment.** The shell stopped and its supervisor (`desktop-shell supervise`) started it again within a few seconds. Quickshell's own crash handler is off (`QS_DISABLE_CRASH_HANDLER`): it relaunched the shell by itself, racing the supervisor and `desktop-shell restart` for the polkit agent and the notification server, and opened a report window. `coredumpctl list quickshell` keeps the crashes, `journalctl --user -b -t desktop-shell` the restarts.

**Do not swap a plugin inside a running session.** `hyprctl plugin unload` and `load` crashed the compositor here. To try a build, replace its file with `install`, which leaves the running copy alone, and log in again; [the verification log](../development/verification-log.md#tablet-follow-ups-2026-10-30) has the details.

**A QML edit does not show up.** Look for "Reloading configuration" in `qs log -p ~/.config/quickshell/desktop`. If it is missing, make an in-place change to `shell.qml`, as [Conventions](../development/conventions.md) describes.

**Volume does nothing with Bluetooth headphones.** PipeWire uses the headset's own volume (AVRCP absolute volume), and a connection that went wrong can leave it unsynced: the level changes in the shell, not in the ears. Check with `busctl get-property org.bluez <transport> org.bluez.MediaTransport1 Volume` (the transport is the `.../sepN/fdN` path in `busctl tree org.bluez`): it should move with the slider. If it does not, `systemctl --user restart wireplumber` recreates the transport. Seen once when headset and laptop connected at the same time (`bluetoothd`: "Operation already in progress"). If a headset never syncs, `bluez5.hw-volume = [ hfp_ag hsp_ag ]` in a `monitor.bluez.rules` entry for its `device.name` makes PipeWire scale the stream instead.

**GTK 3 dialogs are light with a dark theme.** The theme asks for `adw-gtk3-dark`; without `adw-gtk3-theme` installed GTK 3 falls back to light Adwaita. Install it (`sudo dnf install adw-gtk3-theme`) and run `systemctl --user restart xdg-desktop-portal-gtk`.

**The keyboard offers no suggestions.** The word lists download on first use: run `~/.local/libexec/desktop/predict.py fetch`. Suggestions stay away from terminals, passwords and URLs by design.

## Reporting a problem

If none of the above helps, [open an issue](https://github.com/angelobdev/dotfiles/issues/new/choose): there are forms for bug reports, feature requests and enhancements. For a bug, the output of the [diagnostics](#diagnostics) above helps most; read it first and leave out anything personal. `desktop-shell status` in particular includes your calendar, notifications and clipboard.

## References

[Hyprland Lua](https://wiki.hypr.land/Configuring/Start/), [Quickshell](https://quickshell.org/docs/v0.3.0/types/), [PopupAnchor](https://quickshell.org/docs/v0.3.0/types/Quickshell/PopupAnchor/), [IdleInhibitor](https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/IdleInhibitor/), [Hyprshot](https://github.com/Gustash/Hyprshot), [DDC/CI brightness](https://www.ddcutil.com/command_getvcp/), [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/), [hyprlock](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/), [hyprpaper](https://wiki.hypr.land/Hypr-Ecosystem/hyprpaper/), [Hyprland portal](https://wiki.hypr.land/Hypr-Ecosystem/xdg-desktop-portal-hyprland/), [Electron Wayland](https://www.electronjs.org/blog/tech-talk-wayland), [cliphist](https://github.com/sentriz/cliphist), [wf-recorder](https://github.com/ammen99/wf-recorder), [Kitty](https://sw.kovidgoyal.net/kitty/conf/).
