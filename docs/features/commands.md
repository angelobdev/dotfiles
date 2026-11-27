# Commands

[← Docs](../README.md)

The launcher (`Super + Space`, or a right click on the empty desktop) reaches the apps and everything the desktop can do, from the keyboard alone. How it is used is in the [interface guide](../guide/interface.md#commands); this page is what it is made of and how to add your own.

## What it lists

The first level is always the same: the categories of `quickshell/.config/quickshell/desktop/commands.json`, in its order.

| Category | Holds |
| --- | --- |
| Apps | Every app, as the launcher listed them before the commands: the ones you open most and most lately first |
| Toggles | Keep awake, Do Not Disturb, focus session, night shift, the bar, zoom, rotation lock, the on-screen keyboard, each with its switch |
| Appearance | The theme and the bar background (choices), the theme and wallpaper switchers, the next wallpaper, editing the bar |
| Windows & workspaces | The layout of the workspace (a choice), floating, fullscreen, maximize, the window tricks, closing the window |
| Tools | Clipboard, emoji, reminders, color picker, QR codes, screen recording, notifications, calendar, the shortcuts sheet, the assistant and the radio where installed |
| System | Lock, suspend, log out, restart (Alt: restart to the firmware setup), shut down, the power profile and the sound output (choices), the panels |
| Updates | The updates panel, restarting to finish them, What's new |
| Settings | Every section, tab and option of Settings, from the index of its own search: Enter opens Settings there, the option scrolled to and selected |
| Shortcuts | Every described shortcut of the Hyprland config that no command above stands for (Terminal, Browser, Workspace 3, Move left…): Enter does what the key does |

Typing on the first level searches the apps and every command, the rows of Settings and Shortcuts included; inside a category, only what it holds. A command found by a search says on its right where it is, and one with a shortcut shows its keys.

## Commands as data

Each entry of `commands.json` is keyed by a dotted id, its place in the tree: `system.reboot` is in `system`. An entry with an action is a command, one with `rows` gets its entries from the shell, anything else is a category.

| Field | Meaning |
| --- | --- |
| `label` | A catalog key (both catalogs); your own entries take plain text |
| `icon` | A shell glyph (`quickshell/.config/quickshell/desktop/assets/icons/`) |
| `panel` | Opens a panel, by the names of `desktop-shell toggle` |
| `settings` | Opens Settings on a section, or `section/tab` |
| `session` | `lock`, `suspend`, `logout`, `reboot`, `poweroff`, `firmware`; all but lock ask first in the session menu |
| `call` | `[name, argument]`: a service of the shell, as its IPC reaches it (`keepAwake`, `quiet`, `focus`, `nightShift`, `bar`, `zoom`, `rotationLock`, `keyboard`) |
| `run` | A command as a list of words, never a shell string; `desktop-…` is looked up in `~/.local/bin`, `~/` is the home folder |
| `rows` | A provider: `apps`, `themes`, `barStyles`, `workspaceLayouts`, `powerProfiles`, `audioOutputs`, `settings`, `shortcuts` |
| `state` | A switch, on while that state holds; Enter flips it and the launcher stays open |
| `when` | Shown only while that state holds |
| `enabled` | Dimmed while it does not hold, with `reason` (a catalog key) beside it |
| `alt` | The id of the command that takes its place while Alt is held |
| `bind` | The description of its Hyprland bind (as in `config/binds.lua`): its keys show beside it |
| `requires` | A program that must be installed (looked up once, `~/.local/bin` included) |
| `hidden` | `true` leaves it out |

States are properties of the shell's services, never a process per check: `keepAwake`, `quiet`, `focus`, `nightShift`, `nightShiftAvailable`, `bar`, `zoom`, `rotation`, `rotationLock`, `touchscreen`, `onScreenKeyboard`, `battery`, `efi`, `numberedWorkspace`, `restartNeeded`, `assistant`, `radio`. A condition is one name, `!name` for its opposite, or a list of them that must all hold.

`scripts/check-i18n.py` checks every label, reason and glyph, one action at most per entry, every `alt`, and every `bind` against the Hyprland config.

## Your own commands

`~/.config/desktop/commands.json` (outside the repository) is laid over the desktop's by id:

```json
{
  "mine": { "label": "Mine", "icon": "pin" },
  "mine.vpn": { "label": "Work VPN", "icon": "vpn", "run": ["nmcli", "connection", "up", "work"], "requires": "nmcli" },
  "mine.notes": { "label": "Today's note", "run": ["kitty", "nvim", "~/notes/today.md"] },
  "system.lock": { "label": "Lock it now" },
  "system.suspend": { "hidden": true }
}
```

- An id of the desktop takes your fields over its own and keeps its place: a new icon, a label of yours, `"hidden": true` to leave it out.
- A new id comes after the desktop's, a new first-level id as a category of its own (**Mine** above). Its label is shown as you wrote it.
- `requires` keeps a command out until its program is installed.
- The file is read again when it changes. One that is not valid JSON is left out whole, with a notification, and the desktop's commands stay.

## From scripts

`desktop-shell commands` opens the launcher on the first level, `desktop-shell commands ID` on a category (`system`, `apps`, `settings`) or runs a command or a row (`toggles.keepAwake`, `appearance.barStyle.pills`, `settings.desktop-barclockformat`). A row's id is its category's id, a dot, then its value in lower case with every other character run turned into `-`.

## Files

- `quickshell/.config/quickshell/desktop/commands.json`: the commands of the desktop.
- `services/CommandModel.js`: the tree, the conditions, merging your file, the search (tested by `scripts/tests/tst_command_model.qml`).
- `services/Commands.qml`: the states, the rows of each provider, the keys of the binds (`hyprctl binds`), running a command.
- `panels/Launcher.qml`: the list, the category label, the keys.
- `hypr/.config/hypr/config/util.lua`: `desktop_run_bind(description)`, what a Shortcuts row runs; `config/binds.lua` `desktop_window_trick(name)` and `config/workspace_layouts.lua` `desktop_workspace_layout_set(mode)`.
