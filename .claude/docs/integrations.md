# Session and integrations

[← README](../../README.md)

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

`hypr/.config/hypr/config/xwayland.lua` explicitly enables Fedora's XWayland server. `force_zero_scaling = true` renders X11 surfaces at 1:1 to avoid compositor upscaling blur on HiDPI screens. Qt uses `wayland;xcb` and GTK `wayland,x11,*`, with `DISPLAY` imported into the D-Bus/systemd environment at login. Native applications use Wayland; X11 applications use the bridge without a separate X desktop.

X11 applications therefore draw in physical pixels and must scale themselves. `desktop-xwayland apply` (run by `desktop-session start` and again whenever a monitor is added or removed) sets X resources from the focused monitor's scale: `Xft.dpi` = 96 × scale (160 at 1.667), `Xcursor.theme` = the GNOME cursor theme (`default` is resolved to the theme it inherits, Adwaita, because X clients otherwise fell back to the server's blocky arrow), and `Xcursor.size` = 24 × scale (40). Qt, GTK, and Chromium/Electron clients on X11 then match Wayland windows in text and widget size, and the pointer looks the same over both. `XCURSOR_SIZE` is no longer exported globally, because it overrides the X resource; Wayland clients keep 24 logical pixels through `HYPRCURSOR_SIZE` and GNOME settings. `desktop-xwayland status` prints the resources and the focused monitor.

X11 has one scale for all windows. With a mixed setup (built-in panel at 1.667, external display at 1), the profile follows the monitor focused when it is applied; run `desktop-xwayland apply` with the other monitor focused and restart the X11 application to switch. Applications already running keep the values they read at startup. Applications that only scale by whole numbers cannot match 1.667 exactly.

### Blurred text on fractional-scale displays

The reported ChatGPT and Nautilus windows were both XWayland on the eDP monitor at scale 1.667. Nautilus had `GDK_BACKEND=x11`; ChatGPT had started without Wayland display variables. Scaling X11 surfaces can blur text ([Hyprland documentation](https://wiki.hypr.land/configuring/extra/xwayland/)). Isolated instances of both applications were verified as native Wayland without changing CSS, fonts, or monitor scale.

The `shell` Stow package includes `~/.local/share/applications/chatgpt.desktop` with `--ozone-platform=wayland` and `org.gnome.Nautilus.desktop` with `GDK_BACKEND=wayland`. Nautilus launcher D-Bus activation is disabled so the command environment applies; the application still retains its single-instance behavior. `desktop-session start` also updates `GDK_BACKEND` and `QT_QPA_PLATFORM` in the service environment. These overrides require a Wayland session.

**Completely close and reopen applications** to apply the backend: opening a new window from an existing X11 process is insufficient. User instances were not terminated during verification. Check the `xwayland` field in `hyprctl -j clients`: `false` indicates a native window. XWayland surfaces now use 1:1 rendering; native Wayland windows retain per-monitor scaling. Inactive window opacity remains 0.92 and can reduce contrast even with native rendering.

### Aseprite

Aseprite (Steam build, X11 only) scales its interface by whole numbers, and under XWayland it draws in physical pixels, so its own 200% looks like about 120% on the 1.667 panel. `desktop-aseprite` sets `screen_scale` in `~/.config/aseprite/aseprite.ini` to 200% × the focused monitor's scale, rounded, before starting it: 3 on the built-in panel (about 1.8 logical pixels per UI pixel), 2 on an unscaled external display. Prefix the launch option with `DESKTOP_ASEPRITE_SCALE=1.5` (or another base) for a different size. The rest of the file is left untouched. Set it once as Aseprite's Steam launch option (Library → Aseprite → Properties → Launch options):

```text
/home/angelo/.local/bin/desktop-aseprite %command%
```

Both the Steam library and the app-menu entry (which goes through Steam) then use it. Without the launch option, `desktop-xwayland apply` (session start, monitor hotplug) also writes the same value whenever `aseprite.ini` exists, so Aseprite follows the X11 profile; Aseprite saves its in-memory value when it quits, so a change made while it runs applies after the next apply or launch. Aseprite does not rescale when its window moves to another monitor; quit and start it on the target monitor. Whole numbers are the only crisp option, so the result is close to, not exactly, the chosen base. Aseprite's own pixel cursor is multiplied by `screen_scale` (huge at 3), so the wrapper also turns on `[cursor] use_native_cursor` when it is not set: the native cursor is the X theme cursor, already sized by `Xcursor.size`, and matches the rest of the desktop. An explicit choice in Aseprite's Preferences is kept.

## AI assistant

`Super + A` runs `desktop-ai`: the first press starts Claude Code (`claude`, installed in `~/.local/bin` by its installer) in a Kitty window of class `desktop-ai`; the `desktop-ai` window rule floats it at 60% × 70% of the monitor, centred, on the special workspace `ai`. When the monitor changes shape (rotation in tablet mode, a new scale) the window takes 60% × 70% of the new size again, centred (`monitor.layout_changed` in `rules.lua`); other floating windows larger than their monitor shrink to 90% of it. Later presses toggle that workspace, so the same session stays alive while hidden; closing the window ends the session and the next press starts a new one. The window opens in `$HOME`. If `claude` is missing, a notification points here.

The session gets `--settings` for this window only, so the global `~/.claude/settings.json` is untouched: voice dictation in hold mode and `language`, which Claude Code uses both for dictation and for its replies. The language comes from the system locale (`assistant.language` in the catalogs: `english`, `italian`); set `DESKTOP_AI_LANGUAGE` (e.g. `hl.env("DESKTOP_AI_LANGUAGE", "italian")` in `local.lua`, then close the assistant window) for another one.

Hold `Space` in the prompt to record, release to insert the transcript, `Esc` to cancel; a single tap still types a space. Hold detection relies on keyboard repeat, so recording starts after Hyprland's repeat delay. Transcription runs on Anthropic's servers and needs Claude Code signed in with a claude.ai account: `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or an `apiKeyHelper` take precedence and disable it (`/voice` then reports an unknown command; run `/login`). Recording uses Claude Code's native module and falls back to `arecord` (installed) or SoX `rec`.

## Steam and gamescope

The RPM Steam client currently uses XWayland. On the built-in 2880×1800 display at scale 1.667, compositor upscaling softened its text. XWayland now renders at 1:1. `desktop-steam` selects the focused monitor's scale, with per-monitor preferences from `~/.config/desktop/steam.json` (`monitorScales`). Without an entry Steam uses the monitor's own scale (1.667 on the built-in eDP-1, 1 on an unscaled external display), matching Wayland applications; the CEF renderer accepts fractional values. Add `"eDP-1": 2` to `monitorScales` for a larger interface (the previous default). `desktop-steam` also drops a session `XCURSOR_SIZE` so Steam uses the scaled X cursor resource. The local `steam.desktop` override routes the app menu, Steam links, and desktop actions through this wrapper. The desktop entry uses `/home/angelo/.local/bin/desktop-steam`; update that path for another user. The launcher adds `~/.local/bin` to Steam's PATH so games can find the gamescope wrapper. Direct `/usr/bin/steam` invocations bypass the wrapper.

**Exit Steam completely, including its tray process, then reopen it from the app menu** to apply the change. A running client receives requests without changing its startup scale. Steam does not dynamically rescale when moved between differently scaled monitors: exit and relaunch on the desired monitor. An explicit `-forcedesktopscaling` argument takes precedence; `DESKTOP_STEAM_SCALE=1.5 desktop-steam` provides a manual override. Outside Hyprland, Steam's normal automatic scaling is retained unless an override is supplied. No global GTK/Qt scaling variables or Electron flags are applied.

The installed client build 1788652215 ignored the legacy `-forcedesktopscaling` argument and `STEAM_FORCE_DESKTOPUI_SCALING` for visible desktop scaling, even with Steam's HiDPI switch enabled. `rendererScaling: true` in `steam.json` enables a small local CEF initialization workaround. The launcher compiles `steam-scale.c` once into `~/.cache/desktop/steam-ui/` (requires `cc`, provided by Fedora's `gcc` package). A dedicated runtime entry point loads it only in `steamwebhelper`; the Steam client and games do not receive the library through `LD_PRELOAD`. Original Steam scripts and binaries are not edited. The legacy controls remain for compatibility with other builds.

The workaround calls the renderer's existing scale API after successful initialization, producing larger text rendered at the target resolution. It depends on Steam's current runtime entry-point convention and CEF API; check it after client updates. Set `rendererScaling` to `false` and completely exit/reopen Steam to disable it. An unknown CEF scale symbol leaves the normal renderer unchanged. The approach was investigated using the [steam-hidpi-shim documentation](https://github.com/katerinakosac51-creator/steam-hidpi-shim); this repository keeps its own small implementation and limits loading to the web-helper runtime.

Gamescope is optional **per game**, leaving the regular Steam client outside it. Install `gamescope` with DNF; the Intel GPU also needs Mesa Vulkan drivers, including i686 drivers for 32-bit games. This machine already has both architectures. In **Game → Properties → General → Launch Options**, use one of:

```sh
# Native physical output/render resolution of the focused Hyprland monitor:
desktop-gamescope -- %command%
# Lower internal resolution, FSR 1 upscaling, and a 60 FPS limit on this 16:10 display:
desktop-gamescope --render 1920x1200 --fsr --fps 60 -- %command%
# Explicit output dimensions or a window rather than fullscreen:
desktop-gamescope --output 1920x1080 --windowed -- %command%
```

The wrapper uses gamescope's Wayland backend. It distinguishes physical pixels from Hyprland logical geometry, handles rotated outputs, defaults to native rendering without an FPS cap, and forwards the game command without shell evaluation. Focus the intended monitor before launching; normal Hyprland window rules still determine placement. `--output` changes dimensions, not the selected monitor. Keep render/output aspect ratios aligned to avoid unwanted bars. FSR 1 is spatial upscaling; lower resolutions trade detail for GPU workload. When Steam was started before the launcher PATH update, use the absolute `/home/angelo/.local/bin/desktop-gamescope` path in launch options or exit and reopen Steam. Remove the launch option to run the game normally. HDR, frame generation, driver overrides, and a separate gamescope login session are not enabled.

References: [Hyprland XWayland scaling](https://wiki.hypr.land/configuring/extra/xwayland/), [Valve Steam scaling discussion](https://github.com/ValveSoftware/steam-for-linux/issues/5460), [Valve gamescope options and per-game examples](https://github.com/ValveSoftware/gamescope#examples).

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

## Removable drives and iPhone

`desktop-session start` starts udiskie without a tray icon and activates `gvfs-afc-volume-monitor.service` in the user session. USB drives are automatically mounted through UDisks2; their notifications appear in Quickshell and Files handles browsing/ejection. Configuration is in the `udiskie` Stow package.

An iPhone is not a USB block disk: GVfs/AFC provides access in Nautilus, while usbmuxd and libimobiledevice handle USB communication and pairing. Connect a data-capable cable, unlock the phone, and accept **Trust This Computer** on the device, including its passcode if requested. Open Files and select the iPhone or its Documents entry. The GPhoto2 backend can also expose photos/camera content. Availability depends on iOS and the services/apps exposed by the phone; AFC does not grant access to the entire iOS filesystem, and app documents require the app's file-sharing support. No jailbreak or iOS modification is configured.

For pairing diagnostics, as the regular desktop user:

```sh
idevice_id -l
idevicepair validate
# Only when pairing is missing: unlock the phone and approve its trust dialog.
idevicepair pair
gio mount -li
systemctl --user status gvfs-afc-volume-monitor.service
systemctl status usbmuxd.service
```

With multiple devices, use `idevicepair -u DEVICE_ID validate` / `pair` to select one. If trust was denied, unlock and reconnect the phone, then accept the new prompt. Do not reset pairing or change permissions on `/var/lib/lockdown` as routine troubleshooting. usbmuxd is activated by the system's device rules; no manual `enable` or root-owned file manager is needed.

GVfs volumes use `afc://` URIs and appear in Files rather than `/run/media`. Use Files' unmount action when done. The currently connected iPhone was accessible after accepting its trust prompt. Pairing validation, a GVfs AFC mount, and a root metadata query succeeded without reading personal file contents; udiskie itself is not involved in that AFC connection.

References: [udiskie usage](https://github.com/coldfix/udiskie/wiki/Usage), [libimobiledevice](https://github.com/libimobiledevice/libimobiledevice), [GVfs AFC backend](https://gitlab.gnome.org/GNOME/gvfs/-/tree/master/daemon).
