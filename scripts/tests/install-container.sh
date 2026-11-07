#!/usr/bin/env bash
# Runs install-desktop.py for real in a throwaway fedora:45 container, as root, on a copy of the repository.
# Files are piped in: never mount the repository with :z, which relabels the files the live session reads.
#
#   git ls-files -co --exclude-standard -z | tar --null -T - -c | docker run -i --rm fedora:45 \
#       bash -c 'mkdir /src && tar -x -C /src && exec bash /src/scripts/tests/install-container.sh'
#
# Environment: PROFILES (default core,hardware,tablet,plugins,herdr), COMPILE=1 also builds the plugins (slow), BASE_EXTRA lists
# packages the system has before the installer (ffmpeg-free makes the swaps run, and their undoing). The container
# has no systemd, so the firewall, Flatpak and login steps skip themselves: only a VM covers those.
set -euo pipefail

source=${1:-/src}
profiles=${PROFILES:-core,hardware,tablet,plugins,herdr}
user=ci
home=/home/$user
repo=$home/.dotfiles

section() { printf '\n== %s\n' "$*"; }
as_user() { runuser -u "$user" -- env HOME="$home" XDG_RUNTIME_DIR=/tmp/runtime "$@"; }

section 'A fresh user with sudo, as on an installed system'
# As on a released Fedora. A pre-release image has this on, until the upgrade step brings a fedora-repos that turns
# it off: what it installed is then newer than any repository, and dnf downgrades glibc mid-transaction.
install -d /etc/dnf/repos.override.d
printf '[updates-testing]\nenabled=0\n' >/etc/dnf/repos.override.d/90-install-test.repo
dnf -y -q install sudo shadow-utils util-linux git-core python3 authselect
# Prove the manifest is explicit: nothing may depend on a weak dependency being installed.
install -d /etc/dnf/libdnf5.conf.d
printf '[main]\ninstall_weak_deps=False\n' >/etc/dnf/libdnf5.conf.d/90-install-test.conf
[[ -z ${BASE_EXTRA:-} ]] || dnf -y -q install $BASE_EXTRA
useradd --create-home --groups wheel "$user"
printf '%s ALL=(ALL) NOPASSWD: ALL\n' "$user" >/etc/sudoers.d/$user
install -d -m 700 -o "$user" /tmp/runtime
cp -a "$source/." "$repo"
chown -R "$user:" "$repo"
authselect select local --force >/dev/null
cd "$repo"
packages() { rpm -qa --qf '%{NAME}.%{ARCH}\n' | sort -u; }
packages >/tmp/packages-before
before_shell=$(getent passwd "$user" | cut -d: -f7)
before_auth=$(authselect current --raw)
# The container starts without systemd, which the installer brings: until then the target is Fedora's default,
# the one systemctl reports once it is there (the container has no default.target link of its own).
before_target=$(command -v systemctl >/dev/null && systemctl get-default || echo graphical.target)

section 'Preview changes nothing'
before=$(rpm -qa | sort | sha256sum)
as_user ./scripts/install-desktop.py dry-run --profiles "$profiles" | grep -E '^[a-z]+: |^Warning'
[[ $before == "$(rpm -qa | sort | sha256sum)" ]] || { echo 'dry-run changed the installed packages' >&2; exit 1; }

section "apply --profiles $profiles"
as_user ./scripts/install-desktop.py apply --profiles "$profiles"

section 'Packages that must stay out'
for package in ffmpeg-free libavcodec-free power-profiles-daemon; do
    if rpm -q "$package" >/dev/null; then
        echo "$package is installed" >&2
        exit 1
    fi
done

if [[ ,$profiles, == *,herdr,* ]]; then
    section 'Herdr where its installer puts it'
    [[ -x $home/.local/bin/herdr-core && $(readlink "$home/.local/bin/hc") == "$home/.local/bin/herdr-core" ]] || { echo 'herdr-core or hc missing' >&2; exit 1; }
    [[ -x $home/.local/share/herdr-app/herdr-app && -L $home/.local/bin/herdr-app ]] || { echo 'the Herdr app is missing' >&2; exit 1; }
    grep -qx "Exec=$home/.local/bin/herdr-app" "$home/.local/share/applications/herdr-app.desktop" || { echo 'no Herdr launcher entry' >&2; exit 1; }
    stat -c '%U %n' "$home/.local/bin/herdr-core" "$home/.local/share/herdr-app"
fi

section 'A second apply finds nothing to do'
again=$(as_user ./scripts/install-desktop.py apply --profiles "$profiles")
printf '%s\n' "$again"
grep -qx 'Nothing to do.' <<<"$again"

section 'Open questions for Fedora 45'
rpm -q gdm hyprland hyprland-uwsm quickshell kitty matugen || true
echo "authselect: $(authselect current --raw)"
grep -n 'pam_exec' /etc/authselect/system-auth || true
echo "default target: $(systemctl get-default)"
echo "gdm: $(systemctl is-enabled gdm.service)"
echo "oo7-daemon for every user: $(systemctl --global is-enabled oo7-daemon.service)"
echo "PAM of GDM:"
grep -nE 'oo7|gnome_keyring|fprintd' /usr/lib/pam.d/gdm-password /usr/lib/pam.d/gdm-fingerprint || true
echo 'Secret portals:'
grep -ls 'org.freedesktop.impl.portal.Secret' /usr/share/xdg-desktop-portal/portals/*.portal || true
echo 'Vendor change default:'
grep -rs allow_vendor_change /usr/share/dnf5/libdnf.conf.d/ /etc/dnf/ || echo 'not set'
rpm -q ffmpeg ffmpeg-libs wf-recorder

section 'check.sh on this release'
dnf -y -q install desktop-file-utils python3-cmarkgfm qt6-qtdeclarative-devel
as_user ./scripts/check.sh

if [[ ${COMPILE:-} == 1 ]]; then
    # build.py compiles whatever Hyprland is installed: the guard of verified builds is in bundle.py.
    section 'Compile the plugins against this release'
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
manifest=$(python3 -c 'import tomllib; t = tomllib.load(open("scripts/install/manifest.toml", "rb"))["fedora"]
print("\n".join(p.split("(")[0] for profile in t.values() if isinstance(profile, dict) for p in profile.get("packages", ())))' | sort -u)
[[ $(getent passwd "$user" | cut -d: -f7) == "$before_shell" ]] || { echo 'login shell not restored' >&2; exit 1; }
[[ $(authselect current --raw) == "$before_auth" ]] || { echo "authselect not restored: $(authselect current --raw)" >&2; exit 1; }
[[ $(systemctl get-default) == "$before_target" ]] || { echo 'default target not restored' >&2; exit 1; }
links=$(find "$home" -type l -lname "*.dotfiles/*" | head)
[[ -z $links ]] || { printf 'Links left:\n%s\n' "$links" >&2; exit 1; }
for path in .local/bin/herdr-core .local/bin/hc .local/bin/herdr-app .local/share/herdr-app .local/share/applications/herdr-app.desktop; do
    [[ ! -e $home/$path && ! -L $home/$path ]] || { echo "~/$path left" >&2; exit 1; }
done
grep -q '"uninstalled": true' "$home/.local/state/dotfiles/install.json" || { echo 'install record not marked as undone' >&2; exit 1; }
again=$(as_user ./scripts/install-desktop.py apply --uninstall)
grep -qx 'Nothing to do.' <<<"$again" || { printf '%s\n' "$again" >&2; exit 1; }
# A package of the manifest may stay only while something that stays needs it: then dnf refuses to remove it.
left=$(comm -12 <(sed 's/\.[^.]*$//' <<<"$extra" | sort -u) <(grep -vxE 'python3|git-core' <<<"$manifest") || true)
for package in $left; do
    if dnf remove --assumeno "$package" >/tmp/left.log 2>&1 || ! grep -q 'Problem' /tmp/left.log; then
        printf 'Still installed after uninstall, and nothing needs it: %s\n' "$package" >&2
        exit 1
    fi
    echo "Kept, still needed: $package ($(grep -m1 -o 'installed package [^ ]*' /tmp/left.log))"
done

section 'All good'
