.pragma library
.import "LauncherRank.js" as Rank

// The commands of the launcher (">", services/Commands.qml): the tree read from commands.json, which entries show,
// and the search. Tested by scripts/tests/tst_command_model.qml.
//
// An entry is keyed by a dotted id, its place in the tree: "system.reboot" is under "system", an id without a dot is
// on the first level. One with an action (panel, settings, session, call, run) is a command; one with rows gets its
// entries from a provider of the shell when it opens; anything else is a category. "when" hides it, "enabled" dims
// it, "state" draws a switch: each the name of a state of the shell, "!name" for its opposite, or a list of them
// that must all hold. "alt" names the entry that stands in for it while Alt is held, which is then left out of
// its category but still found by the search.

const ACTIONS = ["panel", "settings", "session", "call", "run"];

// {order: [ids, as in the file], items: {id: entry with id and parent}}. Entries that are not objects are skipped;
// a missing parent puts an entry on the first level.
function parse(object) {
    const order = [];
    const items = {};
    if (!object || typeof object !== "object" || Array.isArray(object))
        return { order: order, items: items };
    for (const id in object) {
        const value = object[id];
        if (!value || typeof value !== "object" || Array.isArray(value) || !/^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$/.test(id))
            continue;
        const entry = Object.assign({}, value);
        entry.id = id;
        order.push(id);
        items[id] = entry;
    }
    for (const id of order) {
        const dot = id.lastIndexOf(".");
        const parent = dot < 0 ? "" : id.slice(0, dot);
        items[id].parent = parent === "" || items[parent] ? parent : "";
    }
    return { order: order, items: items };
}

function isCommand(entry) {
    return !!entry && ACTIONS.some(name => entry[name] !== undefined);
}

function hasRows(entry) {
    return !!entry && typeof entry.rows === "string" && entry.rows !== "";
}

// A category opens (its entries, or a provider's rows); a command runs.
function opens(entry) {
    return !!entry && !isCommand(entry);
}

// Whether a condition holds: "" or none always; "name", "!name", or a list of them.
function holds(condition, state) {
    if (condition === undefined || condition === null || condition === "")
        return true;
    if (Array.isArray(condition))
        return condition.every(part => holds(part, state));
    const text = String(condition);
    const negated = text.startsWith("!");
    const value = (state ?? {})[negated ? text.slice(1) : text] === true;
    return negated ? !value : value;
}

// "requires" names a program that must be installed: the shell checks it once ("requires:NAME" in the state).
function shown(entry, state) {
    if (!entry || entry.hidden === true || !holds(entry.when, state))
        return false;
    return typeof entry.requires !== "string" || entry.requires === "" || (state ?? {})["requires:" + entry.requires] === true;
}

// The commands of the desktop with the user's own laid over them, both objects as commands.json holds them. An id
// of both takes the user's fields over the shipped ones and keeps its place; a new one comes after the shipped
// ones; "hidden": true leaves one out. A label or reason the user wrote is their own text, shown as it is
// (literal), not a catalog key.
function merge(shipped, own) {
    const result = {};
    const plain = value => value && typeof value === "object" && !Array.isArray(value);
    for (const id in (plain(shipped) ? shipped : {}))
        result[id] = shipped[id];
    if (!plain(own))
        return result;
    for (const id in own) {
        const value = own[id];
        if (!plain(value))
            continue;
        const entry = Object.assign({}, plain(result[id]) ? result[id] : {}, value);
        if (value.label !== undefined || !plain(result[id]))
            entry.literal = true;
        result[id] = entry;
    }
    return result;
}

// The programs commands name in "requires", once each.
function required(model) {
    const names = [];
    for (const id of model.order) {
        const name = model.items[id].requires;
        if (typeof name === "string" && name !== "" && !names.includes(name))
            names.push(name);
    }
    return names;
}

function enabled(entry, state) {
    return holds(entry.enabled, state);
}

// "on", "off" or "" (no switch).
function switchState(entry, state) {
    if (entry.state === undefined || entry.state === "")
        return "";
    return holds(entry.state, state) ? "on" : "off";
}

// The ids other entries name as their Alt stand-in: not listed in their category.
function alternates(model) {
    const names = {};
    for (const id of model.order) {
        const alt = model.items[id].alt;
        if (typeof alt === "string" && model.items[alt] && isCommand(model.items[alt]))
            names[alt] = true;
    }
    return names;
}

// What a category holds that shows: its entries in file order, without Alt stand-ins and without categories that
// show nothing (a provider's category always counts, its rows come later).
function children(model, parent, state) {
    const skip = alternates(model);
    const result = [];
    for (const id of model.order) {
        const entry = model.items[id];
        if (entry.parent !== parent || skip[id] || !shown(entry, state))
            continue;
        if (opens(entry) && !hasRows(entry) && children(model, id, state).length === 0)
            continue;
        result.push(entry);
    }
    return result;
}

// The entry that stands in for this one while Alt is held, when it shows; else the entry itself.
function variant(model, entry, state, alt) {
    if (!alt || !entry || typeof entry.alt !== "string")
        return entry;
    const other = model.items[entry.alt];
    return other && isCommand(other) && shown(other, state) ? other : entry;
}

// The ids above an entry, outermost first.
function ancestors(model, id) {
    const result = [];
    let parent = model.items[id]?.parent ?? "";
    while (parent !== "") {
        result.unshift(parent);
        parent = model.items[parent]?.parent ?? "";
    }
    return result;
}

// The categories above an entry or a provider's row (whose parent is its category).
function above(model, entry) {
    return model.items[entry.id] ? ancestors(model, entry.id) : ancestors(model, entry.parent).concat([entry.parent]);
}

// Whether an entry and every category above it show.
function reachable(model, id, state) {
    if (!shown(model.items[id], state))
        return false;
    return ancestors(model, id).every(parent => shown(model.items[parent], state));
}

// The commands under a category ("" for all) that match the query, best first, each with its LauncherRank tier, so
// the launcher can mix them with apps: by how well the label matches (the names of the categories above count as
// other words), then in file order. rows maps a provider category id to its
// rows as entries (id, parent, label); label(entry) is the text shown.
function matches(model, query, state, label, under, rows) {
    const within = under ?? "";
    const found = [];
    function consider(entry, position) {
        const path = above(model, entry).map(id => label(model.items[id]));
        const tier = Rank.tier({ name: label(entry), keywords: path.concat(entry.terms ?? []) }, query);
        if (tier === Rank.NONE)
            return;
        found.push({ entry: entry, tier: tier, position: position });
    }
    const inside = id => within === "" || id === within || id.startsWith(within + ".");
    model.order.forEach((id, position) => {
        const entry = model.items[id];
        if (!inside(id) || !reachable(model, id, state))
            return;
        if (isCommand(entry))
            consider(entry, position);
        else if (hasRows(entry))
            (rows?.[id] ?? []).forEach((row, index) => consider(row, position + (index + 1) / 1000));
    });
    found.sort((a, b) => a.tier - b.tier || a.position - b.position);
    return found.map(match => ({ entry: match.entry, tier: match.tier }));
}

// The same, the entries alone.
function search(model, query, state, label, under, rows) {
    return matches(model, query, state, label, under, rows).map(match => match.entry);
}
