.pragma library

function normalize(value) {
    const base = String(value || "").trim().replace(/-/g, "_").split(/[.@]/)[0].toLowerCase();
    return base === "it" || base.startsWith("it_") ? "it_IT" : "en_US";
}

function configValues(text) {
    const values = {};
    for (const line of String(text || "").split(/\r?\n/)) {
        // locale.conf is assignment data, never shell code to execute.
        const match = line.match(/^\s*(LANG|LC_MESSAGES|LC_TIME)\s*=\s*(?:"([^"\n]*)"|'([^'\n]*)'|([^\s#"']+))\s*(?:#.*)?$/);
        if (match) values[match[1]] = match[2] ?? match[3] ?? match[4];
    }
    return values;
}

// C and POSIX name no language: they fall through to the next source.
function named(value) {
    return !!value && !/^(C|POSIX)([._@]|$)/i.test(String(value).trim());
}

// The session's own locale first (GDM sets it from the user's language), then the system's /etc/locale.conf.
function languageFromConfig(text, environment) {
    const values = configValues(text);
    const env = environment || {};
    return normalize([env.LC_ALL, env.LC_MESSAGES, env.LANG, values.LC_MESSAGES, values.LANG].find(named));
}

// Dates, times and numbers follow LC_TIME, apart from the message language: en_GB gets a 24-hour clock and
// weeks from Monday in an English UI. A name Qt can take (language, optional region), else the language.
function regionFromConfig(text, environment, language) {
    const values = configValues(text);
    const env = environment || {};
    const value = [env.LC_ALL, env.LC_TIME, env.LANG, values.LC_TIME, values.LANG].find(named);
    const base = String(value || "").trim().replace(/-/g, "_").split(/[.@]/)[0];
    return /^[a-z]{2,3}(_[A-Z]{2})?$/.test(base) ? base : language;
}

function format(message, args) {
    const values = args || [];
    return String(message).replace(/%([1-9][0-9]*)/g, (token, index) => {
        const value = values[Number(index) - 1];
        return value === undefined ? token : String(value);
    });
}

// Resolve a dotted semantic key through a nested JSON catalog.
function lookup(catalog, key) {
    let value = catalog;
    for (const segment of String(key).split(".")) {
        if (!value || typeof value !== "object" || !Object.prototype.hasOwnProperty.call(value, segment)) return undefined;
        value = value[segment];
    }
    return typeof value === "string" ? value : undefined;
}
