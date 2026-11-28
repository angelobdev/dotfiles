# Bar

[← Docs](../README.md)

The bar is made of widgets in five sections: **left**, **center left**, **center**, **center right** and **right**. Center left, center and center right sit side by side as one block, centred on the screen; the free room lies between the left section and that block, and between the block and the right section. The window title takes whatever its section has left and is cut with an ellipsis. When one side holds too much for the block to stay centred, the block moves away from it.

Without a layout of your own the bar is the **classic** one, item for item the bar before layouts: launcher, workspaces and window title on the left; tray, media, privacy, recording, reminders (added since, shown only while one is pending), battery, updates, assistant, shortcuts, notifications, Control Center, clock and session on the right.

## Widgets

| Id | Shows | Click |
| --- | --- | --- |
| `launcher` | The distribution logo | Launcher |
| `workspaces` | The workspaces of the monitor ([workspaces](../guide/interface.md#workspaces-per-monitor)), the focused one with the glyph of its layout when not tiling | Focuses one; on the focused one, the next layout; the wheel moves |
| `title` | The active window; on a narrow bar or in tablet mode, its app icon | Right click or long press: window menu |
| `globalMenu` | The menu of the app of this monitor: its own (File, Edit, View…) or a generic one ([global menu](#global-menu)); in no layout until you add it | A menu opens below it; right click: its options |
| `tray` | The status icons of apps | Their menus |
| `media` | What plays (with `barMedia`) | Play/pause; wheel skips; right click Control Center |
| `privacy` | Microphone, camera or screen sharing in use | — |
| `recording` | The time of a screen recording | Stops it |
| `reminders` | The minutes to the next reminder, while one is pending | The Reminders dialog |
| `battery` | Charge, power profile | Battery panel |
| `updates` | The number of updates waiting | Updates panel |
| `assistant` | The state of the coding agent | Its panel |
| `hints` | — | Shortcuts |
| `notifications` | The bell, Do Not Disturb, a focus session | Notifications |
| `controls` | — | Control Center |
| `clock` | Date and time, in one of five formats (`barClockFormat`) | Calendar; right click: the next format |
| `power` | — | Session menu |
| `weather` | Temperature and conditions (with `weatherEnabled`), refreshed every 30 minutes | Calendar |
| `volume` | The output volume | Sound panel; wheel ±5%; middle click mutes |
| `network` | Wi-Fi strength or cable | Network panel |
| `keyboardLayout` | The input layout in use, as its code | Next layout |
| `separator` | A thin line | — |
| `spacer` | 24 px of empty room | — |

Widgets that have nothing to show (no player, no updates, no battery) stay hidden. Only the separator and the spacer can appear more than once.

## Global menu

The `globalMenu` widget puts the menus of the app on the bar, as on macOS, after [Oma Top Menu](https://github.com/Somnius/oma.top.menu) (MIT), whose reading of menus it follows. Each monitor shows the menu of its own window: the focused window on the monitor in use, elsewhere the window last used on the workspace that monitor shows; a monitor without a window shows none.

- **An app with a menu of its own** shows its icon and its menus, read from the app: Firefox **File Edit View History Bookmarks Tools Help**, VS Code **File Edit Selection View Go Run Terminal Help**. A click opens one below it, with each entry's shortcut on the right; a submenu opens in the same menu, under a row that goes back.
- **An app without one** shows its icon, its name and a generic menu: the name (**New window**, the actions of its desktop entry, **Close window**, **Quit**), **File**, **Edit** (Undo, Redo, Cut, Copy, Paste, Select all, sent to the window as their keys), **View** (floating, fullscreen, maximize, pop out, transparency), **Window** (to the previous or next workspace, move left, right, up, down, close) and **Help** (the keyboard shortcuts, the launcher). Or nothing, as an option.
- `↑↓` select, Enter runs, `→` opens a submenu, `←` goes back, and `←` `→` on the top level move to the menu beside it.
- **A right click** on the menu opens its options (**Global menu**, also `desktop-shell toggle globalmenu`): **Focus** (System keeps your Hyprland setting; Hover, Click and Off set `input:follow_mouse` to 1, 2 or 0 while the widget is on a bar, again after each reload, never in a file: with Hover the menu changes as the pointer crosses windows on the way to the bar), **Apps without a menu** (generic menu or nothing), **App icon**, and the apps to start under X11.

Where a menu comes from, in this order (`globalmenu_reader.py`):

1. `com.canonical.dbusmenu` through the registrar, for X11 apps: Electron apps under XWayland, such as VS Code, which hand their menu over only under X11 (below).
2. `org.gtk.Menus`, for GTK apps that publish their menu bar.
3. `com.canonical.dbusmenu` an app publishes itself (Qt).
4. The accessibility tree (AT-SPI): the menu bar of the window as a screen reader sees it, which covers Firefox and its family, Qt and GTK 3 apps on Wayland. While the widget is on a bar the reader keeps accessibility on for the session, registered as a screen reader is; **an app already open before shows its menu once it is restarted**. Firefox fills a menu only once it has been open: the first time, the menu opens inside Firefox for a moment, is read and closed again (two Escapes sent to its window), and its entries show on the bar; after that it opens at once.

Without any of them, the generic menu. GTK 4 and libadwaita apps, terminals and Herdr have no menu bar, so they get it too.

**Apps under X11.** When the widget is added the shell asks which apps to start under X11 for it: the installed Electron apps, each with a switch. **Apply** changes their launchers (`electron.py`, `--ozone-platform=x11` in place of the Wayland flags); an app already open keeps running as it is until it is restarted. Under X11 an app loses a few Wayland features (in tablet mode the on-screen keyboard no longer opens by itself in it) and stays sharp, as XWayland renders at full resolution with the DPI of the monitor's scale.

- VS Code exports its menu only with its native title bar and menus: choosing it also sets `"window.titleBarStyle": "native"`, `"window.menuStyle": "native"` and `"window.menuBarVisibility": "toggle"` (its own menu bar on Alt) in `~/.config/Code/User/settings.json`, edited in place (comments and trailing commas kept). The values found before are kept in `~/.local/state/desktop-shell/globalmenu.json` and put back when VS Code leaves the global menu.
- While the widget is on a bar, `desktop-globalmenu.service` (a user service, so a shell restart keeps the menus of the open X11 apps) is the registrar, and `globalmenu.py watch` reads the menus. Taking the widget off the bar stops both, turns accessibility back off and starts the chosen apps under Wayland again, their settings as they were; the choice is kept (`~/.config/desktop/global-menu-apps.conf`).
- An X11 app registers its menu when its window opens, with the registrar already there: one opened before the widget was added shows its menu once restarted.

## Editing

- **Hold Super** with the pointer on a bar for a moment (200 ms, without pressing another key): that bar becomes editable. Each section gets an outline, its name and widget count below it, and a **+** at its end; empty sections show as slots, and hidden widgets show dimmed so they can be placed too. Releasing Super saves; **Esc** drops the changes.
- **Drag** a widget (still holding Super) to move it: a bar marks where it lands. Dropping it on **Drop here to remove from the bar**, which appears below the bar, takes it off; dropping it anywhere else leaves it where it was.
- **Super + right click** on a widget opens its menu: move it to another section, add a widget beside it, remove it.
- **+** opens the gallery of the widgets not on the bar, with the section **Add** puts them in; a card can also be dragged to its place. Opening the gallery keeps the bar in editing after Super is released, until **Done** (or **Cancel**, Esc, or a press outside the bar).
- **Right click** (or a long press) on an empty part of the bar opens the bar menu: **Edit layout** (editing without holding Super, ended with Done), the **Classic**, **Centered** and **Minimal** layouts, and with the pills style **One pill for the center**. A layout chosen there is saved at once.
- `desktop-shell bar edit` edits the bar of the focused monitor (as Edit layout does), `bar done` saves, `bar cancel` drops, `bar reset` goes back to the classic layout.

While Super is held over the bar, Hyprland turns off its `Super + left/right drag` window binds (`config/binds.lua`), so the presses reach the bar; they come back when Super is released. The windows do not move: the bar grows down the screen only while it is edited, and reserves the same height.

## Backgrounds

Settings → Appearance → Theme, **Bar**, or a double click on an empty part of the bar, which steps through them:

- **Shaded**: the dark gradient across the whole width (the default).
- **Floating**: a rounded surface away from the screen edges: by the screen margin of the windows (**Settings → Appearance → Layout**, Hyprland `gaps_out`), so it lines up with them; the windows keep that margin from the bar too.
- **Pills**: one rounded surface per section that shows, with the same margins as Floating; with **One pill for the center** (Settings → Desktop → Bar, or the bar menu) center left, center and center right share one.
- **Transparent**: no surface; text and icons take the theme text colour that contrasts more with the wallpaper, with a soft halo ([theming](theming.md)).

Floating and pills reserve that margin more at the top, and panels, notifications and the assist button open that much lower.

## Configuration

`~/.config/desktop/shell.json`:

- `barLayout`: the widget ids of each section, as `{"left": ["launcher", "workspaces"], "centerLeft": ["media"], "center": ["clock"], "centerRight": ["weather"], "right": ["tray", "network", "volume", "battery", "notifications", "controls", "power"]}`. Editing writes it, and removes it again when the layout is the classic one. Unknown ids are skipped, and a widget that cannot repeat is kept where it first appears; an object with none of the five sections is the classic layout.
- `barMergeCenter: false`: one pill for the center block.
- `barMedia: true`: whether the media widget shows what plays.
- `barClockFormat: "default"`: the clock's format: `default` (date and time), `time`, `seconds`, `weekday` (day name and time) or `iso` (`2026-11-27  14:32`). Built from the catalog's date format and the locale's time format, so it follows the language and the 12 or 24 hours; a right click on the clock and Settings → Desktop → Bar (with each format shown as the clock now) change it.
- `Super + B` hides and shows every bar for the session (`desktop-shell bar hide|show|toggle`); the full-screen desktop (`Super + Ctrl + Alt + F`) hides them too.

The style is a theme preference (`desktop-theme bar-style shade|floating|pills|transparent|toggle`).

## Files

- `bar/Bar.qml`: the window, the sections, the backgrounds and the edit mode (drag, outlines, trash, the bar and widget menus).
- `bar/BarSection.qml`: one section, its widgets loaded from `bar/widgets/`.
- `bar/widgets/Registry.js`: every widget, its file and glyph; `bar/widgets/*Widget.qml`, one per widget, each with a `bar` and a `shown` property.
- `bar/BarLayoutModel.js`: the sections, the presets, moving and centring (tested by `scripts/tests/tst_bar_layout.qml`).
- `services/BarLayout.qml`: the saved layout, the draft while editing, the custom events from Hyprland and `desktop-shell bar`.
- `bar/BarGallery.qml`, `bar/BarMenuWindow.qml`: the gallery and the menus.
- `bar/widgets/GlobalMenuWidget.qml`, `bar/GlobalMenuWindow.qml`, `services/GlobalMenu.qml`, `panels/GlobalMenuPanel.qml`, `shell/.local/libexec/desktop/globalmenu.py` and `globalmenu_reader.py` (tested by `scripts/tests/test_globalmenu.py`) and `desktop-globalmenu.service`: the global menu.
