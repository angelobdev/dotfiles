.pragma library

// When a reminder is due, from what is typed in its dialog or given to desktop-shell remind: minutes ("20"),
// hours and minutes ("1h30", "1 h 30 min", "90m", "2h"), or a time of day ("14:30", "9.05"), today or, when it
// has passed, tomorrow. The time in ms, or NaN for anything else. A day at most: a reminder is for the hours ahead.
var MAX_MINUTES = 24 * 60;

function due(text, now) {
    var value = String(text || "").trim().toLowerCase();
    var clock = /^([01]?[0-9]|2[0-3])[:.]([0-5][0-9])$/.exec(value);
    if (clock) {
        var at = new Date(now);
        at.setHours(+clock[1], +clock[2], 0, 0);
        if (at.getTime() <= now)
            at.setDate(at.getDate() + 1);
        return at.getTime();
    }
    var span = /^(?:([0-9]+)\s*(?:hours?|hrs?|h|ore|ora))?\s*(?:([0-9]+)\s*(?:minutes?|minut[oi]|mins?|m)?)?$/.exec(value);
    if (!span || (span[1] === undefined && span[2] === undefined))
        return NaN;
    var minutes = (+(span[1] || 0)) * 60 + (+(span[2] || 0));
    if (minutes < 1 || minutes > MAX_MINUTES)
        return NaN;
    return now + minutes * 60000;
}

// What is left, in whole minutes rounded up (a reminder half a minute away still says 1).
function minutesLeft(at, now) {
    return Math.max(0, Math.ceil((at - now) / 60000));
}
