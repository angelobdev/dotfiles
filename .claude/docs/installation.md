# Installation and maintenance

[← README](../../README.md)

Verified versions: Hyprland 0.56.2, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6, and hyprpaper 0.8.4.

## Packages

| Stow | Contents |
| --- | --- |
| `hypr` | `~/.config/hypr/hyprland.lua` and Lua modules |
| `quickshell` | Bar, launcher, controls, notifications, power menu, Polkit agent, and `i18n/it_IT.json` / `i18n/en_US.json` catalogs |
| `shell` | `~/.local/bin/desktop-{shell,session,power,theme,wallpaper,electron,portal-picker,steam,gamescope}` and Python helpers for wallpapers, brightness, clipboard, recording, Bluetooth, EDS calendars, and shared translations (`i18n.py`) |
| `hypridle` | Timers and lock/suspend coordination |
| `hyprlock` | Wayland lock screen with PAM and fprintd fingerprints |
| `hyprpaper` | Fedora 44 night wallpaper on every monitor |
| `gtk` | Palette, fonts, icons, and dark preference for GTK 3/4 |
| `qt` | Graphite colour scheme for Qt 5/6 (qt5ct/qt6ct); `qt5ct.conf`/`qt6ct.conf` themselves are rendered by `desktop-theme` |
| `kitty` | Graphite terminal with translucent background and shared ANSI palette |
| `fastfetch` | Fedora layout with a neutral palette |
| `udiskie` | Removable-drive automounting, Quickshell notifications, and no external tray icon |
| `portals` | XDG preferences: Hyprland for capture/sharing, GTK for files and settings |
| `electron` | `~/.config/electron-flags.conf` with Wayland flags for launchers that read it |

## Installation and updates

This machine uses the `nett00n/hyprland` and `errornointernet/quickshell` COPRs.

```sh
sudo dnf install hyprland quickshell stow kitty brightnessctl ddcutil wireplumber \
  NetworkManager bluez upower power-profiles-daemon \
  hypridle hyprlock hyprpaper qt5ct qt6ct papirus-icon-theme ripgrep \
  f44-backgrounds-base xorg-x11-server-Xwayland ImageMagick python3 libnotify jq grim slurp \
  xdg-desktop-portal xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
  wl-clipboard cliphist wf-recorder pulseaudio-utils fprintd fprintd-pam \
  python3-gobject evolution-data-server \
  udiskie udisks2 gvfs gvfs-afc gvfs-gphoto2 usbmuxd libimobiledevice-utils
cd ~/.dotfiles
./scripts/stow.py dry-run
./scripts/stow.py apply
./scripts/check.sh
hyprctl reload
~/.local/bin/desktop-session start
# Only after installing/changing portals; stop active sharing sessions first:
systemctl --user restart xdg-desktop-portal-hyprland xdg-desktop-portal-gtk xdg-desktop-portal
~/.local/bin/desktop-shell restart
```

The repository is the source of the files; Stow creates symlinks without directory folding. `dry-run` writes nothing and reports conflicts as errors. `apply` backs up conflicting files to `~/.local/state/dotfiles/backups/<timestamp>/`, simulates the operation, then applies the links. It rejects symlinked parent directories. Run `apply` again after adding files. Do not use sudo with Stow.

Multilingual support uses the existing Qt and Python installations, with no additional dependencies. The shell language comes from `/etc/locale.conf`; see [Interface language](configuration.md#interface-language) for details and catalogs.

Packages use standard XDG paths under `$HOME`. The two Qt `color_scheme_path` settings and the Steam desktop launcher contain `/home/angelo`: update them when installing for another user. The Fedora 44 wallpaper is included as JPEG in `hyprpaper/.local/share/wallpapers`, converted from the installed JPEG XL image because this hyprpaper build cannot decode it. It comes from `f44-backgrounds-base`; the original CC BY-SA 4.0 license and Fedora attribution are included in the package files.

Removable drives use udiskie; iPhone access uses GVfs/AFC and usbmuxd. See [Removable drives and iPhone](integrations.md#removable-drives-and-iphone). The usbmuxd system service is activated by device discovery; no manual service enablement is required.

## Optional fonts

The Theming panel lists the installed fonts. These add common interface and coding families from the Fedora repositories:

```sh
sudo dnf install rsms-inter-fonts ibm-plex-sans-fonts ibm-plex-mono-fonts jetbrains-mono-fonts fira-code-fonts
```

The dynamic theme (the Dynamic card in the Theming panel) needs matugen, from the `nett00n/hyprland` COPR that also provides Hyprland:

```sh
sudo dnf install matugen
```

WebP previews in the file picker (`Super + Shift + W`) need Qt's image format plugins; the Theming panel does not, as it shows cached JPEG thumbnails:

```sh
sudo dnf install qt6-qtimageformats
```

## Optional gaming packages

For the RPM Steam client and per-game gamescope support:

```sh
sudo dnf install gamescope gcc
```

Steam must already be installed from the configured package source. `gcc` supplies the C compiler used to cache the optional renderer scaling workaround; the existing plugin build tools already provide it on this machine. Mesa Vulkan drivers and `vulkan-loader` are needed in x86_64 and i686 variants for 64/32-bit Intel games; both are present on this machine. See [Steam and gamescope](integrations.md#steam-and-gamescope) for the local launcher and per-game launch options. Run Stow after adding these launchers, then completely exit and reopen Steam.

## Compositor plugins

Hyprspace, Hyprgrass, Hyprglass, hypr-hot-edge, and HyprCapture are managed through hyprpm. Build dependencies, installation, and updates are described in [Hyprland plugins](plugins.md). Run Stow after adding files, then run `./scripts/install-hypr-plugins.py` from a terminal in the Hyprland session.

## Removal

First stop the shell (`desktop-shell stop`) and daemons (`pkill -x hypridle; pkill -x hyprpaper; pkill -x udiskie`), then run `./scripts/stow.py remove`. Removal unlinks the files, preserves the repository, and does not automatically restore backups. Copy the desired files from the backup and reload Hyprland. GSettings preferences remain: restore them using the values in `interface-before-theme.ini` with `gsettings set org.gnome.desktop.interface KEY VALUE`. Log in again to change the Qt environment.
