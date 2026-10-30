.pragma library

// As on iOS, a likely next letter is easier to hit, though the keys look the same: its key grows towards
// its neighbours. Never by more than a share of the key height, so a touch well inside a key stays on it.
var REACH = 0.2;
// Below this probability a letter gets nothing; a surprising letter is still only one good tap away.
var FLOOR = 0.02;

function gain(probability, reach) {
    if (!(probability > FLOOR))
        return 0;
    return reach * (Math.log(Math.min(probability, 1)) - Math.log(FLOOR)) / -Math.log(FLOOR);
}

// What it takes to turn the letters typed into a suggestion: going back over what differs (an accent left
// out) and typing on from there.
function edit(typed, word) {
    const letters = Array.from(word);
    const done = Array.from(typed);
    let same = 0;
    while (same < done.length && done[same] === letters[same])
        same++;
    return {
        back: done.length - same,
        rest: letters.slice(same)
    };
}

// Among keys with their distance from the touch, 0 inside the key. Only letters compete: a touch nearest
// to any other key is that key, and with no prediction the nearest key wins.
function pick(keys, letters, reach) {
    let nearest = null;
    for (const key of keys) {
        if (nearest === null || key.distance < nearest.distance)
            nearest = key;
    }
    if (nearest === null || Object.keys(letters).length === 0 || !/^[a-z]$/.test(nearest.label ?? ""))
        return nearest;
    let best = nearest;
    let score = nearest.distance - gain(letters[nearest.label], reach);
    for (const key of keys) {
        if (!/^[a-z]$/.test(key.label ?? ""))
            continue;
        const value = key.distance - gain(letters[key.label], reach);
        if (value < score) {
            best = key;
            score = value;
        }
    }
    return best;
}
