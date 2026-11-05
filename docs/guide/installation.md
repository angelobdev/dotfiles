# Installation and maintenance

[← README](../../README.md)

Verified versions: Hyprland 0.57.1, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6, and hyprpaper 0.8.4.

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
| `zsh` | `~/.zshenv` and `~/.config/zsh`: the login shell with Powerlevel10k, zsh-autocomplete and the other plugins; see [Terminal shell](../features/shell.md) |
| `steam-hidpi` | Optional: `~/.local/share/applications/steam.desktop`, Steam through `desktop-steam` (only with `--with steam-hidpi`) |

## Automated installation

`scripts/install-desktop.py` turns an installed Fedora 45 into this desktop. It starts from any edition, Server included, and leaves disks and partitions alone. Other distributions and releases are refused until they are verified: [`manifest.toml`](../../scripts/install/manifest.toml) has the supported list.

```sh
sudo dnf install -y git-core python3
git clone https://github.com/angelobdev/dotfiles ~/.dotfiles
cd ~/.dotfiles
./scripts/install-tui.py                                     # guided, see below; or by hand:
./scripts/install-desktop.py                                 # preview: changes nothing
./scripts/install-desktop.py apply                           # or --profiles core,hardware,plugins,apps,codecs, …
sudo systemctl reboot
```

Run it as your user: it asks sudo for each system change. Each step checks what is left to do first, so running it again is always safe, and after an interruption it picks up where it stopped. The boot step comes last: until then the system keeps starting on the console.

| Profile | Installs |
| --- | --- |
| `core` | Hyprland, Quickshell, GDM with the `hyprland-uwsm` session, portals, audio, network, fonts and everything the shell calls; zsh as your login shell, with its [plugins](../features/shell.md) |
| `hardware` | Firmware, video decoding and sensors of an Intel 2-in-1, fingerprint and [tablet sign-in](#tablet-mode-sign-in-without-the-fingerprint-reader), firewall zone, `sshd` off; on the OmniBook, HP's sensor hub firmware for rotation from `--firmware DIR` (see [Tablet and touch](../features/tablet-and-touch.md#tablet-mode-and-rotation)) |
| `plugins` | What building the [Hyprland plugins](plugins.md) needs, from RPM Fusion too; the RPM Fusion `ffmpeg` replaces `ffmpeg-free` |
| `apps` | Zen Browser, 1Password, VS Code, Neovim, `gh`, `glab`, `uv`, `gcc` and a few command-line tools |
| `containers` | Docker (`moby-engine`, `docker-compose`, the `docker` group) and Tailscale |
| `media` | Loupe, Papers and Showtime for images, PDFs and videos |
| `gaming` | Steam, gamescope and the 32-bit drivers games need; see [Gaming](#gaming) |
| `steam-hidpi` | The Steam launcher that scales the client for the monitor it opens on (the optional `steam-hidpi` Stow package) |
| `codecs` | The RPM Fusion codecs: `ffmpeg` and `intel-media-driver` replace `ffmpeg-free` and `libva-intel-media-driver`, plus the GStreamer freeworld plugins, libav, OpenH264, HEIF and aptX |

The default is `core,hardware,plugins`; the others are opt-in. No Flatpak is installed: Flathub is yours to choose from. GDM needs GNOME Shell and GNOME Settings; the extras they recommend (Tour, Parental Controls, Color Profile Viewer, remote desktop, Rygel) are kept out. The manifest is the only list of packages: a new dependency goes there.

After the reboot, sign in at GDM. A terminal opens by itself and runs `install-desktop.py post`, which builds the plugins (hyprpm asks for confirmation) and lists what is left by hand. If it fails it comes back at the next login; to run it yourself, press `Super + Return`.

### Guided installation

`scripts/install-tui.py` runs the same steps behind a few terminal screens; it needs nothing beyond Python, so it also works on the console of a fresh Server install.

1. **Welcome**: the system, the model, the free space and the state of the [Hyprland plugins](plugins.md#verification-and-updates). Inside Hyprland, while the first login after an install has not finished, it also offers to finish it (`post`). **Remove the desktop** goes straight to a review of the [removal](#removal).
2. **Profiles**: each one says whether it is `installed`, partly installed (`3/12`, with what is missing) or not, from its packages, swaps and Stow links. On a desktop already set up the installed profiles start on, on a fresh system the defaults do, and `--profiles` wins over both. `Space` toggles one, `d` picks the defaults, `i` the installed ones; `core` always stays on. Turning off an installed profile removes nothing. The bottom shows what the highlighted profile adds, read from the manifest.
3. **Vendor firmware**: only on a model whose firmware is still missing (see `--firmware` above). Type the directory with a copy (`Tab` completes it) or leave it empty to go on without.
4. **Review**: the preview of every step, the warnings, and the equivalent `install-desktop.py` command. `Enter` opens a step's list, `r` checks again, `a` applies after a confirmation.

Nothing changes before `a`. Then the installer leaves the screens and runs in the terminal: sudo asks for the password once and stays valid for the whole run, each step prints what it does, and at the end it offers to reboot. `--profiles` and `--firmware` preset the choices. Without a terminal, or on one that cannot draw, use `install-desktop.py`.

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

The repository is the source of the files; Stow creates symlinks without directory folding. `dry-run` writes nothing and reports conflicts as errors. `--with steam-hidpi` also links that optional package. `apply` backs up conflicting files to `~/.local/state/dotfiles/backups/<timestamp>/`, simulates the operation, then applies the links. It rejects symlinked parent directories. Run `apply` again after adding files. Do not use sudo with Stow.

Multilingual support uses the existing Qt and Python installations, with no additional dependencies. The shell language comes from the session locale, then `/etc/locale.conf`; see [Interface language](configuration.md#interface-language) for details and catalogs.

Packages use standard XDG paths under `$HOME`, and nothing names a user: desktop entries call `desktop-*` commands by name, found through the `PATH` that `hypr/.config/hypr/config/session.lua` extends with `~/.local/bin`. The Fedora night wallpaper is included as JPEG in `hyprpaper/.local/share/wallpapers`, converted from the JPEG XL image of Fedora's `f44-backgrounds-base` because this hyprpaper build cannot decode it; the CC BY-SA 4.0 license and Fedora attribution are included next to it.

Removable drives use udiskie; iPhone access uses GVfs/AFC and usbmuxd. See [Removable drives and iPhone](integrations.md#removable-drives-and-iphone). The usbmuxd system service is activated by device discovery; no manual service enablement is required.

## Tablet mode sign-in without the fingerprint reader

Folded into tablet mode, the OmniBook screen covers the fingerprint reader, and `pam_fprintd` (authselect `with-fingerprint`) makes sudo, polkit and the lock screen wait for it. This step, part of the `hardware` profile, makes PAM skip the reader while the desktop is in tablet mode and ask for the password at once (typed on the on-screen keyboard); elsewhere nothing changes. To run it by hand:

```sh
./scripts/tablet-auth.sh install   # or: status, remove
```

It installs `/usr/local/libexec/desktop-tablet-mode` (succeeds only while `$XDG_RUNTIME_DIR/desktop-shell/tablet.json` of the user says `"tablet": true`), copies the `local` authselect profile to `custom/desktop-tablet`, inserts `auth [success=1 default=ignore] pam_exec.so quiet …` right before `pam_fprintd.so` in its `system-auth`, and selects it with the same features. `remove` selects `local` again and deletes both. Without it, Ctrl+C at the fingerprint prompt of sudo goes on to the password.

## Gaming

The `gaming` profile installs the RPM Steam client, gamescope, `gcc` (the C compiler used to cache the optional renderer scaling workaround) and the 32-bit Mesa Vulkan drivers and `vulkan-loader` that 32-bit Intel games need. The `steam-hidpi` profile adds the launcher that scales Steam for the monitor; by hand, `./scripts/stow.py apply --with steam-hidpi` links it and `./scripts/stow.py remove` unlinks it with the rest. See [Steam and gamescope](integrations.md#steam-and-gamescope) for the launcher and per-game launch options. Completely exit and reopen Steam after linking it.

## Compositor plugins

Hyprspace, Hyprgrass, Hyprglass, and HyprCapture are managed through hyprpm. The `plugins` profile installs their build dependencies; installation and updates are described in [Hyprland plugins](plugins.md). Run Stow after adding files, then run `./scripts/install-hypr-plugins.py` from a terminal in the Hyprland session.

## Removal

The installer takes the desktop away as it set it up. Log out of Hyprland first: removing the configuration a running Hyprland reads breaks it, so the installer refuses while one runs. Switch to a console (`Ctrl + Alt + F3`), sign in, and run:

```sh
cd ~/.dotfiles
./scripts/install-tui.py                          # Remove the desktop, review, a
./scripts/install-desktop.py dry-run --uninstall  # or by hand: the preview
./scripts/install-desktop.py apply --uninstall
```

`apply` writes down what each step is about to change, and the value it replaces, in `~/.local/state/dotfiles/install.json`. Uninstall reads it and undoes, in this order:

1. the Hyprland plugins (hyprpm's repository, the builds, `hyprcapture-ui`), the default session, GDM and the boot target as they were, the first-login autostart;
2. the zsh plugin clones, the Stow links (`stow.py remove`, then the files Stow had moved to `~/.local/state/dotfiles/backups` go back where they were), the GNOME interface settings saved before the first theme, and the Flatpak apps it installed;
3. authselect (the tablet profile, then the fingerprint feature), the firewall zone, the services, the login shell and the groups, before the packages they point at;
4. the files in `/etc` and the vendor firmware (then the initramfs), the packages the installer installed with whatever dnf removes along with them, the swaps back to the packages they replaced, and the repositories it added.

Every step checks first and leaves alone what is already back, so it is safe to run again, and the record stays, marked as undone, so a second run finds nothing to do. What you changed after the install stays as you left it, and the preview says so: a file in `/etc` you edited (a browser added to 1Password's list), a login shell, firewall zone, default session or boot target you chose since. The preview lists what dnf would remove, dependencies included. A package you installed yourself never goes as a dependent: the packages of the installer it needs stay (marked `keep`). A repository that packages staying still come from (an RPM Fusion driver, say) stays too, so they keep getting updates. A package that something staying still needs stays too: dnf refuses to break a protected package such as `systemd-udev`, and the installer leaves what it needs (for example `pkgconf-pkg-config`, which `kmod` uses). The prerequisites `python3` and `git-core` stay, and so do your preferences in `~/.config/desktop`, this repository, and the system upgrade the installer ran. Reboot afterwards: the system starts on the console, as before.

An install made before the record existed is rebuilt from the manifest and the package history, at the uninstall or at the next `apply`, whichever comes first: only packages that arrived after the system was installed (the first transactions, before any typed command) count, the login shell goes back to `/bin/bash`, the firewall zone to the edition's default, and units the installer turned off (such as `sshd.service`) stay off. If the history does not show how the system itself was installed, as in a container image, no package from before the record is removed. Both the preview and the guided installer say when this is the case. An unreadable record is moved aside to `install.json.unreadable` and rebuilt the same way. Uninstall still runs after an upgrade to a Fedora the manifest does not list yet; installing does not.

By hand, `./scripts/stow.py remove` only unlinks the files; stop the shell (`desktop-shell stop`) and daemons (`pkill -x hypridle; pkill -x hyprpaper; pkill -x udiskie`) first.
