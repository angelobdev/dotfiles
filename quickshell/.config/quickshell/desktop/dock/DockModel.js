.pragma library

// Pure layout helpers for the dock, kept apart so scripts/tests can exercise them without a compositor.

// Centre of an item in the unmagnified row, relative to the row's centre. Using the resting layout keeps
// magnification from feeding back into the distances it is computed from.
function baseOffset(index, count, separatorIndex, cell, gap) {
    const separators = separatorIndex > 0 ? 1 : 0;
    const width = count * cell + separators * gap;
    const left = index * cell + (separatorIndex > 0 && index >= separatorIndex ? gap : 0);
    return left + cell / 2 - width / 2;
}

// Scale for an icon whose resting centre is `distance` away from the pointer: a cosine falloff that
// reaches 1 at 2.5 cells, so the icon under the pointer and its neighbours grow.
function magnify(distance, cell, magnification) {
    if (!(magnification > 1) || !isFinite(distance))
        return 1;
    const t = Math.abs(distance) / (cell * 2.5);
    if (t >= 1)
        return 1;
    return 1 + (magnification - 1) * (Math.cos(t * Math.PI) + 1) / 2;
}

// Pinned slot nearest to the pointer while dragging a pin, in the resting layout.
function dropIndex(pointerOffset, pinnedCount, count, separatorIndex, cell, gap) {
    let best = 0;
    for (let i = 1; i < pinnedCount; i++) {
        if (Math.abs(baseOffset(i, count, separatorIndex, cell, gap) - pointerOffset) < Math.abs(baseOffset(best, count, separatorIndex, cell, gap) - pointerOffset))
            best = i;
    }
    return best;
}

// Horizontal shift of item `index` while the pin at `from` is dragged to `target`: the neighbours in
// between slide one cell towards the old slot, which opens the gap at the target.
function dragShift(index, from, target, cell) {
    if (from < 0 || target < 0)
        return 0;
    if (index === from)
        return (target - from) * cell;
    if (from < target && index > from && index <= target)
        return -cell;
    if (target < from && index >= target && index < from)
        return cell;
    return 0;
}
