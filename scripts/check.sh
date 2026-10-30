#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
for script in "$repo"/shell/.local/bin/*; do bash -n "$script"; done
bash -n "$repo/scripts/tablet-auth.sh"
# compile() also catches errors ast.parse accepts (e.g. return outside a function); it writes no bytecode.
python3 - "$repo/scripts/stow.py" "$repo/scripts/install-hypr-plugins.py" "$repo/scripts/check-i18n.py" "$repo/scripts/check-links.py" "$repo"/scripts/tests/test_*.py "$repo/scripts/hyprpm/build.py" "$repo"/shell/.local/libexec/desktop/*.py "$repo/shell/.local/libexec/desktop/steamrt-ui/_v2-entry-point" <<'PY'
import pathlib, sys
for path in sys.argv[1:]:
    compile(pathlib.Path(path).read_text(encoding='utf-8'), path, 'exec')
PY
python3 "$repo/scripts/check-i18n.py"
# Needs python3-cmarkgfm, the Markdown engine GitHub uses.
if python3 -c 'import cmarkgfm' 2>/dev/null; then
    python3 "$repo/scripts/check-links.py"
fi
for test in "$repo"/scripts/tests/test_*.py; do python3 "$test"; done
# Same flags gaming.py uses when it caches the Steam UI library.
if command -v cc >/dev/null; then
    cc -Wall -Wextra -Werror -shared -fPIC -O2 -o /dev/null "$repo/shell/.local/libexec/desktop/steam-scale.c" -ldl
fi
if command -v desktop-file-validate >/dev/null; then
    desktop-file-validate --no-hints "$repo"/shell/.local/share/applications/*.desktop
fi
# Quickshell ships no qmltypes: skip type-resolution categories, keep syntax and QML errors.
qmllint=/usr/lib64/qt6/bin/qmllint
if [[ -x $qmllint ]]; then
    find "$repo/quickshell/.config/quickshell/desktop" -name '*.qml' -print0 |
        xargs -0 "$qmllint" --import disable --unqualified disable --unresolved-type disable \
            --required disable --missing-property disable --incompatible-type disable --unused-imports disable
fi
# Pure JS helpers of the shell (dock layout); offscreen, no compositor needed.
qmltestrunner=/usr/lib64/qt6/bin/qmltestrunner
if [[ -x $qmltestrunner ]]; then
    QT_QPA_PLATFORM=offscreen "$qmltestrunner" -silent -input "$repo/scripts/tests"
fi
XDG_CONFIG_HOME="$repo/hypr/.config" Hyprland --verify-config -c "$repo/hypr/.config/hypr/hyprland.lua"
printf '\nTo check QML in the session: qs -p "%s/quickshell/.config/quickshell/desktop"\n' "$repo"
