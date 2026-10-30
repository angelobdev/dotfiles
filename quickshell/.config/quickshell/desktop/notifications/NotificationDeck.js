.pragma library

// Each card behind the front one of a closed deck drops this far and shrinks by this much; a few are
// drawn, the last of them fainter, and the rest wait out of sight.
var PEEK = 10;
var SHRINK = 0.035;
var VISIBLE = 3;
var FADE = 0.55;

var BROWSERS = /chrome|chromium|brave|edge|vivaldi|opera|helium|firefox|zen|librewolf/i;
var DOMAIN = /^[a-z0-9-]+(\.[a-z0-9-]+)+$/i;

function slug(text) {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

// Browsers name the site at the start of the body, as a link or on a line of its own.
function site(body) {
    const link = /^\s*<a\s[^>]*href=["'][a-z][a-z0-9+.-]*:\/\/([^\/:?#"']+)[^>]*>([^<]*)<\/a>/i.exec(body);
    if (link && (link[2].trim().toLowerCase() === link[1].toLowerCase() || DOMAIN.test(link[2].trim())))
        return link[1].toLowerCase();
    const line = body.split("\n")[0].trim();
    return DOMAIN.test(line) ? line.toLowerCase() : "";
}

// One deck per app, one per site for browsers; plain notify-send calls share nothing but the tool.
function groupKey(entry) {
    const app = entry?.appName || entry?.desktopEntry || "";
    if (app === "" || app === "notify-send")
        return "single:" + entry?.id;
    const host = BROWSERS.test(app) ? site(entry.body ?? "") : "";
    return host !== "" ? "web:" + host : "app:" + slug(app);
}

// Entries newest first: decks follow their newest card, cards stay in order inside a deck.
function group(entries) {
    const index = {};
    const decks = [];
    for (const entry of entries) {
        const key = groupKey(entry);
        if (index[key] === undefined) {
            index[key] = decks.length;
            decks.push({
                key: key,
                items: []
            });
        }
        decks[index[key]].items.push(entry);
    }
    return decks;
}

// Where every card goes. A closed deck shows its cards at the height of the front one, one behind the
// other; the open deck is a plain list and pushes the decks below it down. rects says where each deck
// and its front card are, for hit tests.
function layout(decks, options) {
    const heightOf = id => options.heights[id] ?? options.fallback;
    const places = {};
    const rects = [];
    let y = 0;
    decks.forEach((deck, index) => {
        const open = deck.key === options.openDeck;
        const top = y;
        const frontHeight = heightOf(deck.items[0].id);
        deck.items.forEach((item, rank) => {
            const drawn = open || rank < VISIBLE;
            const height = open ? heightOf(item.id) : frontHeight;
            places[item.id] = {
                y: open ? y : top + rank * PEEK,
                height: height,
                scale: open ? 1 : Math.max(0.7, 1 - rank * SHRINK),
                opacity: open || rank === 0 ? 1 : !drawn ? 0 : rank === VISIBLE - 1 ? FADE : 0.85,
                z: 1000 - rank,
                front: rank === 0,
                drawn: drawn,
                open: open,
                stacked: deck.items.length > 1
            };
            if (open)
                y += height + options.gap;
        });
        y = open ? y - options.gap : top + frontHeight + Math.min(deck.items.length - 1, VISIBLE - 1) * PEEK;
        rects.push({
            key: deck.key,
            top: top,
            frontBottom: top + frontHeight,
            bottom: y
        });
        if (index < decks.length - 1)
            y += options.deckGap;
    });
    return {
        places: places,
        rects: rects,
        height: y
    };
}

// The deck whose front card is at this height, give or take a small margin; "" between front cards.
function deckAt(rects, y, margin) {
    const rect = rects.find(r => y >= r.top - margin && y <= r.frontBottom + margin);
    return rect ? rect.key : "";
}

// The notification center lists whole decks together. Closed ones show only their newest entry; counts
// says how many entries each front entry stands for.
function collapse(entries, openKeys) {
    const shown = [];
    const counts = {};
    const keys = {};
    for (const deck of group(entries)) {
        const front = deck.items[0];
        counts[front.id] = deck.items.length;
        keys[front.id] = deck.key;
        for (const item of openKeys.includes(deck.key) ? deck.items : [front])
            shown.push(item);
    }
    return {
        entries: shown,
        counts: counts,
        keys: keys
    };
}
