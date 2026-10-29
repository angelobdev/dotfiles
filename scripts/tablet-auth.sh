#!/usr/bin/env bash
# Skip the fingerprint reader in tablet mode: folded back, the screen covers it, so sudo, polkit and the
# lock screen should ask for the password at once instead of waiting for the reader to time out.
#
#   ./scripts/tablet-auth.sh install   copy the authselect profile, add the tablet check, select it
#   ./scripts/tablet-auth.sh remove    select the original profile again and remove the copy and check
#   ./scripts/tablet-auth.sh status    show what is installed
#
# Run as the desktop user: the script asks sudo for each system change. Outside tablet mode nothing changes;
# in it, only the fingerprint step is skipped, and the password is checked as always.
set -euo pipefail

profile=desktop-tablet
custom=/etc/authselect/custom/$profile
check=/usr/local/libexec/desktop-tablet-mode
# Must match the fingerprint line of the base profile template; the inserted line skips it on success.
skip='auth        [success=1 default=ignore]                   pam_exec.so quiet /usr/local/libexec/desktop-tablet-mode {include if "with-fingerprint"}'

current() { authselect current --raw 2>/dev/null || true; }

install_check() {
    local temporary
    temporary=$(mktemp)
    cat >"$temporary" <<'EOF'
#!/bin/sh
# pam_exec check from ~/.dotfiles/scripts/tablet-auth.sh: succeeds only while the desktop session of
# PAM_USER is in tablet mode, which the shell records in its runtime directory.
uid=$(id -u -- "$PAM_USER" 2>/dev/null) || exit 1
state="/run/user/$uid/desktop-shell/tablet.json"
[ -f "$state" ] && [ ! -L "$state" ] && grep -Eq '"tablet"[[:space:]]*:[[:space:]]*true' "$state"
EOF
    sudo install -o root -g root -m 0755 "$temporary" "$check"
    rm -f "$temporary"
}

case "${1:-}" in
    install)
        read -r base features <<<"$(current)"
        [[ -n ${base:-} ]] || { echo 'authselect has no current profile.' >&2; exit 1; }
        if [[ $base == "custom/$profile" ]]; then
            echo "custom/$profile is already selected."
            install_check
            exit 0
        fi
        [[ $base == local ]] || { echo "Expected the local profile, found $base: adapt the script first." >&2; exit 1; }
        install_check
        if [[ ! -d $custom ]]; then
            sudo authselect create-profile "$profile" -b "$base"
        fi
        if ! sudo grep -qF 'desktop-tablet-mode' "$custom/system-auth"; then
            sudo grep -q 'pam_fprintd.so' "$custom/system-auth" || { echo "No pam_fprintd line in $custom/system-auth." >&2; exit 1; }
            sudo sed -i "/pam_fprintd.so/i $skip" "$custom/system-auth"
        fi
        echo "Fingerprint lines of $custom/system-auth:"
        sudo grep -n 'pam_exec\|pam_fprintd' "$custom/system-auth"
        # shellcheck disable=SC2086 # the features are separate words
        sudo authselect select "custom/$profile" $features
        sudo authselect apply-changes
        echo "Selected custom/$profile with: $features"
        ;;
    remove)
        read -r base features <<<"$(current)"
        if [[ ${base:-} == "custom/$profile" ]]; then
            # shellcheck disable=SC2086
            sudo authselect select local $features
        fi
        [[ -d $custom ]] && sudo rm -r "$custom"
        sudo rm -f "$check"
        echo "Selected: $(current)"
        ;;
    status)
        echo "Profile: $(current)"
        [[ -x $check ]] && echo "Check: $check" || echo "Check: not installed"
        [[ -d $custom ]] && grep -n 'pam_exec\|pam_fprintd' "$custom/system-auth" || echo "Custom profile: not created"
        ;;
    *) echo 'Usage: tablet-auth.sh install|remove|status' >&2; exit 2 ;;
esac
