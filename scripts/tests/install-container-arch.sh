#!/usr/bin/env bash
# Runs install-desktop.py for real in a throwaway archlinux container, as root, on a copy of the repository.
# Files are piped in, as for install-container.sh.
#
#   git ls-files -co --exclude-standard -z | tar --null -T - -c | docker run -i --rm archlinux:latest \
#       bash -c 'mkdir /src && tar -x -C /src && exec bash /src/scripts/tests/install-container-arch.sh'
#
# Environment: PROFILES (default core,hardware,plugins), COMPILE=1 also builds the plugins (slow). apps builds the
# AUR packages with makepkg and gaming enables multilib. The container runs no systemd, so the Flatpak and login
# steps skip themselves: only a VM covers those.
set -euo pipefail

source=${1:-/src}
profiles=${PROFILES:-core,hardware,plugins}
user=ci
home=/home/$user
repo=$home/.dotfiles

section() { printf '\n== %s\n' "$*"; }
as_user() { runuser -u "$user" -- env HOME="$home" XDG_RUNTIME_DIR=/tmp/runtime "$@"; }

section 'A fresh user with sudo, as on an installed system'
# What docs/guide/installation.md asks for first; sudo is not in the base system.
pacman -Syu --noconfirm --needed sudo git python >/dev/null
useradd --create-home --groups wheel "$user"
printf '%s ALL=(ALL) NOPASSWD: ALL\n' "$user" >/etc/sudoers.d/$user
install -d -m 700 -o "$user" /tmp/runtime
cp -a "$source/." "$repo"
chown -R "$user:" "$repo"
cd "$repo"
packages() { pacman -Qq | sort -u; }
packages >/tmp/packages-before
before_shell=$(getent passwd "$user" | cut -d: -f7)
before_target=$(systemctl get-default)
cp /etc/pacman.conf /tmp/pacman.conf-before

section 'Preview changes nothing'
before=$(pacman -Q | sha256sum)
as_user ./scripts/install-desktop.py dry-run --profiles "$profiles" | grep -E '^[a-z]+: |^Warning'
[[ $before == "$(pacman -Q | sha256sum)" ]] || { echo 'dry-run changed the installed packages' >&2; exit 1; }

section "apply --profiles $profiles"
as_user ./scripts/install-desktop.py apply --profiles "$profiles"

section 'Packages that must stay out'
# By name: pacman -Q also answers for what provides it (tuned-ppd provides power-profiles-daemon).
for package in power-profiles-daemon pulseaudio jack2 gnome-keyring; do
    if [[ $(pacman -Qq "$package" 2>/dev/null) == "$package" ]]; then
        echo "$package is installed" >&2
        exit 1
    fi
done

section 'A second apply finds nothing to do'
again=$(as_user ./scripts/install-desktop.py apply --profiles "$profiles")
printf '%s\n' "$again"
grep -qx 'Nothing to do.' <<<"$again"

section 'Open questions for Arch'
pacman -Q gdm hyprland uwsm quickshell kitty matugen oo7 || true
echo "default target: $(systemctl get-default)"
echo "gdm: $(systemctl is-enabled gdm.service)"
echo "oo7-daemon for every user: $(systemctl --global is-enabled oo7-daemon.service)"
echo "Session entry: $(ls /usr/share/wayland-sessions/)"
echo 'PAM of GDM:'
grep -nE 'oo7|gnome_keyring|fprintd' /usr/lib/pam.d/gdm-password /usr/lib/pam.d/gdm-fingerprint || true
echo 'Secret portals:'
grep -ls 'org.freedesktop.impl.portal.Secret' /usr/share/xdg-desktop-portal/portals/*.portal || true
echo "Repositories: $(pacman-conf --repo-list | tr '\n' ' ')"
echo "Entries of the AUR apps: $(cd /usr/share/applications && ls | grep -iE 'zen|code|1password|onepassword' | tr '\n' ' ')"

section 'What the helpers load'
# The GObject libraries the Python helpers ask for, at the versions they ask for.
as_user python3 - <<'EOF'
import gi
for namespace, versions in (('ECal', ('2.0',)), ('EDataServer', ('1.2',)), ('ICalGLib', ('3.0', '4.0')),
                            ('Geoclue', ('2.0',)), ('Gio', ('2.0',)), ('GLibUnix', ('2.0',))):
    for version in versions:
        try:
            gi.require_version(namespace, version)
            break
        except ValueError:
            continue
    else:
        raise SystemExit(f'{namespace} {versions} is not available')
    __import__('gi.repository', fromlist=[namespace])
    print(namespace, version)
EOF
as_user python3 -c "import runpy, sys; sys.path.insert(0, '$home/.local/libexec/desktop'); sys.argv = ['calendar.py']; runpy.run_path('$home/.local/libexec/desktop/calendar.py', run_name='calendar_check')"
tesseract --list-langs 2>&1 | grep -xE 'ita|eng'
qalc --version
fd --version
ls /usr/share/unicode/emoji/emoji-test.txt /usr/share/unicode/cldr/common/annotations/it.xml /usr/share/unicode/cldr/common/annotationsDerived/it.xml

section 'check.sh on this system'
pacman -S --noconfirm --needed desktop-file-utils python-cmarkgfm qt6-declarative lua >/dev/null
as_user ./scripts/check.sh

if [[ ${COMPILE:-} == 1 ]]; then
    # build.py compiles whatever Hyprland is installed: the guard of verified builds is in bundle.py.
    section 'Compile the plugins against this Hyprland'
    as_user python3 -c "import sys; sys.path.insert(0, 'scripts/hyprpm'); import bundle; print('verified:', bundle.verify())"
    build=$(as_user mktemp -d)
    for plugin in Hyprspace hyprgrass hyprglass HyprCapture; do
        echo "-- $plugin"
        as_user bash -c "cd '$build' && python3 '$repo/scripts/hyprpm/build.py' '$plugin'" >"$build-$plugin.log" 2>&1 || {
            tail -30 "$build-$plugin.log"
            exit 1
        }
        unresolved=$(ldd "$build/out/$plugin.so" | grep -E 'not found' | grep -v 'libaquamarine\|libhypr' || true)
        [[ -z $unresolved ]] || { printf '%s\n' "$unresolved" >&2; exit 1; }
        ls -l "$build/out/$plugin.so"
    done
fi

section 'Uninstall: preview, then the system as it was'
as_user ./scripts/install-desktop.py dry-run --uninstall | grep -E '^[a-z]+: '
as_user ./scripts/install-desktop.py apply --uninstall | grep -vE '^  '
packages >/tmp/packages-after
gone=$(comm -23 /tmp/packages-before /tmp/packages-after)
[[ -z $gone ]] || { printf 'Removed with the desktop but there before it:\n%s\n' "$gone" >&2; exit 1; }
# Not undone: the upgrade step and the tools check.sh needed. Nothing the manifest names may stay.
extra=$(comm -13 /tmp/packages-before /tmp/packages-after)
printf 'Left by the upgrade and check.sh: %s\n' "$(echo $extra)"
[[ $(getent passwd "$user" | cut -d: -f7) == "$before_shell" ]] || { echo 'login shell not restored' >&2; exit 1; }
[[ $(systemctl get-default) == "$before_target" ]] || { echo 'default target not restored' >&2; exit 1; }
# sha256sum: the image has no cmp (diffutils).
[[ $(sha256sum </etc/pacman.conf) == $(sha256sum </tmp/pacman.conf-before) ]] || { echo 'pacman.conf not restored' >&2; exit 1; }
links=$(find "$home" -type l -lname "*.dotfiles/*" | head)
[[ -z $links ]] || { printf 'Links left:\n%s\n' "$links" >&2; exit 1; }
[[ ! -e $home/.cache/dotfiles/aur ]] || { echo 'AUR checkouts left' >&2; exit 1; }
grep -q '"uninstalled": true' "$home/.local/state/dotfiles/install.json" || { echo 'install record not marked as undone' >&2; exit 1; }
again=$(as_user ./scripts/install-desktop.py apply --uninstall)
grep -qx 'Nothing to do.' <<<"$again" || { printf '%s\n' "$again" >&2; exit 1; }
# A package of the manifest may stay only while something that stays needs it.
manifest=$(python3 -c 'import tomllib; t = tomllib.load(open("scripts/install/manifest.toml", "rb"))["arch"]
print("\n".join(p for profile in t.values() if isinstance(profile, dict) for p in [*profile.get("packages", ()), *(a["package"] for a in profile.get("aur", ()))]))' | sort -u)
left=$(comm -12 <(printf '%s\n' $extra | sort -u) <(grep -vxE 'python|git' <<<"$manifest") || true)
for package in $left; do
    needed=$(pacman -Qi "$package" | sed -n 's/^Required By *: //p')
    [[ $needed != None ]] || { printf 'Still installed after uninstall, and nothing needs it: %s\n' "$package" >&2; exit 1; }
    echo "Kept, still needed: $package (by $needed)"
done

section 'All good'
