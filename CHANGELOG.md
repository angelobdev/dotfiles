# Changelog

What changed in each release of the desktop. The desktop shows the sections of the releases it installs in **What's new** after an update, and **Settings → System → About** shows the section of the installed release; each is also a [GitHub release](https://github.com/angelobdev/dotfiles/releases).

Releases are `vMAJOR.MINOR.PATCH`: a new minor version brings new features, a patch only fixes, and a new major version changes something you may have to act on (said in its notes). How a release is made: [Releasing](docs/development/releasing.md).

## v1.0.0 - 2026-11-26

The first release. From now on the desktop updates from releases instead of following every change as it is made: **Settings → System → Updates** (or the updates icon in the bar) offers a new release when there is one and shows what it changes, and after the update this window shows the changes once.

### Added

- Releases and this **What's new** window. **Settings → System → About** shows the installed release and opens its notes again.
- `desktop-msfonts`: the Microsoft fonts (Segoe UI, Calibri, Cambria, Consolas…) from your own Windows ISO, installation media or Windows partition.
- Settings has a search field at the top of its sidebar; a found option is scrolled to and highlighted.
- A live preview of the layout (gaps, borders, rounding) in **Settings → Appearance → Layout**, and a map of the monitors in **Settings → Displays**.
- The launcher matches loosely, ranks by how well a name matches, and lists the apps you use most and most lately first. **Settings → Privacy** turns that history off and clears it.
- Optional workspace numbers in the bar, thumbnails for images in the clipboard, and the time each notification arrived in the notification center.

### Changed

- Hyprland plugins for Hyprland 0.57.2-2: Hyprglass 1.2.0 (glass behind the menus of glassed bars, fixes for very large windows), HyprCapture 0.7.0 (text recognition in the screenshot editor, recording fixes) and Hyprgrass, with upstream fixes to how it tracks the windows a gesture touched. They are rebuilt once at the next login.
- Network, Bluetooth, Sound and Updates group their contents on cards; key hints are drawn as keycaps; dialogs take one of three widths.

### Fixed

- The launcher sorts names the same way in every language.
- Settings sections take the whole width of the panel, and Assistant scrolls clear of its key hints.
- The hours of the forecast in the calendar spread across the whole width.
- Bar icons are closer in weight and size, and eleven icons were redrawn in the style of the icon pack.
