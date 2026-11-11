# Theming

[← Docs](../README.md)

One panel switches the whole desktop: shell, terminal, GTK and Qt apps, lock screen, wallpapers, fonts and icons, with hand-made themes and a dynamic one drawn from the wallpaper.

## The Theming panel

The Theming panel is the **Appearance** section of **Settings**. `Super + Ctrl + T` opens Settings there (and closes it when Appearance is already on screen); `Super + I`, the Settings entry in the launcher or `desktop-shell toggle settings` open Settings on the section seen last. Settings has a sidebar of sections after GNOME Settings; more of the desktop's configuration moves in over time ([#8](https://github.com/angelobdev/dotfiles/issues/8)). On a screen narrower than the sidebar and a section together, it shows one of the two, with a back button. `Ctrl+Tab` / `Ctrl+Shift+Tab` (or `Ctrl+PgDown` / `Ctrl+PgUp`) switch tabs, and so does a one-finger swipe sideways over the page by touch (to the left for the next tab); arrows move within a tab, Enter applies, and Esc closes.

**Tabs**
- **Theme:** a card per theme with a small mock-up of its surfaces, text and accent, plus its terminal colours; the current one is marked. Choosing one switches colours at once, and the theme's wallpaper follows.
  - Above the cards, each option is a label and a drop-down (`components/ChoiceCombo.qml`, the interface of `ChoiceChips`), wrapping onto a second line when the panel is narrow; the font size and the shell icon source on their tabs are drop-downs too. Only the tab switcher keeps its pills.
  - **Bar: Shaded · Transparent** sets the bar style. Transparent drops the dark gradient, and the bar stays transparent. Only its text and icons change colour, taking whichever of the theme's light and dark text contrasts more with the wallpaper under the bar. A soft halo in the other text colour keeps them readable where part of the wallpaper differs from the rest of the strip (a bright sky on one side only). With nothing drawn, the blur (which skips nearly transparent pixels) does not show either.
  - **Effects: Full · Reduced** is for less powerful machines, or for less motion. Reduced turns off Hyprland's animations, blur and shadows and the Hyprglass glass (on windows and shell surfaces; the plugin stays loaded), and stops the shell's own animations as `reduceMotion` does. With no blur behind them, the shell's backgrounds, surfaces, notifications and tooltips become at least 94% opaque, so translucent themes such as Glass stay readable. It applies to every theme and Hyprland reloads at once. Settings of your own in `~/.config/desktop/hypr.lua`, loaded last, still win.
  - A double-click on an empty part of the bar switches the style too; the hint sits under the Bar drop-down.
  - **Window corners** (0–24) and **Border** (none, 1–4 px) set the window rounding and border width. The border colours come from the theme: its accent for the focused window, its border colour for the others.
  - The border also frames the shell surfaces at the same width. Panels and menus take the accent, as they hold the focus. The dock, OSD and notification popups take the border colour. With **None** they keep their thin neutral outline.
  - **Gaps** (0–16) and **Screen margin** (0–32) set the space between tiled windows and between windows and the screen edges (Hyprland `gaps_in` / `gaps_out`, 4 and 4 by default).
  - A small preview of three tiled windows beside (or, on a narrow page, below) the four drop-downs follows them as they are chosen, at 1:6 scale, with the active and inactive border colours; it is only an illustration.
  - Top-level shell surfaces take exactly the window radius, so panels, the Control Center, the dock, the OSD, popup notifications and menus line up with the windows, and their glass follows the same corner. What sits inside them keeps its own, smaller radius.
  - The corners apply to the whole desktop, scaled from the design size of 16: windows, shell panels, cards, buttons, chips, the dock, OSD, tooltips, menus and the lock screen password field. Small dots and slider tracks stay round.
  - **Dynamic**, the last card, generates a theme from the current wallpaper with matugen and switches to it; its mock-up sits on that wallpaper. Choosing it again generates again. While it is the current theme, every wallpaper change (the gallery, Custom…, `Super + Ctrl + W`) generates it anew, and `Super + Ctrl + W` cycles the folder of the image it came from. Without matugen the card shows the install command instead.
  - **Dynamic mode: Auto · Dark · Light** (shown once matugen is installed) shapes the generated theme. Auto lets the image decide between light and dark. A change regenerates at once when the dynamic theme is active. The palette always uses matugen's Tonal spot style: the other styles mostly moved the accent and were dropped.
- **Glass settings**, the slider button on the current theme's card, opens a page with the Hyprglass options of that theme: blur, refraction, colour fringe, lens rim width, lens depth, rim reflection, highlight, window bevel and grain. The bevel applies to windows only: shell surfaces keep their own 1 px stroke instead. Only themes with `glassStyle = "liquid"` (Glass and Glass Light) have it.
  - Each slider saves when it is released (with the arrow keys, after a short pause) and reloads Hyprland, so the glass changes at once. A value that differs from the default is shown in the accent colour; hovering it shows the default.
  - **Reset to defaults** clears the theme's changes; **Themes** goes back. Each theme keeps its own values.
- **Wallpaper:** thumbnails of the current theme's set, with the current one outlined. For Graphite these are the images in the local wallpaper folders.
  - Thumbnails are cached JPEGs (`~/.cache/desktop-theme/thumbs/`), so WebP and very large images preview too.
  - Images that are not downloaded yet show a placeholder; "Download wallpapers" fetches them, and thumbnails appear as they arrive.
  - **Custom…** opens the file picker (`Super + Shift + W`).
  - A pick from either is remembered for the theme.
- **Font:** the installed interface and monospace families, each written in itself, plus a size from 9 to 13 and a preview. "Theme default" goes back to the theme's font.
  - **Use the monospace font everywhere** gives the interface the monospace family as well (shell, GTK, Qt, hyprlock, Kitty).
  - **Other installed family…** takes any installed family by name, even one the lists leave out; the name is checked with fontconfig first.
  - **Open fonts folder** opens `~/.local/share/fonts`; after adding fonts there, **Rescan** refreshes the font cache and the lists.
- **Find online…** (on the Cursors tab, and above the icon packs) opens the KDE Store page: the cursor or icon themes of store.kde.org, most downloaded first, with search, previews, authors and downloads, the same catalogue as Plasma's "Get New" dialogs. **Install** takes the chosen file of an entry (some have variants), checks its md5 when the store gives one, unpacks it (tar through tarfile's data filter member by member, zip checked for paths outside it; at most 300 MB downloaded and 2 GB unpacked) and keeps only theme folders (a `cursors/` folder, or an `index.theme` with `[Icon Theme]` directories) in `~/.local/share/icons`. It never replaces a folder it did not install, notes its own in `~/.local/share/desktop/store.json`, and **Remove** deletes only those (`store.py`). `qs ipc call desktop theming store-icons` (or `store-cursors`) opens the page.
- **Font** also has **Shell text**, a drop-down next to the size: 100, 115, 130 or 150% for the text the shell draws itself (bar, panels, notifications, OSD, on-screen keyboard), applied at once (`desktop-theme text-scale`, `Theme.textSize()`); applications follow the font size above it.
- **Icons:** the installed icon packs with five sample icons each, drawn from that pack. "Theme default" goes back to the theme's pack.
- **Cursors:** the installed cursor themes (XCursor folders with `cursors/`, or hyprcursor ones with a `manifest.hl`, from the usual icon folders), each with five of its own shapes (arrow, hand, text, busy, resize) drawn at the chosen size, and that size: 24, 32, 40 or 48. "Theme default" goes back to the theme's cursor. The shapes are read from the theme's files by `theme.py` (the first frame of the largest image up to 96 px, by CSS name or the X11 names older themes use) and cached as PNG, or SVG for a hyprcursor shape, in `~/.cache/desktop-theme/cursors/`, keyed by the cursor file, so a changed theme gets new previews. **Find online…**, **Open icons folder** and **Rescan** are on this tab too. Hyprland takes the cursor at once (`hyprctl setcursor`), so GTK 4 and Qt 6 apps, which ask it for cursor shapes, change with it; GSettings `cursor-theme`/`cursor-size`, the X resources (`desktop-xwayland`, scaled by the monitor) and the session's `HYPRCURSOR_THEME`, `HYPRCURSOR_SIZE` and `XCURSOR_THEME` follow, so other apps change once reopened. No shell restart is needed. The desktop's set is Adwaita and Breeze (packages) and macOS, macOS White, Bibata Modern Classic and Bibata Modern Ice: pinned releases (sha256-checked, cached in `~/.cache/desktop/cursors/`) that `desktop-theme apply` fetches in the background at login when they are missing, unpacking only each one's folder into `~/.local/share/icons`. Until then they are listed as "(download)" and choosing one fetches it at once.
  - **Shell icons: Desktop · Icon pack** sets where the glyphs of the bar, Control Center, OSD and panels come from. Desktop uses the bundled set. Icon pack uses the pack's symbolic icons, tinted like the bundled ones, and keeps a bundled glyph wherever the pack has none.
  - **Other installed icon theme** takes a theme by its folder name, and **Open icons folder** opens `~/.local/share/icons` for packs installed by hand.

Font, size, icon pack, cursor, shell icons and bar style are your preferences: they apply to every theme. GTK applications follow them at once, and Kitty reloads. Qt applications follow them when reopened. The shell reads fonts and icons only at start, so after a font or icon change the panel shows a **Restart shell** banner. The restart reopens the panel on the same tab; open notifications stay in the history as archived entries.

## Themes

The palette above is the **Graphite** theme. Seven more ship with the dotfiles; all are dark except Glass Light:

| Theme | Accent | GSettings accent | VS Code |
| --- | --- | --- | --- |
| `catppuccin-mocha` | mauve `#cba6f7` | purple | Catppuccin Mocha |
| `tokyo-night` | blue `#7aa2f7` | blue | Tokyo Night |
| `gruvbox` | yellow `#fabd2f` | yellow | Gruvbox Dark Medium |
| `everforest` | green `#a7c080` | green | Everforest Dark |
| `glass` | blue `#4da3ff` | blue | Default Dark Modern |
| `glass-light` | blue `#006be0` | blue | Default Light Modern |
| `high-contrast` | yellow `#ffd400` | yellow | Default High Contrast |

**Glass** and **Glass Light** are the macOS-style pair. Their panels are mostly glass: the card under a panel, the dock and the OSD keep about 30% (dark) or 40% (light) of their fill instead of 85%, tiles and hover states are a thin white veil instead of a second dark layer, popup notifications get a denser fill of their own (`shell.notice`, 72% dark and 80% light, while other themes keep `raised`) so their text reads over any page, and the stroke is brighter, with an 82–85% terminal and `glassStyle = "liquid"`: Hyprglass draws a lens rim that bends and mirrors what is around each card, toast and menu, a thin lit bevel and a little dispersion on the rim, over a flat, lightly frosted center ([plugins](../guide/plugins.md#behavior)). Without Hyprglass loaded they keep Hyprland's native blur and stay readable, only flatter. Both use the local wallpaper folders, like Graphite; glass shows best over a colourful wallpaper.

**High Contrast** is for reading comfort: black surfaces, white text, a yellow accent, opaque panels and terminal, a 32 px cursor, an 11 pt interface font and 2 px window borders (yellow on the active window, white on the others; a border width chosen in the panel wins). It uses the local wallpaper folders.

Graphite uses VS Code's own Default Dark Modern. Their surfaces and terminal colours come from each project's published palette and Kitty port.

A theme is one `theme.json` with:
- `mode`, `fonts` and `system` (GTK, icon and cursor theme, GSettings accent);
- `shell` (the `Theme.qml` tokens);
- `palette` (the semantic colours the application templates use);
- `ansi` (16 terminal colours), `terminal.opacity`;
- `hyprland` (shadow, Hyprglass tint, `glassStyle`: `desktop` or `liquid`).

- `vscode` (`theme`, optional `extension`).

Only `palette` (bg, base, raised, border, fg, muted, dim, accent, accentFg, link, danger, success, warning) and `ansi` are required. `theme.py` derives any missing value from them, and explicit values always win:
- the `shell` tokens, with Graphite's alphas;
- the Qt bevel shades;
- the Hyprland shadow and glass tint; `glassStyle` defaults to `desktop`.

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

Each consumer keeps Graphite as its fallback, so a missing state directory changes nothing. GTK is the exception: it falls back to plain adw-gtk3-dark until the next `desktop-theme` run.

Other applications:
- **VS Code:** `desktop-theme set` replaces (or adds) `workbench.colorTheme` and the preferred theme for the mode in `~/.config/Code/User/settings.json`. The preferred key is `workbench.preferredDarkColorTheme` or `workbench.preferredLightColorTheme`; VS Code uses it instead of `colorTheme` while `window.autoDetectColorScheme` is on, as it is here. The edit is targeted and leaves the rest of the file alone, and VS Code applies it live.
  - It is skipped when the theme's extension is not installed or the file is not valid JSON.
  - The four extensions are Catppuccin.catppuccin-vsc, enkia.tokyo-night, jdinhlife.gruvbox and sainnhe.everforest.
  - Before the themes, `workbench.colorTheme` was unset (Default Dark Modern).
- **btop:** every theme, Graphite included, is written to `~/.config/btop/themes/desktop.theme`. `btop.conf` gets `color_theme = "desktop"`, and a running btop reloads on `SIGUSR2`.
  - The main background stays empty, so the translucent Kitty background shows through.
  - btop rewrites `btop.conf` on exit, so it is not stowed. Set `color_theme = "Default"` to go back.
- **Herdr app** ([herdr](https://herdr.dev/), the console with herdr installed): when `~/.config/herdr-app` exists, every theme is written to `themes/desktop.json` there (the terminal colors and 16 ANSI colors, and the panel colors by herdr's names: `canvas`, `chrome`, `surface`, `raised`, `border`, `accent`, the agent states…), and `settings.json` gets `theme: "desktop"`, the monospace font and size (points × 4/3, herdr counts pixels) and the interface font. A key is changed only while unset or still the value written last time (`~/.local/state/desktop-theme/herdr-app.json`), so a theme or font picked in Herdr stays; a `settings.json` that does not parse is left alone. Herdr reloads both live. Before Herdr's first start, which creates that folder, `desktop-ai` runs `theme.py herdr`, so it opens in the desktop theme.
  - Herdr's **main** layout ("Herdr") has no look of its own and follows at once. Layouts that bring their own (**Terminals**, Herdr 98) set fixed colors that win over any theme: duplicate one (`herdr-app do layout.clone '{"name":"terminals","as":"desktop"}'`, or *Duplicate layout* in its palette), remove `colors` and `background` from the copy's root in `layouts/desktop.json` and set `"theme": "desktop"`; it then follows the desktop like main.
- **Zen and other portal-aware apps** follow the `color-scheme` that `mode` sets (all shipped themes are dark; the dynamic one can be light).

Preferences: `~/.local/state/desktop-theme/preferences.json` holds what is chosen in the Theming panel, or with these commands:
- `desktop-theme font --sans F --mono F --size N --unified on|off` (`--default` clears them). `--unified on` makes the interface use the monospace family.
- `desktop-theme icon-theme NAME|default`.
- `desktop-theme cursor [--theme NAME|default] [--size 24|32|40|48]` / `--default`: the cursor, saved as `cursor` in `preferences.json`; `theme.py cursors` lists the installed themes.
- `desktop-theme shell-icons desktop|pack`: the shell glyphs from `assets/icons`, or the icon pack's symbolic icons mapped in `components/IconNames.js`.
- `desktop-theme bar-style shade|transparent|toggle`.
- `desktop-theme reduce-effects on|off|toggle`: saved as `reduceEffects` in `preferences.json`.
- `desktop-theme glass --option OPTION --value N` / `--reset`: the glass tuning of the current theme, saved under `glass.<theme>` in `preferences.json` (only values that differ from the default). `GLASS_TUNING` in `theme.py` lists the options with their defaults (the `liquid` preset in `plugins.lua`, checked by `test_theme.py`) and ranges; values are clamped to them. They are rendered into `hyprland.lua` as `glassTuning`, and `plugins.lua` lays them over the preset. A theme without liquid glass refuses the command.
- `desktop-theme window-style --rounding N --border N --gaps-in N --gaps-out N` (`--default` clears them). Hyprland `decoration.rounding`, `general.border_size`, `general.gaps_in` and `general.gaps_out`, defaulting to 16, 0, 4 and 4. The border colours (`general.col.active_border` / `inactive_border`) are the theme's accent and border colours, rendered into `hyprland.lua` and applied with `hyprctl reload`. The same rounding reaches Quickshell as `rounding` in `quickshell.json`: `Theme.radius`, used by `Card`, the dock, the OSD, popup notifications, `PopupMenu` and the tray menu, is the rounding itself; `Theme.corner(n)` scales the radii inside them by rounding/16. Radii under 6 (dots, tracks) are not scaled. hyprlock gets `rounding = 26 × rounding/16` for its password field. The border width and both colours reach Quickshell as `borderSize`, `activeBorder` and `inactiveBorder`. While `borderSize` is above 0, `Theme.frameWidth` and `Theme.frameActive` frame `Card` (every panel), `PopupMenu` and the tray menu, and `Theme.frameInactive` frames the dock, the OSD and notification popups. At 0 they keep a 1 px `stroke`, and popups none.

The bar style, shell icon source and Reduce effects reach Quickshell through `quickshell.json` (`barStyle`, `iconSource`, `reduceEffects`); Reduce effects reaches Hyprland through the rendered `hyprland.lua` (`reduceEffects`, read by `appearance.lua` and `plugins.lua`).

`theme.py tone` measures the strip under the bar on the current wallpaper. It crops the wallpaper to the focused monitor's logical size as hyprpaper does (cover), takes the mean grey of the top 4%, and caches it in `tone.json`.

Text and icons then use whichever of the current theme's two text colours (`shell.text`, `shell.accentText`) has the higher WCAG contrast with that strip. The bar background stays transparent. `services/BarStyle.qml` runs it whenever the wallpaper or the bar style changes. Since one mean cannot fit a strip that is bright on one side and dark on the other, the bar row is drawn through a `MultiEffect` shadow with no offset in the other text colour (`BarStyle.halo`): over a backdrop the chosen colour already suits it hardly shows, elsewhere it outlines text and icons. The Shaded bar has no halo.

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
- **System:** adw-gtk3 or adw-gtk3-dark, Papirus-Dark or Papirus-Light, the GSettings accent nearest to the primary hue (slate when it is grey), VS Code Default Dark Modern or Default Light Modern.
- **Light mode:** the bar shade uses bg at 60%/53% instead of black, so its dark text stays readable. This applies to any theme with `"mode": "light"` that does not set `barShadeTop`/`barShadeBottom`.
- `wallpaperDirectories` is the image's folder, so `Super + Ctrl + W` cycles it.

`desktop-theme dynamic --mode auto|dark|light` stores `dynamic` in `preferences.json` (matugen `-m smart|dark|light`, always with `-t scheme-tonal-spot`) and regenerates when the dynamic theme is current. `services/DynamicTheme.qml` watches `current.json`, the wallpaper selection and the generated theme: while the theme is `dynamic` and the wallpaper is not its `source`, it runs `theme.py generate`, one run at a time.

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

The palette uses graphite gray, neutral primary `#d4d6dc`, light text, Adwaita Sans, and Papirus-Dark icons. GTK, Qt, and hyprlock share the palette; GSettings uses the slate accent. GTK 3 uses adw-gtk3-dark (`adw-gtk3-theme`: Fedora 44 no longer ships the GTK 3 Adwaita-dark, and GTK 3 falls back to light Adwaita for a theme it cannot find) and CSS colors; GTK 4/libadwaita receives the dark preference through GSettings/the portal and named colors. Qt Widgets uses Fusion and custom palettes for both generations. The installed qt6ct plugin also accepts `qt5ct`, so `QT_QPA_PLATFORMTHEME=qt5ct` covers Qt 5/6. Qt Quick Controls uses Basic; applications with their own styling may ignore these preferences.

`desktop-theme` applies GSettings and imports Qt variables into D-Bus/systemd; on its first run it saves previous values to `~/.local/state/dotfiles/interface-before-theme.ini`. Restart open applications to adopt the theme; the next login also applies the full environment. Flatpak applications depend on sandbox runtimes/themes and may not follow every CSS override.
