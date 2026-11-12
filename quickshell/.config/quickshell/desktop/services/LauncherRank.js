.pragma library

// How the launcher orders apps: how well the query matches (a tier), then how much each app was used lately (a
// score from the launch history of services/Apps.qml), then the name. Tested by scripts/tests/tst_launcher_rank.qml.

const DAY = 24 * 60 * 60 * 1000;
// Each launch adds the points of the first bucket its age fits; launches older than the last one count nothing
// and are dropped from the history.
const buckets = [
    { age: DAY, points: 100 },
    { age: 7 * DAY, points: 70 },
    { age: 30 * DAY, points: 40 },
    { age: 90 * DAY, points: 20 }
];
const forgetAfter = 90 * DAY;
// The history keeps the latest launches of each app and the apps with the highest scores.
const launchesKept = 10;
const appsKept = 100;

// Match tiers, best first; NONE leaves the app out.
const PREFIX = 0;
const WORD_START = 1;
const SUBSTRING = 2;
const SUBSEQUENCE = 3;
const OTHER_FIELDS = 4;
const NONE = -1;

function weight(age) {
    for (const bucket of buckets) {
        if (age < bucket.age)
            return bucket.points;
    }
    return 0;
}

// The use score of one app from its launch times (ms since the epoch).
function score(times, now) {
    let total = 0;
    for (const time of times ?? [])
        total += weight(Math.max(0, now - time));
    return total;
}

// Lower case without accents, so "é" matches "e".
function fold(text) {
    const lower = String(text ?? "").toLowerCase();
    return typeof lower.normalize === "function" ? lower.normalize("NFD").replace(/[̀-ͯ]/g, "") : lower;
}

// Alphabetical order on the folded names, so it is the same under every locale: localeCompare follows the locale
// of the process, and the C locale (a session without one, the test container) puts every capital before "a".
function byName(a, b) {
    const left = fold(a);
    const right = fold(b);
    if (left !== right)
        return left < right ? -1 : 1;
    return String(a) < String(b) ? -1 : String(a) > String(b) ? 1 : 0;
}

// The words of a name, split at spaces and punctuation and where a lower case letter meets an upper case one
// ("LibreOffice" -> libre, office).
function words(name) {
    return fold(String(name ?? "").replace(/([a-z])([A-Z])/g, "$1 $2")).split(/[^0-9a-zÀ-￿]+/).filter(word => word !== "");
}

// The query (spaces removed) read as prefixes of words in order, each word giving at least one letter and
// words allowed to be skipped: "vsc" and "vscode" find Visual Studio Code, "code" finds it too.
function matchesWordStarts(list, query) {
    const failed = {};
    function from(at, first) {
        if (at === query.length)
            return true;
        if (failed[at + ":" + first])
            return false;
        for (let index = first; index < list.length; index++) {
            const word = list[index];
            let common = 0;
            while (common < word.length && at + common < query.length && word[common] === query[at + common])
                common++;
            for (let taken = common; taken > 0; taken--) {
                if (from(at + taken, index + 1))
                    return true;
            }
        }
        failed[at + ":" + first] = true;
        return false;
    }
    return query !== "" && from(0, 0);
}

function isSubsequence(text, query) {
    let at = 0;
    for (let index = 0; index < text.length && at < query.length; index++) {
        if (text[index] === query[at])
            at++;
    }
    return query !== "" && at === query.length;
}

// How an app matches the query: one of the tiers above. An empty query matches every app in the first tier.
function tier(entry, query) {
    const wanted = fold(query).trim();
    if (wanted === "")
        return PREFIX;
    const name = fold(entry.name);
    if (name.startsWith(wanted))
        return PREFIX;
    const compact = wanted.replace(/\s+/g, "");
    if (matchesWordStarts(words(entry.name), compact))
        return WORD_START;
    if (name.includes(wanted))
        return SUBSTRING;
    if (isSubsequence(name.replace(/\s+/g, ""), compact))
        return SUBSEQUENCE;
    // What the launcher matched before ranking: the query anywhere in the name, generic name and keywords.
    const keywords = Array.from(entry.keywords ?? []).join(" ");
    if (fold(entry.name + " " + (entry.genericName ?? "") + " " + keywords).includes(wanted))
        return OTHER_FIELDS;
    return NONE;
}

// The entries that match, best first: by tier, then by use score, then by name. history maps a desktop-entry
// id to its launch times; an empty one leaves the order alphabetical within each tier.
function rank(entries, query, history, now) {
    const found = [];
    for (const entry of entries) {
        const level = tier(entry, query);
        if (level !== NONE)
            found.push({
                entry: entry,
                tier: level,
                score: score(history?.[entry.id], now)
            });
    }
    found.sort((a, b) => a.tier - b.tier || b.score - a.score || byName(a.entry.name, b.entry.name));
    return found.map(item => item.entry);
}

// The history with one more launch of id at now, trimmed.
function record(history, id, now) {
    const next = Object.assign({}, history);
    next[id] = (next[id] ?? []).concat([now]).slice(-launchesKept);
    return prune(next, now);
}

// Launch times older than forgetAfter go, then apps without any, then all but the appsKept best scores
// (on a tie, the most recent launch stays).
function prune(history, now) {
    const kept = [];
    for (const id in history) {
        const times = history[id].filter(time => now - time < forgetAfter);
        if (times.length > 0)
            kept.push({
                id: id,
                times: times,
                score: score(times, now)
            });
    }
    kept.sort((a, b) => b.score - a.score || b.times[b.times.length - 1] - a.times[a.times.length - 1]);
    const result = {};
    for (const item of kept.slice(0, appsKept))
        result[item.id] = item.times;
    return result;
}

// launches.json read back: {"apps": {id: [times]}}. Anything else in it is left out; a broken file is an empty history.
function parse(text, now) {
    let value = null;
    try {
        value = JSON.parse(text);
    } catch (error) {
        return {};
    }
    const apps = value && typeof value === "object" ? value.apps : null;
    if (!apps || typeof apps !== "object" || Array.isArray(apps))
        return {};
    const history = {};
    for (const id in apps) {
        if (Array.isArray(apps[id]))
            history[id] = apps[id].filter(time => typeof time === "number" && isFinite(time)).sort((a, b) => a - b).slice(-launchesKept);
    }
    return prune(history, now);
}

function serialize(history) {
    return JSON.stringify({
        apps: history
    }) + "\n";
}
