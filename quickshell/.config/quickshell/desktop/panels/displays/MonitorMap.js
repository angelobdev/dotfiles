.pragma library

// The map of the monitors in use in Settings → Displays, from what Hyprland reports (hyprctl monitors -j).

// The logical size: the mode divided by the scale, turned a quarter by the odd transforms (90 and 270 degrees,
// also flipped).
function logicalSize(monitor) {
    const scale = monitor.scale > 0 ? monitor.scale : 1;
    const width = monitor.width / scale;
    const height = monitor.height / scale;
    const turned = (monitor.transform ?? 0) % 2 === 1;
    return {
        width: turned ? height : width,
        height: turned ? width : height
    };
}

function mirrors(monitor) {
    return !!monitor.mirrorOf && monitor.mirrorOf !== "none";
}

// One box per place on the desktop, fitted into width × height and centred, each with x, y, width, height and the
// names shown there: a mirror joins the monitor it shows (Hyprland names it by name or id), as does a monitor at
// the same position. Disabled monitors and FALLBACK are left out.
function boxes(monitors, width, height) {
    const used = (monitors ?? []).filter(monitor => !monitor.disabled && monitor.name !== "FALLBACK");
    // The monitors with their own picture first, so a mirror finds the one it shows.
    const ordered = used.filter(monitor => !mirrors(monitor)).concat(used.filter(mirrors));
    const places = [];
    const byKey = {};
    for (const monitor of ordered) {
        let place = mirrors(monitor) ? byKey[String(monitor.mirrorOf)] : undefined;
        place = place ?? places.find(entry => entry.left === monitor.x && entry.top === monitor.y);
        if (!place) {
            const size = logicalSize(monitor);
            place = {
                left: monitor.x,
                top: monitor.y,
                right: monitor.x + size.width,
                bottom: monitor.y + size.height,
                names: []
            };
            places.push(place);
        }
        place.names.push(monitor.name);
        byKey[monitor.name] = place;
        if (monitor.id !== undefined)
            byKey[String(monitor.id)] = place;
    }
    if (places.length === 0 || !(width > 0) || !(height > 0))
        return [];
    const left = Math.min(...places.map(place => place.left));
    const top = Math.min(...places.map(place => place.top));
    const spanWidth = Math.max(...places.map(place => place.right)) - left;
    const spanHeight = Math.max(...places.map(place => place.bottom)) - top;
    if (!(spanWidth > 0) || !(spanHeight > 0))
        return [];
    const factor = Math.min(width / spanWidth, height / spanHeight);
    const offsetX = (width - spanWidth * factor) / 2;
    const offsetY = (height - spanHeight * factor) / 2;
    // Edges rounded rather than sizes, so neighbours meet on the same pixel.
    const across = value => Math.round(offsetX + (value - left) * factor);
    const down = value => Math.round(offsetY + (value - top) * factor);
    return places.map(place => ({
                x: across(place.left),
                y: down(place.top),
                width: across(place.right) - across(place.left),
                height: down(place.bottom) - down(place.top),
                names: place.names
            }));
}
