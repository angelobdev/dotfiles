# Installation and maintenance

[← README](../../README.md)

Verified versions: Hyprland 0.57.1, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6, and hyprpaper 0.8.4.

## Packages

| Stow | Contents |
| --- | --- |
| `hypr` | `~/.config/hypr/hyprland.lua` and Lua modules |
| `quickshell` | Bar, launcher, controls, notifications, power menu, Polkit agent, and `i18n/it_IT.json` / `i18n/en_US.json` catalogs |
| `shell` | `~/.local/bin/desktop-{shell,session,power,theme,wallpaper,electron,portal-picker,steam,gamescope,ai,updates,manager}`, the `desktop-updates` systemd user timer, and Python helpers for wallpapers, brightness, clipboard, recording, Bluetooth, EDS calendars, and shared translations (`i18n.py`) |
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

`scripts/install-desktop.py` turns an installed Fedora 45 or Arch Linux into this desktop. On Fedora it starts from any edition, Server included; on Arch, from a base system (pacstrap or archinstall) with your user in `wheel` and sudo allowed for it. It leaves disks and partitions alone. Other distributions and releases, Arch derivatives included, are refused until they are verified: [`manifest.toml`](../../scripts/install/manifest.toml) has the supported list.

```sh
sudo dnf install -y git-core python3                         # Fedora
sudo pacman -S --needed git python                           # Arch
git clone https://github.com/angelobdev/dotfiles ~/.dotfiles
cd ~/.dotfiles
./scripts/install-tui.py                                     # guided, see below; or by hand:
./scripts/install-desktop.py                                 # preview: changes nothing
./scripts/install-desktop.py apply                           # or --profiles core,hardware,plugins,apps.zen,utils.neovim, …
sudo systemctl reboot
```

Run it as your user: it asks sudo for each system change. Each step checks what is left to do first, so running it again is always safe, and after an interruption it picks up where it stopped. The boot step comes last: until then the system keeps starting on the console.

| Profile | Installs |
| --- | --- |
| `core` | Hyprland, Quickshell, GDM with the `hyprland-uwsm` session, portals, audio, network, fonts and everything the shell calls; zsh as your login shell, with its [plugins](../features/shell.md); the codecs: on Fedora from RPM Fusion, whose `ffmpeg` and `intel-media-driver` replace `ffmpeg-free` and `libva-intel-media-driver`, plus the GStreamer freeworld plugins, libav, OpenH264, HEIF and aptX |
| `hardware` | Firewall zone and `sshd` off on Fedora, and these parts: `intel` (Wi-Fi and Bluetooth firmware, GPU and video decoding, NPU, thermald and intel-lpmd), `audio` (SOF and Cirrus firmware, ALSA UCM), `camera` (libcamera, the IPU's sensing controller firmware), `fingerprint` (fprintd and the [polkit prompt](integrations.md) that tries it first), `firmware` (fwupd, bolt) |
| `tablet` | A 2-in-1: the accelerometer (`iio-sensor-proxy`) and its sensor hub modules, the stylus (`libwacom`), [tablet sign-in](#tablet-mode-sign-in-without-the-fingerprint-reader), and the Hyprgrass touchscreen gestures, the only [plugin](plugins.md) built for this profile alone; on the OmniBook, HP's sensor hub firmware for rotation from `--firmware DIR` (see [Tablet and touch](../features/tablet-and-touch.md#tablet-mode-and-rotation)) |
| `plugins` | What building the [Hyprland plugins](plugins.md) needs, from RPM Fusion too; the RPM Fusion `ffmpeg` replaces `ffmpeg-free` |
| `apps` | Desktop apps, as parts: `zen` (Zen Browser), `onepassword` (1Password, allowed to fill in Zen), `vscode`, and the GNOME viewers `loupe`, `papers` and `showtime` |
| `utils` | Command-line tools, as parts: `neovim`, `gcc`, `xclip`, `unrar`, `fuse` (FUSE 2 for AppImages), `gh`, `glab`, `uv`, `wev`, and `tailscale` with its tray icon |
| `assistant` | The AI Assistant: Super + A, its bar icon and its Settings section need it. With it, the [Herdr app and herdr-core](../features/ai-assistant.md#with-herdr-any-coding-agent), the assistant console for any coding agent: their release archives (pinned version and sha256, x86_64 or aarch64) unpacked as you into `~/.local`, where herdr's own installer puts them, with the `hc` link and the launcher entry. Once there they update themselves (the app, and `hc update`), so the installer never installs them again |
| `containers` | Docker (`moby-engine`, `docker-compose`, the `docker` group) |
| `radio` | The [Radio panel](../features/radio.md): mpv (on MPRIS through mpv-mpris), yt-dlp, Qt Multimedia for its video, and ytfzf on Arch |
| `gaming` | `gcc`, and as parts: `steam` with the 32-bit drivers games need, `steam-hidpi` (the launcher that scales the client for the monitor it opens on, the optional `steam-hidpi` Stow package) and `gamescope`; see [Gaming](#gaming) |

**Parts.** A part is picked on its own, as `profile.part` (`apps.zen`, `hardware.camera`), and brings its profile with it. A profile picked alone comes with its default parts:

- `hardware` checks a part where it finds the hardware: `intel` and `audio` on an Intel CPU, `camera` with a V4L2 device or an Intel IPU, `fingerprint` with the USB reader of a known vendor (Synaptics, Goodix, Validity, Egis, FPC, FocalTech, Elan). `firmware` is always checked.
- `apps` checks Zen and the three viewers, `utils` checks Neovim, gcc, xclip, unrar and FUSE, and `gaming` checks all three.

Removing a profile removes its parts too. Removing one part removes only what nothing that stays needs.

On Arch the profiles are the same, from the official repositories, with these differences:

- Hyprland, `hyprpm`, its headers and the `hyprland-uwsm` session entry come from `extra`: no COPR, no `-devel` packages.
- No swaps: Arch's `ffmpeg` and `intel-media-driver` are already the complete builds, so the codecs in `core` are only the GStreamer plugins (bad, ugly, libav) and libheif.
- `hardware.fingerprint` installs `fprintd`, and `tablet` leaves out the [tablet sign-in](#tablet-mode-sign-in-without-the-fingerprint-reader), which is not ported yet: the fingerprint works at GDM, on the lock screen and in the polkit prompt (its own `/etc/pam.d/polkit-1`, as on Fedora); sudo asks for the password. It sets no firewall zone and leaves `sshd` alone, since Arch enables neither. The firmware Fedora splits in several packages is in `linux-firmware-intel`; the initramfs is rebuilt with `mkinitcpio -P` (or dracut, if the system uses it).
- `gaming` first enables the `multilib` repository in `/etc/pacman.conf`.
- `containers` has no tray icon for Tailscale: Arch's package has no unit for it.
- `apps` builds Zen Browser, 1Password and VS Code from the AUR: see [AUR packages](#aur-packages-arch).

pacman installs with `-Syu` (a partial upgrade is not supported on Arch), never installs optional dependencies, and picks `pipewire-jack` where something needs a JACK library.

The default is `core,hardware,plugins` with the default parts of `hardware`, and `tablet` too on a 2-in-1 (a tablet mode switch or a touchscreen in `/proc/bus/input/devices`); the others are opt-in. An install made before `tablet` existed counts it as installed with `hardware`, which held it then. The record of an install made before parts names its profiles in the new ones as it is read: `hardware`, `plugins` and `gaming` with all their parts, `apps` with its apps and the tools that are `utils` now, `herdr` as `assistant`, `media` as `radio` with the three viewers of `apps`, `steam-hidpi` as `gaming.steam-hidpi`, `containers` with `utils.tailscale`, and `codecs` in `core`. Nothing is installed or removed for that. No Flatpak is installed: Flathub is yours to choose from. GDM needs GNOME Shell and GNOME Settings; the extras they recommend (Tour, Parental Controls, Color Profile Viewer, remote desktop, Rygel) are kept out. The manifest is the only list of packages: a new dependency goes there.

After the reboot, sign in at GDM. A terminal opens by itself and runs `install-desktop.py post`, which builds the plugins (hyprpm asks for confirmation) and lists what is left by hand. If it fails it comes back at the next login; to run it yourself, press `Super + Return`.

### Guided installation

`scripts/install-tui.py` runs the same steps behind a few terminal screens; it needs nothing beyond Python, so it also works on the console of a fresh Server install. Once the desktop is there, it also [keeps it updated](#checking-for-updates), and `desktop-manager` opens it from any terminal (`desktop-manager updates` on the updates screen; other arguments go to it as they are: `--profiles`, `--add PROFILES` starts on the profiles with those checked on top of the installed ones, `--remove PROFILES` on the review of [removing them](#removing-profiles)).

1. **Welcome**: the system, the model, the free space and the state of the [Hyprland plugins](plugins.md#verification-and-updates). Inside Hyprland, while the first login after an install has not finished, it also offers to finish it (`post`). **Check for updates** opens the [updates screen](#checking-for-updates); **Remove profiles** asks which profiles to take away, then reviews [their removal](#removing-profiles); **Remove the desktop** goes straight to a review of the [removal](#removal).
2. **Profiles**: each one says whether it is `installed`, partly installed (`3/12`, with what is missing) or not, from its packages, swaps and Stow links; a profile with parts says how many of them are there (`2/5 parts`). On a desktop already set up the installed profiles and parts start on, on a fresh system the defaults do, and `--profiles` wins over both. `Right` opens the parts of a profile and `Left` closes them. `Space` toggles a profile (with its default parts) or a part (with its profile), `d` picks the defaults, `i` the installed ones; `core` always stays on. Turning off an installed profile here removes nothing: **Remove profiles** does. The bottom shows what the highlighted profile adds, read from the manifest.
3. **Vendor firmware**: only on a model whose firmware is still missing (see `--firmware` above). Type the directory with a copy (`Tab` completes it) or leave it empty to go on without.
4. **Review**: the preview of every step, the warnings, and the equivalent `install-desktop.py` command. `Enter` opens a step's list, `r` checks again, `a` applies after a confirmation.

Nothing changes before `a`. Then the installer leaves the screens and runs in the terminal: sudo asks for the password once and stays valid for the whole run, each step prints what it does, and at the end it offers to reboot. `--profiles` and `--firmware` preset the choices. Without a terminal, or on one that cannot draw, use `install-desktop.py`.

On Fedora Server the guided partitioning stops `/` at 15 GiB, which is not enough. Choose custom partitioning, or grow it afterwards: the installer warns under 30 GiB free and prints the command.

### Checking for updates

**Check for updates** in the guided installer (or `desktop-manager updates`, which opens it directly) shows what is newer than the desktop, one line per source, for the profiles the installer applied (from its record; without one, the installed profiles):

| Line | What it checks | What applying it does |
| --- | --- | --- |
| System packages | dnf, or `checkupdates` on Arch: the same list as the update icon in the bar | the installer's `upgrade` step |
| Flatpak apps | `flatpak remote-ls --updates` | `flatpak update`: the system apps with sudo, your own as you |
| AUR packages (Arch), maintainer only | the AUR's latest commit of each pinned PKGBUILD, and the version it builds | the new commit and version go into the manifest, then the `aur` step builds them |
| Release archives, maintainer only | each archive's version in its release manifest (`latest`), for a new install: Herdr updates itself once installed | the new version and its sha256 go into the manifest; the `archives` step installs only what is missing |
| zsh plugins, maintainer only | each clone's latest release tag (`track = 'tags'` in the manifest, as zsh-autocomplete) or the head of its branch (Powerlevel10k, whose releases stopped) | the new commit goes into the manifest, then the `clones` step checks it out |
| Repository | how far this repository is behind its upstream branch (`origin/main` in a clone from GitHub), after a `git fetch` that never asks for a password | `git merge --ff-only`; then `stow.py apply` links new files, Hyprland reloads and the shell restarts (through Hyprland, in the session's environment) when their files changed, and the installer starts again on this screen, from the new version |
| Desktop | what the installed profiles still need from the manifest (after a pull, say) | nothing here: **Install or update the desktop** applies it, after its own review |
| Hyprland plugins | the state of the plugin builds | nothing: they are replaced at a login, before they load |

The pin lines are for whoever maintains the manifest: they write new pins into `scripts/install/manifest.toml` for you to commit, and a clone with uncommitted changes can no longer fast-forward. They show only in a repository with `git config desktop.maintainer true`; every other install gets new pins with **Repository**, and **Desktop** then lists the AUR builds and clone checkouts they need. Keep your own settings in `~/.config/desktop` ([configuration](configuration.md#your-own-settings)), so the repository stays clean and every pull is a fast-forward.

`Space` checks a line, `Enter` shows its details (the packages, the new commits and the links to review their changes), `r` checks again, `a` applies the checked lines after a confirmation, with one sudo prompt for the whole run. Everything there is to apply starts checked but the repository: a pull goes alone and first, because it can move the pins, and the rest is checked again after it. The repository is offered only for a fast-forward, on a clean tree with no commits of its own; a clone with local changes keeps its pin, and the details say which files to look at. New pins change `scripts/install/manifest.toml`, which stays for you to commit, so the other machines get the same ones. From the command line, `./scripts/install-desktop.py pins` lists the newer pins of every distribution (commits, and versions of the release archives) with their links, and `pins --update` writes them into the manifest.

### AUR packages (Arch)

Zen Browser, 1Password and Visual Studio Code are not in Arch's repositories. The manifest pins each AUR PKGBUILD to a commit and names the version that commit builds. The `aur` step checks the commit out in `~/.cache/dotfiles/aur/<package>`, imports the key the sources are signed with when the manifest names one (1Password's; the PKGBUILD's `validpgpkeys` still decides which key may sign), and builds and installs the package with `makepkg` as your user, which asks sudo only for pacman. The preview needs no network: a package is pending while it is missing or at another version than the pinned one. If the commit builds another version than the manifest says, the step stops before building.

To update them:

```sh
./scripts/install-tui.py --updates                # the AUR packages line of the updates screen, or by hand:
./scripts/install-desktop.py pins                 # newer AUR commits, the version each builds, a link to the PKGBUILD changes
./scripts/install-desktop.py pins --update        # once you reviewed them: the new commits go into manifest.toml
./scripts/install-desktop.py apply --profiles core,hardware,plugins,apps
```

`pins` reads the manifest, not the system, so it works from Fedora as well; it covers the [zsh plugin clones](../features/shell.md) too. Uninstall removes the AUR packages with the others, and the checkouts.

## Updates

The [`lionheartp/Hyprland`](https://copr.fedorainfracloud.org/coprs/lionheartp/Hyprland) COPR, which the Hyprland wiki recommends for Fedora, provides Hyprland and Quickshell. Its `hyprland-uwsm` package holds the GDM session entry. On Arch they come from `extra`, and the update icon in the bar checks with `checkupdates` (from `pacman-contrib`, as your user) and updates with `sudo pacman -Syu`; the AUR packages are updated with `pins`, above.

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

Not on Arch yet: Arch has no authselect, and editing its PAM files by hand is left for a step of its own.

It installs `/usr/local/libexec/desktop-tablet-mode` (succeeds only while `$XDG_RUNTIME_DIR/desktop-shell/tablet.json` of the user says `"tablet": true`), copies the `local` authselect profile to `custom/desktop-tablet`, inserts `auth [success=1 default=ignore] pam_exec.so quiet …` right before `pam_fprintd.so` in its `system-auth`, and selects it with the same features. `remove` selects `local` again and deletes both. Without it, Ctrl+C at the fingerprint prompt of sudo goes on to the password.

## Gaming

The `gaming` profile installs the RPM Steam client, gamescope, `gcc` (the C compiler used to cache the optional renderer scaling workaround) and the 32-bit Mesa Vulkan drivers and `vulkan-loader` that 32-bit Intel games need. The `steam-hidpi` profile adds the launcher that scales Steam for the monitor; by hand, `./scripts/stow.py apply --with steam-hidpi` links it and `./scripts/stow.py remove` unlinks it with the rest. See [Steam and gamescope](integrations.md#steam-and-gamescope) for the launcher and per-game launch options. Completely exit and reopen Steam after linking it. On Arch, Steam and the 32-bit Mesa and Vulkan drivers (Intel and AMD) come from `multilib`, which the profile enables.

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
2. the zsh plugin clones, the release archives it unpacked (Herdr and herdr-core, at whatever version they updated to; `~/.config/herdr-app` stays), the Stow links (`stow.py remove`, then the files Stow had moved to `~/.local/state/dotfiles/backups` go back where they were), the GNOME interface settings saved before the first theme, and the Flatpak apps it installed;
3. authselect (the tablet profile, then the fingerprint feature), the firewall zone, the services, the login shell and the groups, before the packages they point at;
4. the files in `/etc` and the vendor firmware (then the initramfs), the packages the installer installed with whatever dnf removes along with them (on Arch, `pacman -Rsc`: what depends on them and the dependencies nothing else needs, then what the desktop's installs brought that `-s` keeps although nothing needs it, such as Steam's `lib32-systemd`, which a bare `libudev.so` dependency of `device-mapper` seems to need; the AUR packages and their checkouts too), the swaps back to the packages they replaced, and the repositories it added (on Arch, `multilib` is commented out again).

Every step checks first and leaves alone what is already back, so it is safe to run again, and the record stays, marked as undone, so a second run finds nothing to do. What you changed after the install stays as you left it, and the preview says so: a file in `/etc` you edited (a browser added to 1Password's list), a login shell, firewall zone, default session or boot target you chose since. The preview lists what dnf would remove, dependencies included. A package you installed yourself never goes as a dependent: the packages of the installer it needs stay (marked `keep`). A repository that packages staying still come from (an RPM Fusion driver, say) stays too, so they keep getting updates. A package that something staying still needs stays too: dnf refuses to break a protected package such as `systemd-udev`, and the installer leaves what it needs (for example `pkgconf-pkg-config`, which `kmod` uses). The prerequisites `python3` and `git-core` (`python` and `git` on Arch) stay, and so do your preferences in `~/.config/desktop`, this repository, and the system upgrade the installer ran. Reboot afterwards: the system starts on the console, as before.

An install made before the record existed is rebuilt from the manifest and the package history, at the uninstall or at the next `apply`, whichever comes first: only packages that arrived after the system was installed (on Fedora the first transactions, before any typed command; on Arch, what pacman's log shows before the installer's first install) count, the login shell goes back to `/bin/bash`, the firewall zone to the edition's default, and units the installer turned off (such as `sshd.service`) stay off. If the history does not show how the system itself was installed, as in a container image, no package from before the record is removed. Both the preview and the guided installer say when this is the case. An unreadable record is moved aside to `install.json.unreadable` and rebuilt the same way. Uninstall still runs after an upgrade to a Fedora the manifest does not list yet; installing does not.

By hand, `./scripts/stow.py remove` only unlinks the files; stop the shell (`desktop-shell stop`) and daemons (`pkill -x hypridle; pkill -x hyprpaper; pkill -x udiskie`) first.

### Removing profiles

One profile, or a few, can go while the desktop stays, from the session too:

```sh
./scripts/install-tui.py --remove gaming,media              # the review, then a
./scripts/install-desktop.py dry-run --remove gaming,media  # or by hand: the preview
./scripts/install-desktop.py apply --remove gaming,media
```

It undoes the same way as the uninstall, step by step, but only what the record holds *and* the removed profiles name in the manifest *and* no installed profile that stays names too: `gcc` stays while `apps` or `gaming` does, `fprintd` while `hardware` or `tablet` does, the RPM Fusion repositories while a profile that uses them does, the `ffmpeg` swap while `plugins` or `codecs` does. A package of a profile that stays never goes as a dependent either, nor does one it needs: `tablet` leaves `iio-sensor-proxy` and `libwacom`, which GDM and Hyprland need (the review marks them `keep`), and they count as core's from then on: removing `tablet` again finds nothing to do. So the steps are those of the profile: its packages and what dnf removes with them, swaps, repositories, files in `/etc` and firmware, groups and services (`hardware` turns `sshd` back on and restores the firewall zone), the tablet sign-in, Flatpak apps, release archives (`herdr`), AUR packages and their checkouts, and the profile's own Stow package (`steam-hidpi`). Then the record no longer lists the profile, nor what went: a package installed again later by hand is yours. Removing `tablet` leaves Hyprgrass out of the next [plugin](plugins.md) build, at the next login.

`core` is the desktop itself: removing it is [Removal](#removal). `plugins` goes only from a console with Hyprland logged out, as the whole desktop does: without its packages the plugins can neither be checked at login nor rebuilt, so their builds go too. What the installer did not record (an install from before the record, whose packages came then) stays: the preview shows what is left to undo.

### Profiles in Settings

Settings → System → Profiles (`desktop-shell toggle settings system/profiles`) lists every profile with its description and what of it is on this system, as the profiles screen of the guided installer reads it (`profiles.py list`): installed, partly installed (how much of it), not installed, or installed but not by the installer (Herdr from its own installer, say), which the installer has no record of and does not remove. **Install** (**Complete** for one partly there) and **Remove** show the installer's plan in the tab first:

- **Install** previews `install-desktop.py dry-run --profiles` with that profile, and its default parts, on top of the recorded ones.
- **Remove**, for a profile the installer recorded, previews `dry-run --remove NAME`; see [its removal](#removing-profiles).

- **Parts**: the arrow beside a profile with parts shows them, one switch each. **Apply changes** previews what the switches changed: the parts switched on are added, those switched off removed (`profiles.py run`, the installer for one, then the other).

Nothing changes before **Apply**. Apply runs the same command with `apply` in the background (`jobs.py`), behind one password or fingerprint prompt through the [root broker](../development/architecture.md#root-for-operations-from-settings). The tab shows the progress, the result and, while it runs or when it failed, the end of the log. A notification gives the result, and the list is read again. Removing `plugins` waits for a session without Hyprland, as the installer requires, and the tab says so before any prompt. `core` has neither button: it is the desktop itself. **Open the guided installer** opens its menu in a terminal, for the rest: the first install, removing the desktop, firmware.
