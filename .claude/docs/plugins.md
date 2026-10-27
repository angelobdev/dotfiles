# Hyprland plugins

[← README](../../README.md)

Configuration: [`plugins.lua`](../../hypr/.config/hypr/config/plugins.lua). Screenshot bindings are in [`binds.lua`](../../hypr/.config/hypr/config/binds.lua); touchpad gestures remain in `input.lua`.

## Installation

Verified build: **Hyprland and hyprland-devel 0.56.2-17.fc44.x86_64**, nett00n COPR. Build dependencies:

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

Packaging in [`scripts/hyprpm`](../../scripts/hyprpm) downloads the five original projects at the revisions below. The script creates a local Git copy under `~/.local/share/dotfiles/hyprpm/`, registered with hyprpm as **dotfiles-desktop**. Enable/disable each plugin individually using its runtime name. No commit is created in the dotfiles repository.

| Plugin / source | Pinned revision |
| --- | --- |
| [Hyprspace](https://github.com/KZDKM/Hyprspace) | `cf08bed82621c1fb943ef4934ff0ba36540fea77` |
| [Hyprgrass](https://github.com/horriblename/hyprgrass) | `8e605468cbf429791d61ddbfaeb14ff5e08fec3e` |
| [Hyprglass](https://github.com/hyprnux/hyprglass) | `84c1a5ab217101a317d4edaab7fba2efcc1bf346` |
| [hypr-hot-edge](https://github.com/claychinasky/hypr-hot-edge) | `32b2dffdf2900a5a4b8cd10133f6a58cfd7ec4d6` |
| [HyprCapture](https://github.com/gfhdhytghd/HyprCapture) | `bf4d1f9021fc288200002f5a7d8291ed56f0df83` |

## Fedora COPR adaptations

This build reports Git commit `unknown`, so downloading headers from a Git revision is not usable. The installer checks that the session, installed binary, and `hyprland-devel` package match, then prepares hyprpm headers by copying the actual RPM headers. It preserves the original `version.h` and ABI. The cache remains root-owned at `/var/cache/hyprpm/$USER`; privileged operations are limited to this cache.

Fedora Hyprland uses Lua 5.4. hypr-hot-edge requires 5.5 in CMake despite using APIs available in both versions: packaging changes only dependency discovery to require Lua 5.4. Building and loading were verified with the compositor's library.

The manifest uses runtime name **HyprCapture**, including capitalization, avoiding the upstream manifest mismatch. It installs the Qt helper `~/.local/bin/hyprcapture-ui` and licenses. It does not install the optional TensorFlow/AEC microphone runtime: capture does not require it. Quickshell recording continues to use wf-recorder.

## Behavior

- **Hyprspace:** overview through the top-left corner or a three-finger upward touchscreen gesture. The same corner closes it on the next visit; no keyboard shortcut opens it, and `Esc` closes it. `affectStrut = false` prevents layout shifts; `hideTopLayers`/`hideOverlayLayers` exclude shell surfaces from previews.
- **hypr-hot-edge:** activates an empty internal special workspace; the Lua callback closes it and toggles Hyprspace on the affected monitor. The trigger rearms when the pointer leaves the corner. Applications cannot use it as a scratchpad.
- **Hyprgrass:** three fingers horizontally for workspaces; bottom-to-top edge swipe for applications; top-to-bottom for controls. Gestures are registered again on every reload.
- **Hyprglass:** `desktop` preset based on `subtle`, with moderate blur, graphite tint, and light refraction. Center distortion and chromatic aberration are zero. Fully opaque applications stay opaque; translucent surfaces receive the effect. Quickshell panel namespaces are explicit; the alpha threshold excludes the transparent area around panels. A backgroundless top bar is not filtered over text alone.
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

`desktop-plugins reload` runs automatically at Hyprland startup. Before loading, it compares the RPM, ABI, and running binary against installer state. After a COPR update it suspends autoload and shows a notification: the `unknown` hash alone cannot identify a compatible build.

Pins and the accepted RPM build are intentionally explicit in `scripts/hyprpm/build.py`. Compositor updates require compatible revisions to be checked, rebuilt, and tested in an isolated session before changing that guard. `hyprpm update` on the local packaging retains pins; it does not automatically select new upstream revisions.

To change packaging on the same build, run `hyprpm remove dotfiles-desktop`, then rerun the installer. To change ABI/headers, first check other registered repositories: the installer rejects a cache with a different ABI rather than overwriting it. Resetting the cache requires rebuilding all plugins that use it.

To temporarily disable a plugin, for example:

```sh
hyprpm disable hyprglass
desktop-plugins reload
hyprctl reload
```

The installer reenables all five plugins. Lua blocks are guarded so startup also works without plugins. Native Hyprland blur remains the fallback when Hyprglass is disabled.

Main-session installation is complete: all five plugins are enabled in hyprpm and loaded in Hyprland; `desktop-plugins reload` and `hyprctl configerrors` pass without errors.

Isolated-session verification covered loading all five `.so` files, parsing the actual Lua files, hot-edge → overview with internal workspace closure, rearming, and capturing the test monitor. Additional checks used two virtual outputs, 2880×1800 at scale 1.667 and 1920×1080 at scale 1: the same hot corner opens/closes the overview, reserved space changes 38 → 0 → 38 only on the affected monitor, HyprCapture overlays work on both, PNGs have native resolutions, and the editor toolbar is visible on the fractional-scale display. Physical gestures and selection on real displays still need confirmation during daily use.
