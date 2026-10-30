# Theming

[← Docs](../README.md)

One panel switches the whole desktop: shell, terminal, GTK and Qt apps, lock screen, wallpapers, fonts and icons, with hand-made themes and a dynamic one drawn from the wallpaper.

## The Theming panel

`Super + Ctrl + T` opens the Theming panel. `Ctrl+Tab` / `Ctrl+Shift+Tab` (or `Ctrl+PgDown` / `Ctrl+PgUp`) switch tabs, arrows move within a tab, Enter applies, and Esc closes.

**Tabs**
- **Theme:** a card per theme with a small mock-up of its surfaces, text and accent, plus its terminal colours; the current one is marked. Choosing one switches colours at once, and the theme's wallpaper follows.
  - **Bar: Shaded · Transparent** sets the bar style. Transparent drops the dark gradient, and the bar stays transparent. Only its text and icons change colour, taking whichever of the theme's light and dark text contrasts more with the wallpaper under the bar. With nothing drawn, the blur (which skips nearly transparent pixels) does not show either.
  - A double-click on an empty part of the bar switches the style too.
  - **Window corners** (0–24) and **Border** (none, 1–4 px) set the window rounding and border width. The border colours come from the theme: its accent for the focused window, its border colour for the others.
  - The border also frames the shell surfaces at the same width. Panels and menus take the accent, as they hold the focus. The dock, OSD and notification popups take the border colour. With **None** they keep their thin neutral outline.
  - The corners apply to the whole desktop, scaled from the design size of 16: windows, shell panels, cards, buttons, chips, the dock, OSD, tooltips, menus and the lock screen password field. Small dots and slider tracks stay round.
  - **Dynamic**, the last card, generates a theme from the current wallpaper with matugen and switches to it; its mock-up sits on that wallpaper. Choosing it again generates again. While it is the current theme, every wallpaper change (the gallery, Custom…, `Super + Ctrl + W`) generates it anew, and `Super + Ctrl + W` cycles the folder of the image it came from. Without matugen the card shows the install command instead.
  - **Dynamic mode: Auto · Dark · Light** and **Palette: Tonal spot · Vibrant · Expressive · Fidelity · Neutral** (shown once matugen is installed) shape the generated theme. Auto lets the image decide between light and dark. A change regenerates at once when the dynamic theme is active.
- **Wallpaper:** thumbnails of the current theme's set, with the current one outlined. For Graphite these are the images in the local wallpaper folders.
  - Thumbnails are cached JPEGs (`~/.cache/desktop-theme/thumbs/`), so WebP and very large images preview too.
  - Images that are not downloaded yet show a placeholder; "Download wallpapers" fetches them, and thumbnails appear as they arrive.
  - **Custom…** opens the file picker (`Super + Shift + W`).
  - A pick from either is remembered for the theme.
- **Font:** the installed interface and monospace families, each written in itself, plus a size from 9 to 13 and a preview. "Theme default" goes back to the theme's font.
  - **Use the monospace font everywhere** gives the interface the monospace family as well (shell, GTK, Qt, hyprlock, Kitty).
  - **Other installed family…** takes any installed family by name, even one the lists leave out; the name is checked with fontconfig first.
  - **Open fonts folder** opens `~/.local/share/fonts`; after adding fonts there, **Rescan** refreshes the font cache and the lists.
- **Icons:** the installed icon packs with five sample icons each, drawn from that pack. "Theme default" goes back to the theme's pack.
  - **Shell icons: Desktop · Icon pack** sets where the glyphs of the bar, Control Center, OSD and panels come from. Desktop uses the bundled set. Icon pack uses the pack's symbolic icons, tinted like the bundled ones, and keeps a bundled glyph wherever the pack has none.
  - **Other installed icon theme** takes a theme by its folder name, and **Open icons folder** opens `~/.local/share/icons` for packs installed by hand.

Font, size, icon pack, shell icons and bar style are your preferences: they apply to every theme. GTK applications follow them at once, and Kitty reloads. Qt applications follow them when reopened. The shell reads fonts and icons only at start, so after a font or icon change the panel shows a **Restart shell** banner. The restart reopens the panel on the same tab; open notifications stay in the history as archived entries.

## Themes

The palette above is the **Graphite** theme. Four more ship with the dotfiles, all dark:

| Theme | Accent | GSettings accent | VS Code |
| --- | --- | --- | --- |
| `catppuccin-mocha` | mauve `#cba6f7` | purple | Catppuccin Mocha |
| `tokyo-night` | blue `#7aa2f7` | blue | Tokyo Night |
| `gruvbox` | yellow `#fabd2f` | yellow | Gruvbox Dark Medium |
| `everforest` | green `#a7c080` | green | Everforest Dark |

Graphite uses VS Code's own Default Dark Modern. Their surfaces and terminal colours come from each project's published palette and Kitty port.

A theme is one `theme.json` with:
- `mode`, `fonts` and `system` (GTK, icon and cursor theme, GSettings accent);
- `shell` (the `Theme.qml` tokens);
- `palette` (the semantic colours the application templates use);
- `ansi` (16 terminal colours), `terminal.opacity`;
- `hyprland` (shadow, Hyprglass tint).

- `vscode` (`theme`, optional `extension`).

Only `palette` (bg, base, raised, border, fg, muted, dim, accent, accentFg, link, danger, success, warning) and `ansi` are required. `theme.py` derives any missing value from them, and explicit values always win:
- the `shell` tokens, with Graphite's alphas;
- the Qt bevel shades;
- the Hyprland shadow and glass tint.

Colours are `#rrggbb` or `#rrggbbaa`. Shipped themes live in `~/.local/share/desktop/themes/<id>/` (from `shell/.local/share/desktop/themes/`). Themes in `~/.config/desktop/themes/<id>/` take precedence.

`desktop-theme` (run at every login) renders the current theme with the templates in `~/.local/share/desktop/templates/` into `~/.local/state/desktop-theme/`. It writes:
- `quickshell.json`, `hyprland.lua`, `kitty.conf`, `gtk.css`, `qt-colors.conf` and `hyprlock.conf`;
- the GSettings values, and `current.json` (`{"theme": "<id>"}`).

The stowed configs only point at those files:
- `Theme.qml` watches `quickshell.json`, so the shell changes live.
- `config/theme.lua` loads `hyprland.lua` on every Hyprland reload.
- `kitty.conf` ends with an `include`.
- `gtk.css` is a single relative `@import`.
- qt5ct/qt6ct: `qtct.conf.tpl` is rendered to `~/.config/qt5ct/qt5ct.conf` and `~/.config/qt6ct/qt6ct.conf`; nothing Qt is stowed any more (the old `qt` package and its `colors/desktop.conf`, which showed up in the qtXct GUI as a stale Graphite scheme, are gone). The rendered file sets the fonts, icon pack, Fusion style and `color_scheme_path` to `qt-colors.conf`. Settings saved from the qt5ct/qt6ct GUI land in that file and are replaced on the next theme change; set fonts and icons in the Theming panel instead.
- `desktop-power lock` passes `--config` to hyprlock when the themed file exists.

Each consumer keeps Graphite as its fallback, so a missing state directory changes nothing. GTK is the exception: it falls back to plain Adwaita-dark until the next `desktop-theme` run.

Other applications:
- **VS Code:** `desktop-theme set` replaces (or adds) `workbench.colorTheme` and the preferred theme for the mode in `~/.config/Code/User/settings.json`. The preferred key is `workbench.preferredDarkColorTheme` or `workbench.preferredLightColorTheme`; VS Code uses it instead of `colorTheme` while `window.autoDetectColorScheme` is on, as it is here. The edit is targeted and leaves the rest of the file alone, and VS Code applies it live.
  - It is skipped when the theme's extension is not installed or the file is not valid JSON.
  - The four extensions are Catppuccin.catppuccin-vsc, enkia.tokyo-night, jdinhlife.gruvbox and sainnhe.everforest.
  - Before the themes, `workbench.colorTheme` was unset (Default Dark Modern).
- **btop:** every theme, Graphite included, is written to `~/.config/btop/themes/desktop.theme`. `btop.conf` gets `color_theme = "desktop"`, and a running btop reloads on `SIGUSR2`.
  - The main background stays empty, so the translucent Kitty background shows through.
  - btop rewrites `btop.conf` on exit, so it is not stowed. Set `color_theme = "Default"` to go back.
- **Zen and other portal-aware apps** follow the `color-scheme` that `mode` sets (all shipped themes are dark; the dynamic one can be light).

Preferences: `~/.local/state/desktop-theme/preferences.json` holds what is chosen in the Theming panel, or with these commands:
- `desktop-theme font --sans F --mono F --size N --unified on|off` (`--default` clears them). `--unified on` makes the interface use the monospace family.
- `desktop-theme icon-theme NAME|default`.
- `desktop-theme shell-icons desktop|pack`: the shell glyphs from `assets/icons`, or the icon pack's symbolic icons mapped in `components/IconNames.js`.
- `desktop-theme bar-style shade|transparent|toggle`.
- `desktop-theme window-style --rounding N --border N` (`--default` clears them). Hyprland `decoration.rounding` and `general.border_size`, defaulting to 16 and 0. The border colours (`general.col.active_border` / `inactive_border`) are the theme's accent and border colours, rendered into `hyprland.lua` and applied with `hyprctl reload`. The same rounding reaches Quickshell as `rounding` in `quickshell.json`: `Theme.corner(n)` scales each design radius by rounding/16, and `Theme.radius` is `corner(18)`. Radii under 6 (dots, tracks) are not scaled. hyprlock gets `rounding = 26 × rounding/16` for its password field. The border width and both colours reach Quickshell as `borderSize`, `activeBorder` and `inactiveBorder`. While `borderSize` is above 0, `Theme.frameWidth` and `Theme.frameActive` frame `Card` (every panel), `PopupMenu` and the tray menu, and `Theme.frameInactive` frames the dock, the OSD and notification popups. At 0 they keep a 1 px `stroke`, and popups none.

The bar style and shell icon source reach Quickshell through `quickshell.json` (`barStyle`, `iconSource`).

`theme.py tone` measures the strip under the bar on the current wallpaper. It crops the wallpaper to the focused monitor's logical size as hyprpaper does (cover), takes the mean grey of the top 4%, and caches it in `tone.json`.

Text and icons then use whichever of the current theme's two text colours (`shell.text`, `shell.accentText`) has the higher WCAG contrast with that strip. The bar background stays transparent. `services/BarStyle.qml` runs it whenever the wallpaper or the bar style changes.

They are merged over every theme before rendering, and an unset key keeps the theme's value. `theme.py fonts` and `theme.py icons` print the choices the panel offers:
- fonts from `fc-list :lang=en`, with script-specific, symbol, serif and URW families left out;
- icon themes with at least two sample icons of their own, resolved through `Inherits`. This list is cached in `icons-cache.json` until an icon directory changes.

Commands:
- `desktop-theme set <id>` switches theme. It renders everything before writing anything, reloads Hyprland and Kitty (`SIGUSR1`), and sets GSettings.
- GTK and Qt applications adopt the new palette when restarted.
- `desktop-theme list` prints the themes as JSON.
- `python3 ~/.local/libexec/desktop/theme.py render --theme <id> --out <dir>` previews the output without applying it.

### Dynamic theme

`desktop-theme generate [--image PATH]` (the Dynamic card in the Theming panel) runs `matugen image PATH --json hex --dry-run --source-color-index 0` on the current wallpaper by default, and writes `~/.config/desktop/themes/dynamic/theme.json`. It then applies it like `desktop-theme set dynamic` and remembers the image as the theme's wallpaper.
- **Palette** from the Material roles: bg = `surface`; base = `surface_container_lowest` (dark) or `surface_container_low` (light); raised = `surface_container_high`; border = `outline_variant`; fg = `on_surface`; muted = `on_surface_variant`; dim = `outline`; accent = `primary`; accentFg = `on_primary`; link = `tertiary`; danger = `error`.
- **ANSI, success and warning** use the standard terminal hues (red, green, yellow, blue, magenta, cyan), each turned at most 15° toward the primary, as Material harmonizes custom colours. matugen's base16 is not used, because it holds the image's own colours in no hue order. Their HSL lightness is then moved away from bg until they reach 3:1 (normal colours) or 4.5:1 (bright colours, which are also success and warning). Black and white come from the surfaces.
- **System:** Adwaita or Adwaita-dark, Papirus-Dark or Papirus-Light, the GSettings accent nearest to the primary hue (slate when it is grey), VS Code Default Dark Modern or Default Light Modern.
- **Light mode:** the bar shade uses bg at 60%/53% instead of black, so its dark text stays readable. This applies to any theme with `"mode": "light"` that does not set `barShadeTop`/`barShadeBottom`.
- `wallpaperDirectories` is the image's folder, so `Super + Ctrl + W` cycles it.

`desktop-theme dynamic --mode auto|dark|light --scheme tonal-spot|vibrant|expressive|fidelity|neutral` stores `dynamic` in `preferences.json` (matugen `-m smart|dark|light` and `-t scheme-…`) and regenerates when the dynamic theme is current. `services/DynamicTheme.qml` watches `current.json`, the wallpaper selection and the generated theme: while the theme is `dynamic` and the wallpaper is not its `source`, it runs `theme.py generate`, one run at a time.

Templates use `{{ path }}` or `{{ path | filter }}`, with the filters `hex`, `rgba[:aa]`, `qt[:aa]`, `hypr` and `hexrgba`. A key the theme lacks is an error, never an empty value.

The shell uses translucent surfaces with blur and thin borders. Window borders follow the Theming panel (width 0–4 px, theme colours; see [Themes](#themes)): active/fullscreen opacity 1, inactive opacity 0.92, and blur enabled. These values are in `hypr/.config/hypr/config/appearance.lua`. Active windows retain full readability.

## Wallpapers

```sh
~/.local/bin/desktop-wallpaper                     # open the QML picker
~/.local/bin/desktop-wallpaper /path/to/image.png
~/.local/bin/desktop-wallpaper --reset             # restore Fedora wallpaper
~/.local/bin/desktop-wallpaper --next              # next wallpaper of the current theme (Super + Ctrl + W)
```

The picker starts at home and supports moving to parent directories, entering a path, and opening the wallpaper collection. It supports PNG, JPEG, WebP, JXL, AVIF, BMP, and TIFF. ImageMagick converts the selected file into a managed JPEG, applies EXIF orientation, and preserves the original. Preview support depends on Qt decoders; a JXL without a preview can still be converted and applied.

Selection lives in `~/.local/state/desktop-session/wallpaper/`: `selection.json` stores the original path and `current.jpg` points to the converted copy. Hyprpaper uses that link in the Stow configuration and restores the selection at login; the repository is not rewritten on each wallpaper change. `desktop-session start` initializes the Fedora wallpaper link only when missing. Failed conversion or application preserves the previous selection. The local copy remains usable if the original moves.

### Wallpapers per theme

Each theme has its own set of wallpapers:
- **Graphite** uses the images in `~/.local/share/wallpapers` and `~/Pictures/Wallpapers` (`wallpaperDirectories`).
- **The other four** list eight each in their `theme.json` (`wallpapers`). Each entry has a file name, a raw GitHub URL pinned to a commit, a sha256 and its source.

Downloads:
- They are fetched only when needed into `~/.local/share/desktop/wallpapers/<theme>/` and never committed.
- A file is kept only when its sha256 matches. A failed or mismatched download is discarded, and the other entries still download.
- `python3 ~/.local/libexec/desktop/theme.py fetch <theme>` downloads a whole set ahead of time.
- `theme.py wallpapers [<theme>]` prints the set as JSON.

Switching theme also switches the wallpaper:
- `desktop-theme set` first remembers the current wallpaper (`selection.json` source) under the theme being left, in `~/.local/state/desktop-theme/wallpapers.json`.
- In the background it then applies the new theme's remembered wallpaper, or its first one, downloading the set if needed (log in `wallpapers.log` there).
- Wallpapers picked with `Super + Shift + W` or `Super + Ctrl + W` are remembered the same way.
- `Super + Ctrl + W` cycles through the current theme's set in order. If nothing is downloaded yet, it starts the download and shows a notification.

Sources:
- Omarchy's theme backgrounds (`basecamp/omarchy`, MIT);
- `zhichaoh/catppuccin-wallpapers` (MIT);
- `AngelJumbo/gruvbox-wallpapers` and `Apeiros-46B/everforest-walls`.

The last two declare no licence; their images are fetched for personal use and not redistributed. To change a set, edit `wallpapers` in the theme: a removed entry stays on disk until deleted from `~/.local/share/desktop/wallpapers/`.

State data is excluded from Git and follows this repository's standard XDG layout. The script serializes concurrent requests, passes paths as arguments, and normalizes the name sent through IPC, including spaces, commas, and special characters.

## Application theme

Dark glass theme: translucent graphite surfaces in Quickshell, Hyprland blur, and opaque text. Shell surfaces use the native palette's RGB values (`#191a1d`, `#202226`, `#292b30`) with separate alpha. Selected elements use opaque dark text for contrast. Kitty uses a 94% opaque background, Adwaita Mono, and matching ANSI colors; text stays opaque. Hyprland window borders remain disabled and inactive window opacity stays at 0.92.

The palette uses graphite gray, neutral primary `#d4d6dc`, light text, Adwaita Sans, and Papirus-Dark icons. GTK, Qt, and hyprlock share the palette; GSettings uses the slate accent. GTK 3 uses Adwaita-dark and CSS colors; GTK 4/libadwaita receives the dark preference through GSettings/the portal and named colors. Qt Widgets uses Fusion and custom palettes for both generations. The installed qt6ct plugin also accepts `qt5ct`, so `QT_QPA_PLATFORMTHEME=qt5ct` covers Qt 5/6. Qt Quick Controls uses Basic; applications with their own styling may ignore these preferences.

`desktop-theme` applies GSettings and imports Qt variables into D-Bus/systemd; on its first run it saves previous values to `~/.local/state/dotfiles/interface-before-theme.ini`. Restart open applications to adopt the theme; the next login also applies the full environment. Flatpak applications depend on sandbox runtimes/themes and may not follow every CSS override.
