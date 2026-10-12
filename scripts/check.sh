#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for script in "$repo"/shell/.local/bin/*; do bash -n "$script"; done
python3 - "$repo/scripts/stow.py" <<'PY'
import ast, pathlib, sys
ast.parse(pathlib.Path(sys.argv[1]).read_text())
PY
XDG_CONFIG_HOME="$repo/hypr/.config" Hyprland --verify-config -c "$repo/hypr/.config/hypr/hyprland.lua"
printf '\nPer verificare QML nella sessione: qs -p "%s/quickshell/.config/quickshell/desktop"\n' "$repo"
