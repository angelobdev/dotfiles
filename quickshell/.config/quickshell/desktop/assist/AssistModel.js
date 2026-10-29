.pragma library

// Geometry of the floating assist button and its menu, in the coordinates of a full-screen surface.
// A position is a side ("left" or "right") and a fraction of the free height, so it survives rotation
// and scale changes.

function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
}

// Top-left corner of the button. Idle, it slides `tuck` of its size past the edge.
function place(position, size, width, height, top, margin, tuck) {
    var free = Math.max(0, height - top - 2 * margin - size);
    var y = top + margin + clamp(position.fraction, 0, 1) * free;
    var inset = margin - (tuck || 0) * (size + margin);
    var x = position.side === "left" ? inset : width - size - inset;
    return {
        x: x,
        y: y
    };
}

// Where a drop at (x, y) snaps: the nearer side, and the height as a fraction of the free space.
function snap(x, y, size, width, height, top, margin) {
    var free = Math.max(1, height - top - 2 * margin - size);
    return {
        side: x + size / 2 < width / 2 ? "left" : "right",
        fraction: clamp((y - top - margin) / free, 0, 1)
    };
}

// The menu opens beside the button, towards the middle of the screen, centred on it and kept inside.
function menuOrigin(button, size, side, menuWidth, menuHeight, width, height, top, margin, gap) {
    var x = side === "left" ? button.x + size + gap : button.x - gap - menuWidth;
    var y = button.y + size / 2 - menuHeight / 2;
    return {
        x: clamp(x, margin, Math.max(margin, width - margin - menuWidth)),
        y: clamp(y, top + margin, Math.max(top + margin, height - margin - menuHeight))
    };
}
