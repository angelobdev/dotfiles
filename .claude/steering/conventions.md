# Conventions

[← CLAUDE.md](../CLAUDE.md)

Match the surrounding code. Comments are sparse one-liners that explain *why* ("Only scan while the user is looking at the network panel"), never what.

## QML / JS

- Formatting is `qmlformat` (Qt 6) output: 4-space indent, braces on multi-line blocks, a single-statement `if` body on the next line. Check with `/usr/lib64/qt6/bin/qmlformat FILE | diff FILE -`.
- The document root has `id: root` (`bar` in `Bar.qml`); child ids are lowerCamel. Files are PascalCase; services are nouns (`Audio`, `Clipboard`).
- Member order: `id`, properties (required, writable, readonly derived), signals and functions, property assignments and handlers, non-visual children (`Process`, `Timer`, `Connections`), then visual children.
- Imports: QtQuick modules, Quickshell modules, then relative `".."`, `"../components"`, `"../services"`. Do not keep unused imports (`check.sh` runs qmllint; for unused-import detection run qmllint without the disabled categories on the changed files).
- Delegates declare `required property var modelData` (and `index`) and qualify access through an id (`trayItem.modelData`).
- JS uses `===`/`!==`, `?.`/`??`, double-quoted strings, arrow handlers (`onExited: (code, status) => {…}`). Replace arrays/objects instead of mutating them so bindings notice (`Object.assign({}, …)`, `filter`, `concat`).
- `textFormat: Text.PlainText` on any `Text` showing external data; markup only through `NotificationText.styled`.
- Colours come from `Theme` (including scrims, tooltip and slider-handle tokens). Radii and font sizes are still literals; there is no type scale yet.
- Keep idle work gated: timers and scans run only while their panel is open (`ShellState.panel === "<name>"`) or their feature is enabled. Coalesce repeated requests with `Qt.callLater` or a `pending/again` flag.
- Do not try to override an `Overlay` handler from a panel: QML runs both the base and the derived handler.
- JS libraries use `.pragma library`.

## Python helpers

- `#!/usr/bin/env python3`, a one-line module docstring (reused as the argparse description), `from i18n import tr` first, then stdlib imports alphabetically by module (`from pathlib import Path` in its sorted position).
- Single quotes, 4 spaces, two blank lines between top-level definitions, no type hints.
- `main()` returns an exit code; `if __name__ == '__main__':` wraps it in `try: sys.exit(main()) except (OSError, ValueError, subprocess.CalledProcessError)` and prints a translated message to stderr.
- `subprocess` always with argument lists (never `shell=True`), with timeouts on interactive paths.
- Atomic writes through `tempfile.mkstemp` + `os.replace`; `os.umask(0o077)` for private data; `ensure_ascii=False` and `encoding='utf-8'` for JSON.
- Exceptions: `scripts/*` developer tools and `gaming.py` print plain English.

## Bash wrappers

- `#!/usr/bin/env bash` + `set -euo pipefail`, 4-space indent, `[[ ]]`, quoted expansions, `$EUID` rather than `$(id -u)`.
- Subcommands through `case "${1:-default}"`; usage errors to stderr with exit 2; the final command is `exec`'d.
- Absolute `$HOME/.local/...` paths; serialize with `exec 9>lock; flock 9` and close fd 9 in long-lived children.

## Hyprland Lua

- Every bind goes through `bind(keys, dispatcher, description, flags)`. The English description is also the Hints lookup key (mapped in `i18n/Sources.js`), so keep descriptions byte-identical or update the mapping and both catalogs.
- User-facing errors from Lua use `python3 ~/.local/libexec/desktop/i18n.py --notify "<title key>" "<message key>"`; `check-i18n.py` scans that literal in `binds.lua`.
- Guard plugin APIs (`hl.plugin or {}`); machine-specific settings go in `config/local.lua`.

## i18n

- Keys are nested lowerCamel paths grouped by area (`clipboard.deleteItem`), errors under `.errors.`, plurals as `.one`/`.other` used via `I18n.plural(one, other, count, args)` (`%1` = count).
- Prefer `%1`, `%2` placeholders over `…Prefix` concatenation for new sentences. Formats (dates, units) also come from the catalogs.
- Catalogs keep insertion order; add keys next to their alphabetical neighbours in both files. `check-i18n.py` checks parity, placeholders and references, not unused keys: grep before removing or after renaming.
- English source strings from external APIs (bind descriptions, network states) map to keys in `i18n/Sources.js`; unknown ones pass through unchanged.
