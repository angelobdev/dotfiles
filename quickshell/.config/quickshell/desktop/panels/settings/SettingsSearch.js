.pragma library
.import "../../SettingsSchema.js" as Schema

// The search of the Settings sidebar (panels/SettingsPanel.qml): an index of the sections, the tabs of Appearance
// and System and every option of SettingsSchema.js, in the language shown, and the matching. Each entry has a path
// (section, group, option; or section, tab; or the section alone), shown as "Section › Group › Option", and what
// opening it needs: section, tab ("" for the one the section remembers) and key (an option, "" for a page).

// The tabs of the sections that have them (panels/theming/ThemingView.qml, panels/system/SystemView.qml).
const tabs = {
    appearance: [
        { name: "theme", labelKey: "theming.tabs.theme" },
        { name: "layout", labelKey: "theming.tabs.layout" },
        { name: "wallpaper", labelKey: "theming.tabs.wallpaper" },
        { name: "font", labelKey: "theming.tabs.font" },
        { name: "icons", labelKey: "theming.tabs.icons" },
        { name: "cursors", labelKey: "theming.tabs.cursors" }
    ],
    system: [
        { name: "about", labelKey: "settings.system.about" },
        { name: "updates", labelKey: "settings.system.updates" },
        { name: "profiles", labelKey: "settings.system.profiles" },
        { name: "plugins", labelKey: "settings.system.plugins" },
        { name: "advanced", labelKey: "settings.system.advanced" }
    ]
};

// Words for what the schema does not list: the pages built by hand ("section" or "section/tab"), and the groups
// that Keyboard and Power add below their options. A comma-separated list in each catalog.
const keywords = {
    network: "settings.search.keywords.network",
    bluetooth: "settings.search.keywords.bluetooth",
    displays: "settings.search.keywords.displays",
    sound: "settings.search.keywords.sound",
    power: "settings.search.keywords.power",
    assistant: "settings.search.keywords.assistant",
    keyboard: "settings.search.keywords.keyboard",
    "appearance/theme": "settings.search.keywords.appearance.theme",
    "appearance/layout": "settings.search.keywords.appearance.layout",
    "appearance/wallpaper": "settings.search.keywords.appearance.wallpaper",
    "appearance/font": "settings.search.keywords.appearance.font",
    "appearance/icons": "settings.search.keywords.appearance.icons",
    "appearance/cursors": "settings.search.keywords.appearance.cursors",
    "system/about": "settings.search.keywords.system.about",
    "system/updates": "settings.search.keywords.system.updates",
    "system/profiles": "settings.search.keywords.system.profiles",
    "system/plugins": "settings.search.keywords.system.plugins",
    "system/advanced": "settings.search.keywords.system.advanced"
};

// How much a query word counts where it is found: in the label of the entry, in the rest of its path (section,
// group), or in its description and keywords. A word found inside another word counts half.
const weights = { label: 4, path: 2, text: 1 };

// Lower case, without accents: "Modalità" and "modalita" are the same.
function fold(text) {
    return String(text ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

// The words of a text, folded; punctuation, symbols and spaces separate them ("Wi-Fi" is "wi", "fi").
function words(text) {
    return fold(text).split(/[^0-9a-zß-öø-ÿĀ-῿Ⰰ-퟿]+/).filter(word => word !== "");
}

// A field to search: its words, and each tail of them run together, so "wifi" finds "Wi-Fi".
function field(text) {
    const list = words(text);
    return list.map((word, at) => list.slice(at).join(""));
}

// 1: a word of the field starts with it; 0.5: it is inside one (three letters or more); 0: not there.
function found(tails, word) {
    if (tails.some(tail => tail.startsWith(word)))
        return 1;
    return word.length >= 3 && tails.some(tail => tail.includes(word)) ? 0.5 : 0;
}

function entry(section, tab, key, path, text) {
    return {
        id: [section, tab, key].join("/"),
        section: section,
        tab: tab,
        key: key,
        path: path,
        label: path[path.length - 1],
        start: words(path[path.length - 1]).join(" "),
        fields: {
            label: field(path[path.length - 1]),
            path: field(path.slice(0, -1).join(" ")),
            text: field(text)
        }
    };
}

// The index in the language of tr (I18n.tr). sections: the sections shown, in sidebar order, each with its name
// and labelKey (SettingsPanel.sections); the options of a section left out (the assistant, not installed) are too.
function entries(tr, sections) {
    const list = [];
    for (const section of sections) {
        const title = tr(section.labelKey);
        list.push(entry(section.name, "", "", [title], keywords[section.name] ? tr(keywords[section.name]) : ""));
        for (const tab of tabs[section.name] ?? []) {
            const name = section.name + "/" + tab.name;
            list.push(entry(section.name, tab.name, "", [title, tr(tab.labelKey)], keywords[name] ? tr(keywords[name]) : ""));
        }
    }
    for (const section of sections) {
        const title = tr(section.labelKey);
        for (const option of Schema.forSection(section.name)) {
            const path = [title, tr(Schema.groupKey(option.group)), tr(Schema.labelKey(option))];
            list.push(entry(section.name, "", option.key, path, option.hint ? tr(Schema.hintKey(option)) : ""));
        }
    }
    return list;
}

// How well an entry matches the words of a query; 0 when one of them is nowhere.
function score(item, query, start) {
    let total = 0;
    for (const word of query) {
        let best = 0;
        for (const name in weights)
            best = Math.max(best, weights[name] * found(item.fields[name], word));
        if (best === 0)
            return 0;
        total += best;
    }
    // The label begins with what was typed: "font" puts the Font tab before "Use the monospace font everywhere".
    return item.start.startsWith(start) ? total + 1 : total;
}

// The entries matching every word of the query, best first; equal ones keep the order of the index (sections and
// tabs, then options in sidebar order).
function find(index, query) {
    const typed = words(query);
    if (typed.length === 0)
        return [];
    const start = typed.join(" ");
    return index.map((item, at) => ({
                item: item,
                at: at,
                score: score(item, typed, start)
            })).filter(match => match.score > 0).sort((a, b) => b.score - a.score || a.at - b.at).map(match => match.item);
}
