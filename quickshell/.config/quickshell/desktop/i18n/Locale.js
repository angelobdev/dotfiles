.pragma library

function normalize(value) {
    const base = String(value || "").trim().replace(/-/g, "_").split(/[.@]/)[0].toLowerCase();
    return base === "it" || base.startsWith("it_") ? "it_IT" : "en_US";
}

function languageFromConfig(text, environment) {
    const values = {};
    for (const line of String(text || "").split(/\r?\n/)) {
        // locale.conf is assignment data, never shell code to execute.
        const match = line.match(/^\s*(LANG|LC_MESSAGES)\s*=\s*(?:"([^"\n]*)"|'([^'\n]*)'|([^\s#"']+))\s*(?:#.*)?$/);
        if (match) values[match[1]] = match[2] ?? match[3] ?? match[4];
    }
    const fallback = environment || {};
    return normalize(values.LC_MESSAGES || values.LANG || fallback.LC_ALL || fallback.LC_MESSAGES || fallback.LANG);
}

function format(message, args) {
    const values = args || [];
    return String(message).replace(/%([1-9][0-9]*)/g, (token, index) => {
        const value = values[Number(index) - 1];
        return value === undefined ? token : String(value);
    });
}
