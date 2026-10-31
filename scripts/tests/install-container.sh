#!/usr/bin/env bash
# Runs install-desktop.py for real in a throwaway fedora:45 container, as root, on a copy of the repository.
# Files are piped in: never mount the repository with :z, which relabels the files the live session reads.
#
#   git ls-files -co --exclude-standard -z | tar --null -T - -c | docker run -i --rm fedora:45 \
#       bash -c 'mkdir /src && tar -x -C /src && exec bash /src/scripts/tests/install-container.sh'
#
# Environment: PROFILES (default core,hardware,plugins), COMPILE=1 also builds the plugins (slow). The container
# has no systemd, so the firewall, Flatpak and login steps skip themselves: only a VM covers those.
set -euo pipefail

source=${1:-/src}
profiles=${PROFILES:-core,hardware,plugins}
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
useradd --create-home --groups wheel "$user"
printf '%s ALL=(ALL) NOPASSWD: ALL\n' "$user" >/etc/sudoers.d/$user
install -d -m 700 -o "$user" /tmp/runtime
cp -a "$source/." "$repo"
chown -R "$user:" "$repo"
authselect select local --force >/dev/null
cd "$repo"

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
    # On this copy only: the guard accepts a build once it has compiled here.
    section 'Compile the plugins against this release'
    version=$(rpm -q --qf '%{VERSION}-%{RELEASE}.%{ARCH}' hyprland)
    sed -i "s/if version != '[^']*':/if version != '$version':/" scripts/hyprpm/build.py
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

section 'All good'
