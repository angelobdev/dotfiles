# Session and integrations

[← README](../README.md)

## Lock, idle, and suspend

`Super + L` and the power panel run `desktop-power lock`, which starts hyprlock with mandatory authentication (`--grace 0`) and serializes requests. PAM uses `/etc/pam.d/hyprlock` from the Fedora package.

| Idle time | Action |
| --- | --- |
| 5 minutes | Lock session |
| 10 minutes | Turn off displays (DPMS) |
| 30 minutes | Suspend |

Customize `hypridle/.config/hypr/hypridle.conf`. The daemon respects application inhibitors. The toggle requires no additional packages: `IdleInhibitor` is included in Quickshell and uses Hyprland's supported protocol; hypridle respects Wayland inhibitors by default (`ignore_wayland_inhibit = false`). **Keep awake** in the Control Center inhibits automatic locking, DPMS, and suspend through a Wayland inhibitor on the bars; it continues working when the panel closes. Manual actions remain available. The toggle starts disabled and resets on shell restart; its configurable module is `idle`. `inhibit_sleep = 3` makes logind wait for the Wayland session-locked signal before sleeping, including with the custom wrapper. `before_sleep_cmd` covers external requests and lid closure when logind maps it to suspend. Displays turn back on after resume. `desktop-power suspend` refuses to proceed if hypridle is not running.

Hyprlock uses **native, parallel** fingerprint authentication through fprintd while retaining PAM/password. System PAM files are not modified. The layout places clock/date at the top and user, password, fingerprint status, and keyboard layout at the bottom, with the shell's graphite palette. This machine already has the Synaptics reader and right index finger enrolled; for another user, use `fprintd-list "$USER"` and, if needed, `fprintd-enroll`. Password authentication remains available without a reader.

The hyprlock configuration was tested in a nested Hyprland session: PAM initialization, rendering, and `onLockLocked` confirmation succeeded; the newer headless test also confirms reader acquisition and right-index verification startup. Successful biometric authentication requires a physical finger test. Password unlock, lid closure, and resume still need testing on the machine; the nested test does not exercise these hardware paths.

## XWayland

`hypr/.config/hypr/config/xwayland.lua` explicitly enables Fedora's XWayland server. `force_zero_scaling = false` retains compositor scaling on HiDPI screens. Qt uses `wayland;xcb` and GTK `wayland,x11,*`, with `DISPLAY` imported into the D-Bus/systemd environment at login. Native applications use Wayland; X11 applications use the bridge without a separate X desktop.

The machine was checked with XWayland active and `xprop -root`. To change X11 application scaling policy, use `hypr/.config/hypr/config/local.lua`; forcing zero scaling may make applications without their own HiDPI support very small.

### Blurred text on fractional-scale displays

The reported ChatGPT and Nautilus windows were both XWayland on the eDP monitor at scale 1.667. Nautilus had `GDK_BACKEND=x11`; ChatGPT had started without Wayland display variables. Scaling X11 surfaces can blur text ([Hyprland documentation](https://wiki.hypr.land/0.54.0/Configuring/XWayland/)). Isolated instances of both applications were verified as native Wayland without changing CSS, fonts, or monitor scale.

The `shell` Stow package includes `~/.local/share/applications/chatgpt.desktop` with `--ozone-platform=wayland` and `org.gnome.Nautilus.desktop` with `GDK_BACKEND=wayland`. Nautilus launcher D-Bus activation is disabled so the command environment applies; the application still retains its single-instance behavior. `desktop-session start` also updates `GDK_BACKEND` and `QT_QPA_PLATFORM` in the service environment. These overrides require a Wayland session.

**Completely close and reopen applications** to apply the backend: opening a new window from an existing X11 process is insufficient. User instances were not terminated during verification. Check the `xwayland` field in `hyprctl -j clients`: `false` indicates a native window. `force_zero_scaling` stays disabled to retain other X11 applications' sizes. Inactive window opacity remains 0.92 and can reduce contrast even with native rendering.

## Electron, portals, and screen sharing

Modern applications choose Wayland through `XDG_SESSION_TYPE=wayland`. The session also sets `XDG_CURRENT_DESKTOP=Hyprland` and imports display variables into D-Bus/systemd. For Electron applications requiring an explicit choice:

```sh
desktop-electron code                  # --ozone-platform=wayland
desktop-electron --x11 code            # XWayland fallback
```

Close application instances first: an existing process may receive the new-window request while retaining its backend. The wrapper does not modify application launchers or add obsolete Electron variables. The repository separately supplies the desktop overrides described above. VS Code was tested with temporary profiles on both backends; existing VS Code and Zen windows were native Wayland. Electron applications with old or custom Chromium versions may have their own limitations.

`portals/.config/xdg-desktop-portal/hyprland-portals.conf` selects Hyprland for ScreenCast, Screenshot, GlobalShortcuts, and InputCapture, with GTK for FileChooser, Settings, and fallback. PipeWire carries video. `desktop-session start` also imports `~/.local/bin` into the service PATH and starts portals **after** importing the environment; it does not automatically restart them during active sharing.

Sharing requests open the **Quickshell** picker (`share.qml`), with displays, windows, search, and keyboard navigation. Select a source and Share; Esc/Cancel denies the request. Window IDs come from the portal rather than Hyprland addresses. `hypr/.config/hypr/xdph.conf` configures `desktop-portal-picker`, a maximum of 60 fps, and nonpersistent consent by default. The GTK fallback is a system backend with no persistent applet.

After installation or backend changes, stop sharing, run `desktop-session start`, then `systemctl --user restart xdg-desktop-portal-hyprland xdg-desktop-portal-gtk xdg-desktop-portal`. Restart open browsers/applications if needed. For diagnostics:

```sh
systemctl --user status xdg-desktop-portal-hyprland xdg-desktop-portal
journalctl --user -b -u xdg-desktop-portal-hyprland -u xdg-desktop-portal
```

The isolated test completed CreateSession/SelectSources/Start and received five real PipeWire frames from a test window through the QML picker. End-to-end testing in the specific calling web app in Zen remains manual: start sharing, verify the display/window, and stop sharing from the application.
