#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for script in "$repo"/shell/.local/bin/*; do bash -n "$script"; done
python3 - "$repo/scripts/stow.py" "$repo/scripts/install-hypr-plugins.py" "$repo/scripts/hyprpm/build.py" "$repo"/shell/.local/libexec/desktop/*.py "$repo/shell/.local/libexec/desktop/steamrt-ui/_v2-entry-point" <<'PY'
import ast, pathlib, sys
for path in sys.argv[1:]:
    ast.parse(pathlib.Path(path).read_text())
PY
python3 "$repo/scripts/check-i18n.py"
XDG_CONFIG_HOME="$repo/hypr/.config" Hyprland --verify-config -c "$repo/hypr/.config/hypr/hyprland.lua"
printf '\nTo check QML in the session: qs -p "%s/quickshell/.config/quickshell/desktop"\n' "$repo"
