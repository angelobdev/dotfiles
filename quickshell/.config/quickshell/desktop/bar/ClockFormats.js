.pragma library

// The formats of the bar clock (Config.barClockFormat). A right click on the clock steps through them in this
// order. Each is built from the date format of the catalog and the time format of the locale, so it stays in
// the language and the 12 or 24 hours of the session; iso is the one fixed format.
var names = ["default", "time", "seconds", "weekday", "iso"];

function format(name, dateFormat, timeFormat) {
    if (name === "time")
        return timeFormat;
    if (name === "seconds")
        return dateFormat + "  " + withSeconds(timeFormat);
    if (name === "weekday")
        return "dddd  " + timeFormat;
    if (name === "iso")
        return "yyyy-MM-dd  HH:mm";
    return dateFormat + "  " + timeFormat;
}

// The locale's short time with seconds after the minutes: "HH:mm" becomes "HH:mm:ss", "h:mm AP" "h:mm:ss AP".
function withSeconds(timeFormat) {
    return timeFormat.indexOf("ss") >= 0 ? timeFormat : timeFormat.replace(/mm/, "mm:ss");
}

function needsSeconds(name) {
    return name === "seconds";
}

function next(name) {
    return names[(names.indexOf(name) + 1) % names.length];
}
