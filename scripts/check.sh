#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for script in "$repo"/shell/.local/bin/*; do bash -n "$script"; done
python3 - "$repo/scripts/stow.py" "$repo/scripts/install-hypr-plugins.py" "$repo/scripts/hyprpm/build.py" "$repo"/shell/.local/libexec/desktop/*.py <<'PY'
import ast, pathlib, sys
for path in sys.argv[1:]:
    ast.parse(pathlib.Path(path).read_text())
PY
XDG_CONFIG_HOME="$repo/hypr/.config" Hyprland --verify-config -c "$repo/hypr/.config/hypr/hyprland.lua"
printf '\nPer verificare QML nella sessione: qs -p "%s/quickshell/.config/quickshell/desktop"\n' "$repo"
