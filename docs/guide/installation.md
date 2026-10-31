# Installation and maintenance

[← README](../../README.md)

Verified versions: Hyprland 0.57.0, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6, and hyprpaper 0.8.4.

## Packages

| Stow | Contents |
| --- | --- |
| `hypr` | `~/.config/hypr/hyprland.lua` and Lua modules |
| `quickshell` | Bar, launcher, controls, notifications, power menu, Polkit agent, and `i18n/it_IT.json` / `i18n/en_US.json` catalogs |
| `shell` | `~/.local/bin/desktop-{shell,session,power,theme,wallpaper,electron,portal-picker,steam,gamescope,ai,updates}`, the `desktop-updates` systemd user timer, and Python helpers for wallpapers, brightness, clipboard, recording, Bluetooth, EDS calendars, and shared translations (`i18n.py`) |
| `hypridle` | Timers and lock/suspend coordination |
| `hyprlock` | Wayland lock screen with PAM and fprintd fingerprints |
| `hyprpaper` | Fedora 44 night wallpaper on every monitor |
| `gtk` | Palette, fonts, icons, and dark preference for GTK 3/4 |
| `kitty` | Graphite terminal with translucent background and shared ANSI palette |
| `fastfetch` | Fedora layout with a neutral palette |
| `udiskie` | Removable-drive automounting, Quickshell notifications, and no external tray icon |
| `portals` | XDG preferences: Hyprland for capture/sharing, GTK for files and settings |
| `electron` | `~/.config/electron-flags.conf` (Wayland and IME flags) and `~/.config/desktop/electron-apps.conf` (the apps that get them through `electron.py`) |

## Automated installation

`scripts/install-desktop.py` turns an installed Fedora 45 into this desktop. It starts from any edition, Server included, and leaves disks and partitions alone. Other distributions and releases are refused until they are verified: [`manifest.toml`](../../scripts/install/manifest.toml) has the supported list.

```sh
sudo dnf install -y git-core python3
git clone https://github.com/angelobdev/dotfiles ~/.dotfiles
cd ~/.dotfiles
./scripts/install-desktop.py                                 # preview: changes nothing
./scripts/install-desktop.py apply                           # add --profiles core,hardware,plugins,apps for the apps
sudo systemctl reboot
```

Run it as your user: it asks sudo for each system change. Each step checks what is left to do first, so running it again is always safe, and after an interruption it picks up where it stopped. The boot step comes last: until then the system keeps starting on the console.

| Profile | Installs |
| --- | --- |
| `core` | Hyprland, Quickshell, GDM with the `hyprland-uwsm` session, portals, audio, network, fonts and everything the shell calls |
| `hardware` | Firmware, video decoding and sensors of an Intel 2-in-1, fingerprint and [tablet sign-in](#tablet-mode-sign-in-without-the-fingerprint-reader), firewall zone, `sshd` off |
| `plugins` | What building the [Hyprland plugins](plugins.md) needs, from RPM Fusion too |
| `apps` | Personal apps: browsers, editors, Steam, Docker, Tailscale, Flatpaks. Only when asked for |

The default is `core,hardware,plugins`. The manifest is the only list of packages: a new dependency goes there.

After the reboot, sign in at GDM. A terminal opens by itself and runs `install-desktop.py post`, which builds the plugins (hyprpm asks for confirmation) and lists what is left by hand. If it fails it comes back at the next login; to run it yourself, press `Super + Return`.

On Fedora Server the guided partitioning stops `/` at 15 GiB, which is not enough. Choose custom partitioning, or grow it afterwards: the installer warns under 30 GiB free and prints the command.

## Updates

The [`lionheartp/Hyprland`](https://copr.fedorainfracloud.org/coprs/lionheartp/Hyprland) COPR, which the Hyprland wiki recommends for Fedora, provides Hyprland and Quickshell. Its `hyprland-uwsm` package holds the GDM session entry.

```sh
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

Packages use standard XDG paths under `$HOME`. The `desktop-ai` and Steam desktop launchers contain `/home/angelo`: update them when installing for another user. The Fedora night wallpaper is included as JPEG in `hyprpaper/.local/share/wallpapers`, converted from the JPEG XL image of Fedora's `f44-backgrounds-base` because this hyprpaper build cannot decode it; the CC BY-SA 4.0 license and Fedora attribution are included next to it.

Removable drives use udiskie; iPhone access uses GVfs/AFC and usbmuxd. See [Removable drives and iPhone](integrations.md#removable-drives-and-iphone). The usbmuxd system service is activated by device discovery; no manual service enablement is required.

## Tablet mode sign-in without the fingerprint reader

Folded into tablet mode, the OmniBook screen covers the fingerprint reader, and `pam_fprintd` (authselect `with-fingerprint`) makes sudo, polkit and the lock screen wait for it. This step, part of the `hardware` profile, makes PAM skip the reader while the desktop is in tablet mode and ask for the password at once (typed on the on-screen keyboard); elsewhere nothing changes. To run it by hand:

```sh
./scripts/tablet-auth.sh install   # or: status, remove
```

It installs `/usr/local/libexec/desktop-tablet-mode` (succeeds only while `$XDG_RUNTIME_DIR/desktop-shell/tablet.json` of the user says `"tablet": true`), copies the `local` authselect profile to `custom/desktop-tablet`, inserts `auth [success=1 default=ignore] pam_exec.so quiet …` right before `pam_fprintd.so` in its `system-auth`, and selects it with the same features. `remove` selects `local` again and deletes both. Without it, Ctrl+C at the fingerprint prompt of sudo goes on to the password.

## Gaming

The `apps` profile installs the RPM Steam client, gamescope, `gcc` (the C compiler used to cache the optional renderer scaling workaround) and the 32-bit Mesa Vulkan drivers and `vulkan-loader` that 32-bit Intel games need. See [Steam and gamescope](integrations.md#steam-and-gamescope) for the local launcher and per-game launch options. Run Stow after adding these launchers, then completely exit and reopen Steam.

## Compositor plugins

Hyprspace, Hyprgrass, Hyprglass, and HyprCapture are managed through hyprpm. The `plugins` profile installs their build dependencies; installation and updates are described in [Hyprland plugins](plugins.md). Run Stow after adding files, then run `./scripts/install-hypr-plugins.py` from a terminal in the Hyprland session.

## Removal

First stop the shell (`desktop-shell stop`) and daemons (`pkill -x hypridle; pkill -x hyprpaper; pkill -x udiskie`), then run `./scripts/stow.py remove`. Removal unlinks the files, preserves the repository, and does not automatically restore backups. Copy the desired files from the backup and reload Hyprland. GSettings preferences remain: restore them using the values in `interface-before-theme.ini` with `gsettings set org.gnome.desktop.interface KEY VALUE`. Log in again to change the Qt environment.
