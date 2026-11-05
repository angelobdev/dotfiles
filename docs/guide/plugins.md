# Hyprland plugins

[← README](../../README.md)

Configuration: [`plugins.lua`](../../hypr/.config/hypr/config/plugins.lua). Screenshot bindings are in [`binds.lua`](../../hypr/.config/hypr/config/binds.lua); touchpad gestures remain in `input.lua`.

## Installation

Verified builds: **Hyprland and hyprland-devel 0.57.1-1.fc45.x86_64**, from the [`lionheartp/Hyprland`](https://copr.fedorainfracloud.org/coprs/lionheartp/Hyprland) COPR that the Hyprland wiki recommends for Fedora, and on Arch **hyprland 0.57.1-1** from `extra`, which also holds the headers (compiled in a container; not yet loaded in an Arch session). The `plugins` profile of the [installer](installation.md#automated-installation) lists the build dependencies, some from RPM Fusion on Fedora, and runs this step at the first login. `hyprland-devel` has to stay installed on Fedora: the check at every login reads its version.

From a terminal in the Hyprland session, as a regular user:

```sh
cd ~/.dotfiles
./scripts/install-hypr-plugins.py
```

The script requests sudo for hyprpm's protected cache; confirm the local repository addition when hyprpm asks. Builds run as the user and may take several minutes initially. Verified builds are already cached on the development machine.

Packaging in [`scripts/hyprpm`](../../scripts/hyprpm) downloads the four original projects at the revisions below. The script creates a local Git copy under `~/.local/share/dotfiles/hyprpm/`, registered with hyprpm as **dotfiles-desktop**. Enable/disable each plugin individually using its runtime name. No commit is created in the dotfiles repository.

| Plugin / source | Pinned revision |
| --- | --- |
| [Hyprspace](https://github.com/KZDKM/Hyprspace) | `258b7b8bcea177e99da74946cf5cddd1dfe0e1ab` |
| [Hyprgrass](https://github.com/horriblename/hyprgrass) | `8ca1af717d5b4ea1215a781df52bcef02d7b15e6` |
| [Hyprglass](https://github.com/hyprnux/hyprglass) | `28b38df92176baf3d42fe58bf6c3b663d230c6c9` |
| [HyprCapture](https://github.com/gfhdhytghd/HyprCapture) | `fd465d85d953592862e30b296dd69ad746bc79af` |

## Fedora COPR adaptations

The installer checks that the session, installed binary, and `hyprland-devel` package (`hyprland` itself on Arch) match, then prepares hyprpm headers by copying the actual packaged headers, preserving `version.h` and the ABI. The cache remains root-owned at `/var/cache/hyprpm/$USER`; privileged operations are limited to this cache. Unlike the previous COPR, this build reports its real Git commit, so the ABI hash changes with each Hyprland release: after an update the installer resets the cache itself, at the next login, before anything is loaded (below).

The manifest uses runtime name **HyprCapture**, including capitalization, avoiding the upstream manifest mismatch. It installs the Qt helper `~/.local/bin/hyprcapture-ui` and licenses. It does not install the optional TensorFlow/AEC microphone runtime: capture does not require it. Quickshell recording continues to use wf-recorder.

## Behavior

- **Hyprspace:** overview through the top-left corner (a hover area of the bar that calls `desktop_overview` with `hyprctl eval`), a four-finger upward touchscreen swipe or the assist button. The same corner closes it on the next visit; no keyboard shortcut opens it, and `Esc` closes it. `affectStrut = false` prevents layout shifts; `hideTopLayers`/`hideOverlayLayers` exclude shell surfaces from previews.
- **Hyprgrass:** `hyprgrass-hold-touches.patch` (below) keeps gesture touches away from apps. No edge swipes. Three fingers left / right step workspaces, up opens applications, down the Control Center, a three-finger long press shows or hides the assist button; four fingers left / right move the active window to the neighbouring workspace, up toggles the overview, down opens notifications; a two-finger long press then drag moves a window; a long press on a window border resizes. The full table is in [Tablet and touch](../features/tablet-and-touch.md#gestures). Gestures are registered again on every reload.
- **Hyprglass:** the theme's `glassStyle` picks the preset. Most themes use `desktop`, based on `subtle`, with moderate blur, the theme tint, and light refraction; its light or dark tuning follows the theme mode (`mode` in the rendered `hyprland.lua`). It glasses the same shell surfaces the `desktop-glass` blur rule covers (dock, panels, notifications, OSD, share picker, menus, on-screen keyboard, password and PIN prompts); the bar has no background and only gets the native blur. Center distortion and chromatic aberration are zero. `layers.force_live_resample` is on and `windows.background_cache` is off: hyprglass's own change detection never noticed a window changing behind the glass, so an open panel, the assistant console or any translucent terminal showed a frozen copy of the video or text behind it. Layer glass is now re-rendered and window glass re-sampled every frame while glass is on screen, at some GPU cost. Fully opaque applications stay opaque; translucent surfaces receive the effect. Quickshell panel namespaces are explicit; the alpha threshold excludes the transparent area around panels. A backgroundless top bar is not filtered over text alone. The Glass themes use `liquid` instead: a 40 px lens rim (`edge_height` 60, `fresnel_reflection` 0.6) with refraction 1.8 and chromatic aberration 0.5 on the rim only, light blur (0.45) so the bent rim stays visible, a darker backdrop in dark mode (`brightness` 0.72, `adaptive_dim` 0.55) and a brighter one in light mode so text stays readable, a 1.5 px bevel on windows (shell surfaces use `liquid-surface`, the same preset without the bevel: contour glass rounds the bevel by about 0.6 × the rim width, which drew a second, differently rounded border inside them) and no grain, applied with `mask_mode = "contour"` so every card, toast and menu inside a layer gets its own rim. Translucent windows such as Kitty get the same look. These are the defaults: the Theming panel's glass settings change blur, refraction, dispersion, rim width and depth, reflection, highlight, bevel and grain per theme ([theming](../features/theming.md#the-theming-panel)).
- **HyprCapture:** `Super + Shift + S` / `Print` selects an area; `Super + Shift + Alt + S` / `Alt + Print` captures the current monitor. All four bindings use `open_editor()`. PNGs are saved to the XDG Pictures directory under `Screenshots`, copied to the clipboard, and announced with a system notification. `overlay_scope = "focus"` allows selection across monitors. The current configuration assigns no separate shortcut to direct capture or the active window.

`BarVisibility.qml` uses the small `bar_visibility.py` helper to observe `desktop-bar` surface alpha through Hyprland's local IPC socket (one process, output only on state changes). It checks every 2 s at rest and every 100 ms while a bar is hidden or for 4 s after a wake-up: the hot corner, the assist button and the four-finger swipe (through `desktop-shell overview`) wake it before opening the overview, so the bar still goes at once. When Hyprspace makes these surfaces invisible, Quickshell sets the exclusive zone and input region to zero on the affected monitor. The surface stays mapped: Hyprspace can restore its alpha on closing. The bar then reserves 38 px again. Disconnection restores normal behavior.

The [interface guide](interface.md) lists bindings and gestures.

## Verification and updates

```sh
hyprpm list
hyprctl plugin list
hyprctl configerrors
desktop-plugins reload
```

`desktop-plugins reload` runs automatically at Hyprland startup, before any plugin is loaded. It compares the package build (`rpm` on Fedora, `pacman` on Arch), ABI and running binary with the last build, and the packaging in `scripts/hyprpm` with the one hyprpm built from:

- **Both match**: it loads the plugins.
- **The packaging changed, or Hyprland was updated to a [verified build](#installation)**: it does not load the old plugins, and opens a terminal that runs `install-hypr-plugins.py`. With nothing loaded, the script replaces them whole (`hyprpm remove`, and for a new ABI a reset of `/var/cache/hyprpm/$USER`), builds, and loads them; it asks for sudo and for hyprpm's confirmations. If it stops, the session goes on without plugins and the next login tries again.
- **A rebuild stopped halfway** (offline, the terminal closed, a plugin that failed to build): hyprpm's repository is gone or marks a plugin as failed, so it opens the terminal again, and every login does until a build finishes.
- **Hyprland was updated to a build the pins were not verified against**: it shows a notification, and the session runs without plugins until the pins are checked and the build is added to `VERIFIED` in `scripts/hyprpm/bundle.py`.
- **`hyprland` and `hyprland-devel` have different versions** (an update that stopped halfway, Fedora only): it shows a notification and loads nothing; finish the update (`sudo dnf upgrade`) and log in again.

The guided installer shows which of these applies on its first screen.

Pins are intentionally explicit in `scripts/hyprpm/build.py`, the accepted package builds (Fedora's RPM, Arch's package) in `scripts/hyprpm/bundle.py`. Arch is a rolling release: a Hyprland update arrives with the next `pacman -Syu`, and the plugins wait for it to be verified as on Fedora. Compositor updates require compatible revisions to be checked, rebuilt, and tested in an isolated session before changing that guard. `hyprpm update` on the local packaging retains pins; it does not automatically select new upstream revisions.

A change to the packaging (`build.py`, `hyprpm.toml` or the patch) is rebuilt at the next login, as above. `install-hypr-plugins.py` refuses to replace plugins that are loaded, because swapping hyprgrass in a running compositor crashed it once ([troubleshooting](../development/verification-log.md#tablet-follow-ups-2026-10-30)); run in the session, it says to log in again. `bundle.py` is not part of the packaging digest, so accepting a Hyprland build rebuilds nothing by itself. To try a single plugin, replace its file with `install`, which leaves the running copy alone, and log in again.

`build.py` applies `scripts/hyprpm/hyprgrass-hold-touches.patch` to Hyprgrass. A new touch on a window waits up to 40 ms for more fingers: three or more claim the sequence and the window sees nothing, while one or two are replayed as soon as they lift, move past 12 px or, for two fingers, outlast the long press. Touches on Overlay and Top layer surfaces and on the lock screen are not held. On a window whose client never asked for `wl_touch`, one finger stands in for the pointer: past 12 px it sends axis events (source `finger`), otherwise its lift is a left click; a second finger ends this. The patch is part of the bundle and of its digest, so when the Hyprgrass pin moves it must be rebased or removed with it. The cache belongs to one ABI: with nothing loaded, the installer resets a cache built for another one, unless it also holds other hyprpm repositories, which would need their own rebuild; then it stops and names them.

To temporarily disable a plugin, for example:

```sh
hyprpm disable hyprglass
desktop-plugins reload
hyprctl reload
```

The installer reenables all four plugins. Lua blocks are guarded so startup also works without plugins. Native Hyprland blur remains the fallback when Hyprglass is disabled.

Main-session installation is complete: all four plugins are enabled in hyprpm and loaded in Hyprland; `desktop-plugins reload` and `hyprctl configerrors` pass without errors.

Isolated-session verification on 0.56 covered loading the `.so` files, parsing the actual Lua files, the hot corner, rearming, and capturing the test monitor; on 0.57 see [troubleshooting](../development/verification-log.md#hyprland-057-2026-10-30). Additional checks used two virtual outputs, 2880×1800 at scale 1.667 and 1920×1080 at scale 1: the same hot corner opens/closes the overview, reserved space changes 38 → 0 → 38 only on the affected monitor, HyprCapture overlays work on both, PNGs have native resolutions, and the editor toolbar is visible on the fractional-scale display. Physical gestures and selection on real displays still need confirmation during daily use.
