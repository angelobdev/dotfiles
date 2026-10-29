.pragma library

// Shell glyph (assets/icons/<name>.svg) to freedesktop symbolic icon names, first match wins. Used when the
// shell icons come from the icon pack; a glyph whose names the pack lacks keeps the bundled drawing.
var names = {
    "apps": ["view-app-grid-symbolic", "view-grid-symbolic"],
    "arrow-left": ["go-previous-symbolic", "go-left-symbolic"],
    "backspace": ["edit-clear-symbolic", "edit-undo-symbolic"],
    "balanced": ["power-profile-balanced-symbolic"],
    "battery-0": ["battery-level-0-symbolic", "battery-empty-symbolic"],
    "battery-25": ["battery-level-20-symbolic", "battery-low-symbolic"],
    "battery-50": ["battery-level-50-symbolic", "battery-good-symbolic"],
    "battery-75": ["battery-level-80-symbolic", "battery-good-symbolic"],
    "battery-100": ["battery-level-100-symbolic", "battery-full-symbolic"],
    "battery-charging": ["battery-level-100-charged-symbolic", "battery-full-charging-symbolic"],
    "bell": ["notifications-symbolic", "preferences-system-notifications-symbolic"],
    "bell-off": ["notifications-disabled-symbolic", "notification-disabled-symbolic"],
    "bluetooth": ["bluetooth-active-symbolic", "bluetooth-symbolic"],
    "chevron-down": ["pan-down-symbolic", "go-down-symbolic"],
    "chevron-left": ["pan-start-symbolic", "go-previous-symbolic"],
    "chevron-right": ["pan-end-symbolic", "go-next-symbolic"],
    "chevron-up": ["pan-up-symbolic", "go-up-symbolic"],
    "clipboard": ["edit-paste-symbolic"],
    "close": ["window-close-symbolic"],
    "coffee": ["caffeine-cup-full-symbolic", "preferences-desktop-screensaver-symbolic"],
    "controls": ["emblem-system-symbolic", "preferences-system-symbolic"],
    "copy": ["edit-copy-symbolic"],
    "enter": ["keyboard-enter-symbolic", "mail-reply-sender-symbolic"],
    "ethernet": ["network-wired-symbolic"],
    "dock": ["user-desktop-symbolic", "preferences-desktop-symbolic"],
    "eye": ["view-reveal-symbolic"],
    "eye-off": ["view-conceal-symbolic"],
    "folder": ["folder-symbolic"],
    "hotspot": ["network-wireless-hotspot-symbolic"],
    "image": ["image-x-generic-symbolic"],
    "keyboard": ["input-keyboard-symbolic"],
    "leaf": ["power-profile-power-saver-symbolic"],
    "lock": ["system-lock-screen-symbolic", "changes-prevent-symbolic"],
    "logout": ["system-log-out-symbolic"],
    "microphone": ["audio-input-microphone-symbolic"],
    "microphone-muted": ["microphone-sensitivity-muted-symbolic", "microphone-disabled-symbolic"],
    "monitor": ["video-display-symbolic"],
    "next": ["media-skip-forward-symbolic"],
    "overview": ["view-dual-symbolic", "focus-windows-symbolic"],
    "pause": ["media-playback-pause-symbolic"],
    "performance": ["power-profile-performance-symbolic"],
    "pin": ["view-pin-symbolic"],
    "pip": ["view-restore-symbolic", "window-restore-symbolic"],
    "play": ["media-playback-start-symbolic"],
    "power": ["system-shutdown-symbolic"],
    "previous": ["media-skip-backward-symbolic"],
    "qr-code": ["qr-code-symbolic"],
    "reboot": ["system-reboot-symbolic"],
    "record": ["media-record-symbolic"],
    "rotate": ["rotation-allowed-symbolic", "object-rotate-right-symbolic"],
    "rotate-lock": ["rotation-locked-symbolic"],
    "shift": ["keyboard-shift-filled-symbolic", "go-up-symbolic"],
    "shift-lock": ["keyboard-caps-lock-filled-symbolic", "go-top-symbolic"],
    "stop": ["media-playback-stop-symbolic"],
    "sun": ["display-brightness-symbolic", "weather-clear-symbolic"],
    "suspend": ["system-suspend-symbolic", "weather-clear-night-symbolic"],
    "trash": ["user-trash-symbolic"],
    "volume-high": ["audio-volume-high-symbolic"],
    "volume-low": ["audio-volume-low-symbolic"],
    "volume-muted": ["audio-volume-muted-symbolic"],
    "vpn": ["network-vpn-symbolic"],
    "wifi": ["network-wireless-signal-excellent-symbolic"],
    "wifi-1": ["network-wireless-signal-weak-symbolic"],
    "wifi-2": ["network-wireless-signal-good-symbolic"],
    "wifi-off": ["network-wireless-offline-symbolic", "network-wireless-disabled-symbolic"]
};

// The first name the current icon theme resolves (resolve returns "" when it has none), else "".
function packSource(glyph, resolve) {
    var candidates = names[glyph] || [];
    for (var i = 0; i < candidates.length; i++) {
        var source = resolve(candidates[i]);
        if (source)
            return source;
    }
    return "";
}
