# Hyprland plugins

[← README](../../README.md)

Configuration: [`plugins.lua`](../../hypr/.config/hypr/config/plugins.lua). Screenshot bindings are in [`binds.lua`](../../hypr/.config/hypr/config/binds.lua); touchpad gestures remain in `input.lua`.

## Installation

Verified build: **Hyprland and hyprland-devel 0.57.0-1.fc44.x86_64**, from the [`lionheartp/Hyprland`](https://copr.fedorainfracloud.org/coprs/lionheartp/Hyprland) COPR that the Hyprland wiki recommends for Fedora. Build dependencies:

```sh
sudo dnf install hyprland-devel git gcc-c++ make cmake pkgconf-pkg-config \
  meson ninja-build glm-devel lua-devel pango-devel patch \
  qt6-qtsvg-devel qt6-qtwayland-devel layer-shell-qt-devel \
  opencv-devel pipewire-devel pulseaudio-libs-devel fftw-devel ffmpeg-devel \
  nlohmann-json-devel libjpeg-turbo-devel x265-devel libde265-devel
```

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

The installer checks that the session, installed binary, and `hyprland-devel` package match, then prepares hyprpm headers by copying the actual RPM headers, preserving `version.h` and the ABI. The cache remains root-owned at `/var/cache/hyprpm/$USER`; privileged operations are limited to this cache. Unlike the previous COPR, this build reports its real Git commit, so the ABI hash changes with each Hyprland release: after an update the cache has to be reset (`sudo rm -rf /var/cache/hyprpm/$USER`, then the installer).

The manifest uses runtime name **HyprCapture**, including capitalization, avoiding the upstream manifest mismatch. It installs the Qt helper `~/.local/bin/hyprcapture-ui` and licenses. It does not install the optional TensorFlow/AEC microphone runtime: capture does not require it. Quickshell recording continues to use wf-recorder.

## Behavior

- **Hyprspace:** overview through the top-left corner (a hover area of the bar that calls `desktop_overview` with `hyprctl eval`), a four-finger upward touchscreen swipe or the assist button. The same corner closes it on the next visit; no keyboard shortcut opens it, and `Esc` closes it. `affectStrut = false` prevents layout shifts; `hideTopLayers`/`hideOverlayLayers` exclude shell surfaces from previews.
- **Hyprgrass:** `hyprgrass-hold-touches.patch` (below) keeps gesture touches away from apps. No edge swipes. Three fingers left / right step workspaces, up opens applications, down the Control Center, a three-finger long press shows or hides the assist button; four fingers left / right move the active window to the neighbouring workspace, up toggles the overview, down opens notifications; a two-finger long press then drag moves a window; a long press on a window border resizes. The full table is in [interface.md](interface.md#hot-corner-and-touchscreen). Gestures are registered again on every reload.
- **Hyprglass:** `desktop` preset based on `subtle`, with moderate blur, the theme tint, and light refraction; its light or dark tuning follows the theme mode (`mode` in the rendered `hyprland.lua`). It glasses the same shell surfaces the `desktop-glass` blur rule covers (dock, panels, notifications, OSD, share picker, menus, on-screen keyboard, password and PIN prompts); the bar has no background and only gets the native blur. Center distortion and chromatic aberration are zero. Fully opaque applications stay opaque; translucent surfaces receive the effect. Quickshell panel namespaces are explicit; the alpha threshold excludes the transparent area around panels. A backgroundless top bar is not filtered over text alone.
- **HyprCapture:** `Super + Shift + S` / `Print` selects an area; `Super + Shift + Alt + S` / `Alt + Print` captures the current monitor. All four bindings use `open_editor()`. PNGs are saved to the XDG Pictures directory under `Screenshots`, copied to the clipboard, and announced with a system notification. `overlay_scope = "focus"` allows selection across monitors. The current configuration assigns no separate shortcut to direct capture or the active window.

`BarVisibility.qml` uses the small `bar_visibility.py` helper to observe `desktop-bar` surface alpha through Hyprland's local IPC socket (100 ms, one process, output only on state changes). When Hyprspace makes these surfaces invisible, Quickshell sets the exclusive zone and input region to zero on the affected monitor. The surface stays mapped, retaining the IdleInhibitor: Hyprspace can restore its alpha on closing. The bar then reserves 38 px again. Disconnection restores normal behavior.

The [interface guide](interface.md) lists bindings and gestures.

## Verification and updates

```sh
hyprpm list
hyprctl plugin list
hyprctl configerrors
desktop-plugins reload
```

`desktop-plugins reload` runs automatically at Hyprland startup. Before loading, it compares the RPM, ABI, and running binary against installer state. After a COPR update it suspends autoload and shows a notification, so the next login runs without plugins until they are rebuilt.

Pins and the accepted RPM build are intentionally explicit in `scripts/hyprpm/build.py`. Compositor updates require compatible revisions to be checked, rebuilt, and tested in an isolated session before changing that guard. `hyprpm update` on the local packaging retains pins; it does not automatically select new upstream revisions.

To change packaging on the same build, run `hyprpm remove dotfiles-desktop`, then rerun the installer. Both steps change plugins inside the running compositor: save your work first, since swapping hyprgrass by hand crashed it once ([troubleshooting](troubleshooting.md#tablet-follow-ups-2026-10-30)). To try a single plugin, replace its file with `install`, which leaves the running copy alone, and log in again.

`build.py` applies `scripts/hyprpm/hyprgrass-hold-touches.patch` to Hyprgrass. A new touch on a window waits up to 40 ms for more fingers: three or more claim the sequence and the window sees nothing, while one or two are replayed as soon as they lift, move past 12 px or, for two fingers, outlast the long press. Touches on Overlay and Top layer surfaces and on the lock screen are not held. The patch is part of the bundle and of its digest, so when the Hyprgrass pin moves it must be rebased or removed with it. To change ABI/headers, first check other registered repositories: the installer rejects a cache with a different ABI rather than overwriting it. Resetting the cache requires rebuilding all plugins that use it.

To temporarily disable a plugin, for example:

```sh
hyprpm disable hyprglass
desktop-plugins reload
hyprctl reload
```

The installer reenables all four plugins. Lua blocks are guarded so startup also works without plugins. Native Hyprland blur remains the fallback when Hyprglass is disabled.

Main-session installation is complete: all four plugins are enabled in hyprpm and loaded in Hyprland; `desktop-plugins reload` and `hyprctl configerrors` pass without errors.

Isolated-session verification on 0.56 covered loading the `.so` files, parsing the actual Lua files, the hot corner, rearming, and capturing the test monitor; on 0.57 see [troubleshooting](troubleshooting.md#hyprland-057-2026-10-30). Additional checks used two virtual outputs, 2880×1800 at scale 1.667 and 1920×1080 at scale 1: the same hot corner opens/closes the overview, reserved space changes 38 → 0 → 38 only on the affected monitor, HyprCapture overlays work on both, PNGs have native resolutions, and the editor toolbar is visible on the fractional-scale display. Physical gestures and selection on real displays still need confirmation during daily use.
