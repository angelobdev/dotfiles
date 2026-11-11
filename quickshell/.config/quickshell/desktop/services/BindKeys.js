.pragma library

// Keys of a Hyprland bind as Settings takes them ("SUPER + SHIFT + B"): whether they are valid (the same check as
// hyprsettings.py), the modifier mask and key Hyprland stores (hyprctl binds), and which binds already use them.

const MASKS = { SHIFT: 1, CTRL: 4, CONTROL: 4, ALT: 8, MOD2: 16, MOD3: 32, SUPER: 64, MOD5: 128 };

function valid(text) {
    const parts = String(text).split("+").map(part => part.trim());
    if (parts.length === 0 || parts.some(part => part === ""))
        return false;
    const key = parts.pop();
    return parts.every(part => MASKS[part.toUpperCase()] !== undefined) && /^[A-Za-z0-9_]+$/.test(key);
}

// { mask, key }, the key lowercase to compare: Hyprland keeps it as written.
function combo(text) {
    const parts = String(text).split("+").map(part => part.trim());
    const key = (parts.pop() || "").toLowerCase();
    return { mask: parts.reduce((mask, part) => mask | (MASKS[part.toUpperCase()] || 0), 0), key: key };
}

// The descriptions of the binds in `taken` ({ mask, key, description }) on these keys, leaving out one with
// `own` as description: the bind this very row put there.
function takenBy(taken, text, own) {
    if (!valid(text))
        return [];
    const wanted = combo(text);
    let skipped = false;
    return taken.filter(bind => {
        if (bind.mask !== wanted.mask || bind.key !== wanted.key)
            return false;
        if (!skipped && bind.description === own) {
            skipped = true;
            return false;
        }
        return true;
    }).map(bind => bind.description);
}

// Keysyms as Hints shows them, by lowercase name: a catalog key under keys., translated with tr, or a symbol that
// reads the same in every language. Any other key keeps its name (F5, A).
const KEY_NAMES = {
    "return": "keys.enter",
    "kp_enter": "keys.enter",
    "space": "keys.space",
    "print": "keys.print",
    "escape": "keys.escape",
    "tab": "keys.tab",
    "backspace": "keys.backspace",
    "delete": "keys.delete",
    "insert": "keys.insert",
    "home": "keys.home",
    "end": "keys.end",
    "prior": "keys.pageUp",
    "page_up": "keys.pageUp",
    "next": "keys.pageDown",
    "page_down": "keys.pageDown",
    "caps_lock": "keys.capsLock",
    "menu": "keys.menu",
    "mouse:272": "keys.leftMouse",
    "mouse:273": "keys.rightMouse",
    "mouse:274": "keys.middleMouse",
    "mouse_up": "keys.scrollUp",
    "mouse_down": "keys.scrollDown",
    "xf86audioraisevolume": "keys.volumeUp",
    "xf86audiolowervolume": "keys.volumeDown",
    "xf86audiomute": "keys.mute",
    "xf86audiomicmute": "keys.microphoneMute",
    "xf86audioplay": "keys.play",
    "xf86audiopause": "keys.pause",
    "xf86audiostop": "keys.stop",
    "xf86audionext": "keys.nextTrack",
    "xf86audioprev": "keys.previousTrack",
    "xf86monbrightnessup": "keys.brightnessUp",
    "xf86monbrightnessdown": "keys.brightnessDown",
    "xf86kbdbrightnessup": "keys.keyboardLightUp",
    "xf86kbdbrightnessdown": "keys.keyboardLightDown",
    "xf86kbdlightonoff": "keys.keyboardLight",
    "xf86calculator": "keys.calculator",
    "xf86sleep": "keys.sleep",
    "xf86poweroff": "keys.power",
    "xf86search": "keys.search",
    "xf86mail": "keys.mail",
    "xf86www": "keys.browser",
    "xf86homepage": "keys.browser",
    "xf86explorer": "keys.files",
    "xf86mycomputer": "keys.files",
    "xf86touchpadtoggle": "keys.touchpad",
    "xf86wlan": "keys.wifi",
    "xf86rfkill": "keys.airplaneMode",
    "xf86display": "keys.display",
    "xf86screensaver": "keys.lock"
};
const KEY_SYMBOLS = {
    "period": ".",
    "comma": ",",
    "minus": "-",
    "plus": "+",
    "equal": "=",
    "slash": "/",
    "backslash": "\\",
    "semicolon": ";",
    "apostrophe": "'",
    "grave": "`",
    "bracketleft": "[",
    "bracketright": "]",
    "left": "←",
    "right": "→",
    "up": "↑",
    "down": "↓"
};

function keyName(key, tr) {
    const text = String(key ?? "");
    const lower = text.toLowerCase();
    if (Object.prototype.hasOwnProperty.call(KEY_SYMBOLS, lower))
        return KEY_SYMBOLS[lower];
    if (Object.prototype.hasOwnProperty.call(KEY_NAMES, lower))
        return tr(KEY_NAMES[lower]);
    return text;
}
