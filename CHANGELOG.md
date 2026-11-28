# Changelog

What changed in each release of the desktop. The desktop shows the sections of the releases it installs in **What's new** after an update, and **Settings → System → About** shows the section of the installed release; each is also a [GitHub release](https://github.com/angelobdev/dotfiles/releases).

Releases are `vMAJOR.MINOR.PATCH`: a new minor version brings new features, a patch only fixes, and a new major version changes something you may have to act on (said in its notes). How a release is made: [Releasing](docs/development/releasing.md).

## v1.6.0 - 2026-11-28

### Added

- **Moving wallpapers**, as in Omarchy: a wallpaper with a loop plays it in place of the picture while the computer is on AC power, and one with an intro plays it once when you choose it, when you switch theme and at login. Eight wallpapers of the Omarchy themes have a loop, 26 an intro. On battery, with **Reduce the shell's motion** on or under a fullscreen window the picture stays. **Settings → Desktop → Motion** turns loops and intros off on their own ([theming](docs/features/theming.md#moving-wallpapers)).
- Every theme's wallpapers and their videos download in the background at login, so switching theme shows its wallpapers at once (about 240 MB in all).

### Changed

- The Omarchy backgrounds that show Omarchy's name or logo are no longer among the wallpapers: one each from Flexoki Light, Lupine and Rosé Pine, three from Tokyo Night.

### Fixed

- Switching theme no longer opens the console (Herdr or Claude Code) when it was closed.
- The Global menu dialog no longer opens at every start of the shell, only when you add the widget to the bar.

## v1.5.0 - 2026-11-28

### Added

- **A global menu on the bar**, as on macOS: the `globalMenu` widget, which you add from the bar's gallery, shows the menus of the app on each monitor. They are read from the app itself (Firefox and its family, Qt and GTK apps through accessibility; Electron apps such as VS Code under X11, which the shell offers to set up when you add it), and an app without one gets a generic File, Edit, View, Window and Help. A right click opens its options: how the focus follows the pointer, the menu for apps without one, the app icon. An app open before the widget was added shows its own menu once restarted ([bar](docs/features/bar.md#global-menu)). Its reading of menus follows [Oma Top Menu](https://github.com/Somnius/oma.top.menu).
- **The 23 themes of Omarchy**, from Catppuccin Latte to Vantablack, in **Settings → Appearance → Theme** and the switcher, each with its wallpapers.
- **More default apps** in **Settings → Apps**: the text editor, images, PDF, video, music and mail. A choice there, and the browser and file manager of the shortcuts, is also what other apps open links, folders and files with; where you have chosen nothing, Files, Loupe, Papers and Showtime are set at login.

### Changed

- Esc goes one step back before it closes a panel: out of the details of a network, a category of the launcher or a question first, and back to the Control Center from Network, Bluetooth and Sound.
- Catppuccin Mocha, Everforest, Gruvbox and Tokyo Night are now Omarchy's: Gruvbox is its Gruvbox Material, with a teal accent instead of yellow. They change at the next login, or when you choose them again.

### Fixed

- Folders opened from other apps (a download, "Show in folder") open in Files, not in a terminal.
- The Wi-Fi password is asked right under its network instead of at the end of the panel.

## v1.4.0 - 2026-11-27

### Added

- **Commands in the launcher.** `Super + Space` now reaches everything the desktop can do as well as the apps, wholly from the keyboard. It opens on its categories, always in the same order: Apps (the app list from before), Toggles, Appearance, Windows & workspaces, Tools, System, Updates, Settings and Shortcuts. Typing searches the apps and every command together. `↑↓` select, Enter or `→` opens, `←` goes back, and `Alt` shows alternatives (Restart becomes **Restart to firmware setup**).
- Switches (Keep awake, Do Not Disturb, the bar…) flip in place, and choices (theme, power profile, sound output, workspace layout, bar background) mark the one in use. A command with a shortcut shows its keys.
- **Settings** in the launcher opens Settings on any section, tab or option, the option selected; **Shortcuts** runs any shortcut by its name.
- Your own commands in `~/.config/desktop/commands.json`: new ones, other labels or icons, or `"hidden": true` to leave one out ([Commands](docs/features/commands.md)). `desktop-shell commands [ID]` opens a category or runs a command from a script.

### Changed

- A right click on the empty desktop opens the launcher with its commands, instead of the desktop menu, which is gone.
- The launcher is narrower.

## v1.3.1 - 2026-11-27

### Fixed

- `Super + A` starts the coding agent in Herdr again when Herdr has only shells open, such as the tabs it gives back after a restart; the Assistant panel no longer lists those shells as agents.

## v1.3.0 - 2026-11-27

### Added

- **Window tricks**: pop a window out over the others on every workspace (`Super + O`), make it see-through (`Super + Backspace`), drop the gaps of a workspace (`Super + Shift + Backspace`), maximize (`Super + Alt + F`), tiled fullscreen (`Super + Ctrl + Shift + F`) and a full-screen desktop without the bar or gaps (`Super + Ctrl + Alt + F`). `Super + B` hides and shows the bar.
- **A layout per workspace**: tiling, scrolling or floating, with `Super + Ctrl + L` or a click on the focused workspace in the bar.
- **Reminders** (`Super + Ctrl + M`, or `desktop-shell remind 20 "Tea"`): they come at their time even with Do Not Disturb on, and the bar counts down to the next.
- The browser, password manager and file manager keys bring the app forward when it is open; `Super + Alt + Enter` and `Super + Alt + Shift + F` open a terminal or Files in the folder of the focused terminal.
- **QR codes** from a screen area (`Super + Ctrl + Shift + T`), and a right click on the bar clock steps through five formats (also in **Settings → Desktop → Bar**).
- **Updates** say when a restart is needed (a new kernel, Hyprland itself, a firmware update), keep 2 GB free before they start and the computer awake while they run, name the cause when they fail, and update firmware too.
- **Notifications** open their links (only plain web and mail addresses, with the site beside words that are not the address), and a repeat within 2 s is dropped.
- The OSD confirms toggles and actions: the window tricks, the bar, the keyboard layout and the power profile.
- The network details show live traffic, let a Wi-Fi network keep to 2.4 or 5 GHz, and run a speed test when one is installed.
- **Fingerprints**: enroll and remove them in **Settings → Privacy**.
- **Omarchy themes**: import one from its folder or a git URL in **Settings → Appearance → Theme**, or with `desktop-theme import`.
- New parts of the installer: `utils.printing` (CUPS and network printers) and `utils.snapshots` (a snapper snapshot of the root before and after each system update, on btrfs). Its defaults now also restart the fingerprint reader after a suspend, give editors room to watch files, stop services faster at shutdown, set the Wi-Fi country from the time zone, enable hardware video decoding in Firefox and Zen, and turn on a firewall on Arch.

## v1.2.1 - 2026-11-27

### Changed

- The **Floating** and **Pills** bars stand off the screen edges by the screen margin of the windows (**Settings → Appearance → Layout**) instead of a fixed 6 px, so they line up with the windows below, which keep the same margin from the bar.

## v1.2.0 - 2026-11-26

### Added

- **The system time zone from the calendar panel.** Under its title the calendar shows the time zone and its offset from UTC; **Change** searches every zone by city or region (in English) or by offset, such as `UTC+1`, and applies one after the administrator password. The bar clock follows at once; apps already open keep the old zone until they restart.
- When the weather follows where the computer is (no city set for it) and that place is in another time zone, the calendar suggests it: **You seem to be in …**, with **Use**.

## v1.1.0 - 2026-11-26

### Added

- **A bar you arrange yourself.** It is made of widgets in five sections: left, center left, center, center right and right; the three center ones stay together, centred on the screen. Without changes it looks as before.
- **Hold Super with the pointer on the bar** to edit it: drag widgets between sections, drop one on **Drop here to remove from the bar** to take it off, and release Super to save (`Esc` cancels). `Super` + right click on a widget moves or removes it; the **+** of a section opens the widgets not on the bar yet.
- A right click on an empty part of the bar opens its menu: **Edit layout** (without holding Super, until **Done**) and the **Classic**, **Centered** and **Minimal** layouts.
- New widgets: weather, volume (the wheel changes it), network, keyboard layout, a separator and a spacer.
- Two new bar backgrounds, **Floating** and **Pills** (one per section), in **Settings → Appearance → Theme** next to Shaded and Transparent. With Pills, **One pill for the center** (Settings → Desktop → Bar, or the bar menu) puts the center block on one.

### Changed

- A double click on an empty part of the bar steps through the four backgrounds instead of switching between Shaded and Transparent.

## v1.0.2 - 2026-11-26

### Fixed

- **What's new** shows an install from before releases the notes of every release up to the one it gets, not only the last: an update from before v1.0.0 straight to this release explains what releases are and which shortcuts moved.
- An install whose branch disappears from GitHub keeps finding the releases: it follows `stable`.

### Changed

- `stable`, the latest release, is now the default branch on GitHub, so a plain `git clone` gets it; the daily work is on `develop`. An install made before releases (on `main`) moves to `stable` at its next update, as before.

## v1.0.1 - 2026-11-26

### Fixed

- On Arch Linux, the Hyprland plugins (overview, touch gestures, glass, screenshots) are built again with Hyprland 0.57.2-2, the version now in `extra`: until this release they stayed off after that update. They are rebuilt once at the next login.

## v1.0.0 - 2026-11-26

The first release. From now on the desktop updates from releases instead of following every change as it is made: **Settings → System → Updates** (or the updates icon in the bar) offers a new release when there is one and shows what it changes, and after the update this window shows the changes once.

### Added

- Quick switchers for the theme (`Super + Ctrl + T`) and the wallpaper (`Super + Ctrl + W`): a row of large previews, ←→ to choose, Enter to apply.
- Shortcuts for the browser (`Super + Shift + Enter`), the password manager (`Super + Shift + Space`, 1Password Quick Access) and the file manager (`Super + Shift + F`). **Settings → Apps** chooses what they and `Super + Enter` open: Firefox, which the installer now adds, kitty and Files are the defaults.
- Releases and this **What's new** window. **Settings → System → About** shows the installed release and opens its notes again.
- `desktop-msfonts`: the Microsoft fonts (Segoe UI, Calibri, Cambria, Consolas…) from your own Windows ISO, installation media or Windows partition.
- Settings has a search field at the top of its sidebar; a found option is scrolled to and highlighted.
- A live preview of the layout (gaps, borders, rounding) in **Settings → Appearance → Layout**, and a map of the monitors in **Settings → Displays**.
- The launcher matches loosely, ranks by how well a name matches, and lists the apps you use most and most lately first. **Settings → Privacy** turns that history off and clears it.
- Optional workspace numbers in the bar, thumbnails for images in the clipboard, and the time each notification arrived in the notification center.

### Changed

- Some shortcuts moved to make room: **Settings** is `Super + Ctrl + Space` (no longer `Super + I`), **fullscreen** is `Super + F` (no longer `Super + Shift + F`), and the **next wallpaper** of the theme is `Super + Ctrl + Shift + W` (no longer `Super + Ctrl + W`). The Appearance section of Settings no longer has a shortcut of its own.
- Hyprland plugins for Hyprland 0.57.2-2: Hyprglass 1.2.0 (glass behind the menus of glassed bars, fixes for very large windows), HyprCapture 0.7.0 (text recognition in the screenshot editor, recording fixes) and Hyprgrass, with upstream fixes to how it tracks the windows a gesture touched. They are rebuilt once at the next login.
- Network, Bluetooth, Sound and Updates group their contents on cards; key hints are drawn as keycaps; dialogs take one of three widths.

### Fixed

- The launcher sorts names the same way in every language.
- Settings sections take the whole width of the panel, and Assistant scrolls clear of its key hints.
- The hours of the forecast in the calendar spread across the whole width.
- Bar icons are closer in weight and size, and eleven icons were redrawn in the style of the icon pack.
