.pragma library

// The bar layout: five sections, each an ordered list of widget ids (bar/widgets/Registry.js). The center
// block is center-left, center and center-right side by side; it is centred on the bar, and the free space
// lies between the left section and the block and between the block and the right section.

var sections = ["left", "centerLeft", "center", "centerRight", "right"];

// classic is the bar as it was before layouts, item for item, with the reminders indicator (shown only while one
// is pending) added since; it is also the layout without a setting.
var presets = {
    classic: {
        left: ["launcher", "workspaces", "title"],
        centerLeft: [],
        center: [],
        centerRight: [],
        right: ["tray", "media", "privacy", "recording", "reminders", "battery", "updates", "assistant", "hints", "notifications", "controls", "clock", "power"]
    },
    centered: {
        left: ["launcher", "workspaces"],
        centerLeft: ["media"],
        center: ["clock"],
        centerRight: ["weather"],
        right: ["tray", "privacy", "recording", "reminders", "network", "volume", "battery", "updates", "assistant", "notifications", "controls", "power"]
    },
    minimal: {
        left: ["workspaces"],
        centerLeft: [],
        center: ["clock"],
        centerRight: [],
        right: ["privacy", "recording", "reminders", "battery", "controls"]
    }
};

function copy(layout) {
    const result = {};
    for (const section of sections)
        result[section] = layout[section].slice();
    return result;
}

// A layout from a setting: unknown ids and sections dropped, a widget that cannot repeat kept only where it
// first appears. known(id) tells whether an id exists, repeats(id) whether it may appear more than once.
function normalize(value, known, repeats) {
    // No section at all (no setting, or one for another version) is the classic bar.
    if (!value || typeof value !== "object" || Array.isArray(value) || !sections.some(section => section in value))
        return copy(presets.classic);
    const seen = {};
    const result = {};
    for (const section of sections) {
        const ids = Array.isArray(value[section]) ? value[section] : [];
        result[section] = ids.filter(id => {
            if (typeof id !== "string" || !known(id))
                return false;
            if (repeats(id))
                return true;
            if (seen[id])
                return false;
            seen[id] = true;
            return true;
        });
    }
    return result;
}

function equal(a, b) {
    return sections.every(section => a[section].length === b[section].length && a[section].every((id, i) => id === b[section][i]));
}

// Ids not in the layout, in catalog order, plus the ones that may repeat.
function available(layout, catalog, repeats) {
    const placed = {};
    for (const section of sections)
        for (const id of layout[section])
            placed[id] = true;
    return catalog.filter(id => repeats(id) || !placed[id]);
}

function insert(layout, id, section, index) {
    const result = copy(layout);
    const list = result[section];
    list.splice(Math.max(0, Math.min(index, list.length)), 0, id);
    return result;
}

function removeAt(layout, section, index) {
    const result = copy(layout);
    result[section].splice(index, 1);
    return result;
}

// Moves the widget at (from, fromIndex) so it lands before what is now at (to, toIndex).
function move(layout, from, fromIndex, to, toIndex) {
    const id = layout[from][fromIndex];
    if (id === undefined)
        return copy(layout);
    let index = toIndex;
    if (from === to && fromIndex < toIndex)
        index -= 1;
    return insert(removeAt(layout, from, fromIndex), id, to, index);
}

// Where a drop at x lands among a section's widgets, given the horizontal centre of each.
function dropIndex(centres, x) {
    let index = 0;
    while (index < centres.length && centres[index] < x)
        index += 1;
    return index;
}

// The x of the center block: centred when it fits, else pushed away from the side that would overlap it.
// fixedLeft is the width the left section needs when the window title shrinks to nothing; 0 when empty.
function centerX(width, blockWidth, fixedLeft, rightWidth, gap) {
    const ideal = (width - blockWidth) / 2;
    const highest = width - blockWidth - (rightWidth > 0 ? rightWidth + gap : 0);
    const lowest = fixedLeft > 0 ? fixedLeft + gap : 0;
    return Math.max(lowest, Math.min(ideal, highest));
}

// Catalog keys of a section's name and of a preset's menu entry.
function sectionKey(section) {
    return "bar.sections." + section;
}

function presetKey(name) {
    return "bar.menu.presets." + name;
}
