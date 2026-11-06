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
