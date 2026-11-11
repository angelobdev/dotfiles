import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/services/LauncherRank.js" as Rank

TestCase {
    name: "LauncherRank"
    readonly property real now: 1800000000000
    readonly property real day: 24 * 60 * 60 * 1000

    function app(id, name, genericName, keywords) {
        return {
            id: id,
            name: name,
            genericName: genericName ?? "",
            keywords: keywords ?? []
        };
    }

    readonly property var apps: [app("firefox", "Firefox", "Web Browser", ["internet", "www"]), app("code", "Visual Studio Code", "Text Editor", ["development"]), app("files", "Files", "File Manager", ["folder"]), app("writer", "LibreOffice Writer", "Word Processor", ["document"]), app("fonts", "Fonts", "Font Viewer", []), app("kitty", "kitty", "Terminal Emulator", ["shell"]), app("settings", "Settings", "", ["preferences"]), app("calc", "Calculator", "", ["math"]), app("cafe", "Café Menu", "", [])]

    function names(query, history) {
        return Rank.rank(apps, query, history ?? {}, now).map(entry => entry.id);
    }

    function test_tiersInOrder() {
        const firefox = apps[0];
        const code = apps[1];
        compare(Rank.tier(firefox, "fire"), Rank.PREFIX);
        compare(Rank.tier(code, "studio"), Rank.WORD_START);
        compare(Rank.tier(code, "vsc"), Rank.WORD_START);
        compare(Rank.tier(code, "vscode"), Rank.WORD_START);
        compare(Rank.tier(code, "studio code"), Rank.WORD_START);
        compare(Rank.tier(firefox, "fox"), Rank.SUBSTRING);
        compare(Rank.tier(firefox, "ff"), Rank.SUBSEQUENCE);
        compare(Rank.tier(firefox, "browser"), Rank.OTHER_FIELDS);
        compare(Rank.tier(firefox, "www"), Rank.OTHER_FIELDS);
        compare(Rank.tier(firefox, "xyz"), Rank.NONE);
    }

    function test_camelCaseSplitsWords() {
        compare(Rank.words("LibreOffice Writer"), ["libre", "office", "writer"]);
        compare(Rank.tier(apps[3], "office"), Rank.WORD_START);
        compare(Rank.tier(apps[3], "low"), Rank.WORD_START);
    }

    function test_caseAndAccentsAreIgnored() {
        compare(Rank.tier(apps[0], "FIRE"), Rank.PREFIX);
        compare(Rank.tier(apps[8], "cafe"), Rank.PREFIX);
        compare(Rank.tier(apps[8], "  cafe "), Rank.PREFIX);
    }

    function test_emptyQueryIsAlphabeticalWithoutHistory() {
        compare(names(""), ["cafe", "calc", "files", "firefox", "fonts", "kitty", "writer", "settings", "code"]);
    }

    function test_emptyQueryPutsUsedAppsFirst() {
        const history = {
            kitty: [now - 3 * day],
            code: [now - 1000, now - 2000]
        };
        compare(names("", history), ["code", "kitty", "cafe", "calc", "files", "firefox", "fonts", "writer", "settings"]);
    }

    function test_betterTierWinsOverUse() {
        // "fi": Files and Firefox start with it, LibreOffice Writer has it inside a word; heavy use does not lift it.
        const history = {
            writer: [now - 1000, now - 2000, now - 3000]
        };
        compare(names("fi", history), ["files", "firefox", "writer"]);
    }

    function test_useBreaksTiesBeforeTheName() {
        // Settings has "f" only in its keyword "preferences": last.
        compare(names("f"), ["files", "firefox", "fonts", "cafe", "writer", "settings"]);
        compare(names("f", {
            fonts: [now - 1000],
            writer: [now - 1000]
        }), ["fonts", "files", "firefox", "writer", "cafe", "settings"]);
    }

    function test_subsequenceComesAfterSubstring() {
        // Israel has "ae" in a row, Aperture only spread out: Israel first, against the alphabet.
        const list = [app("a", "Aperture"), app("b", "Israel")];
        compare(Rank.tier(list[0], "ae"), Rank.SUBSEQUENCE);
        compare(Rank.rank(list, "ae", {}, now).map(entry => entry.id), ["b", "a"]);
    }

    function test_otherFieldsComeLast() {
        // A match in the generic name or the keywords only: after every match in a name.
        const list = [app("a", "Alpha", "Text tool"), app("b", "Zeta Text")];
        compare(Rank.rank(list, "text", {}, now).map(entry => entry.id), ["b", "a"]);
        compare(names("term"), ["kitty"]);
        compare(names("www"), ["firefox"]);
    }

    function test_scoreBuckets() {
        compare(Rank.score([], now), 0);
        compare(Rank.score([now - 1000], now), 100);
        compare(Rank.score([now - 2 * day], now), 70);
        compare(Rank.score([now - 10 * day], now), 40);
        compare(Rank.score([now - 60 * day], now), 20);
        compare(Rank.score([now - 100 * day], now), 0);
        compare(Rank.score([now - 1000, now - 2 * day, now - 10 * day], now), 210);
        // A launch dated after now (a clock moved back) counts as recent.
        compare(Rank.score([now + day], now), 100);
    }

    function test_recordKeepsTheLatestLaunches() {
        let history = {};
        for (let index = 0; index < 15; index++)
            history = Rank.record(history, "firefox", now - (15 - index) * 1000);
        compare(history.firefox.length, Rank.launchesKept);
        compare(history.firefox[Rank.launchesKept - 1], now - 1000);
    }

    function test_pruneForgetsOldAppsAndCapsTheCount() {
        const history = {
            old: [now - 100 * day],
            mixed: [now - 100 * day, now - day / 2]
        };
        for (let index = 0; index < Rank.appsKept + 5; index++)
            history["app" + index] = [now - 40 * day];
        const pruned = Rank.prune(history, now);
        verify(!("old" in pruned));
        compare(pruned.mixed, [now - day / 2]);
        compare(Object.keys(pruned).length, Rank.appsKept);
    }

    function test_parseAcceptsOnlyTheExpectedShape() {
        compare(Rank.parse("", now), {});
        compare(Rank.parse("not json", now), {});
        compare(Rank.parse("[1, 2]", now), {});
        compare(Rank.parse(JSON.stringify({
            apps: {
                firefox: [now - 2000, "x", now - 1000],
                bad: "y"
            }
        }), now), {
            firefox: [now - 2000, now - 1000]
        });
        const history = Rank.record({}, "kitty", now);
        compare(Rank.parse(Rank.serialize(history), now), history);
    }
}
