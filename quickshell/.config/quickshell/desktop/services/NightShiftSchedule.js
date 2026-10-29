.pragma library

// The automatic Night shift window: "HH:MM" start and end, which may cross midnight (20:00 to 07:00).

function minutes(text) {
    var parts = String(text).split(":").map(Number);
    return parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1]) ? parts[0] * 60 + parts[1] : 0;
}

function inWindow(date, start, end) {
    var now = date.getHours() * 60 + date.getMinutes();
    var from = minutes(start), to = minutes(end);
    return from <= to ? now >= from && now < to : now >= from || now < to;
}

// The next start or end after date, in ms since the epoch.
function nextBoundary(date, start, end) {
    var now = date.getHours() * 60 + date.getMinutes();
    var ahead = [minutes(start), minutes(end)].map(function (mark) {
        return (mark - now + 1440) % 1440 || 1440;
    });
    var base = new Date(date.getTime());
    base.setSeconds(0, 0);
    return base.getTime() + Math.min(ahead[0], ahead[1]) * 60000;
}
