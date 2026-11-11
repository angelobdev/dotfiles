import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/panels/settings/SettingsSearch.js" as Search

TestCase {
    name: "SettingsSearch"
    // A small catalog: the real ones are not readable from here; test_settings.py checks the keys exist.
    readonly property var catalog: ({
            "settings.sections.desktop": "Desktop",
            "settings.sections.sound": "Sound",
            "settings.sections.appearance": "Appearance",
            "settings.sections.privacy": "Privacy",
            "settings.groups.dock": "Dock",
            "settings.groups.bar": "Bar",
            "settings.options.dockEnabled": "Show the dock",
            "settings.options.dockIconSize": "Icon size",
            "settings.options.barMedia": "Media controls in the bar",
            "settings.hints.workspaceScroll": "Scrolling over the bar switches workspace",
            "settings.options.workspaceScroll": "Scroll to switch workspace",
            "settings.search.keywords.sound": "volume, microphone, speaker, output, input",
            "settings.search.keywords.appearance.font": "fonts, text size, monospace",
            "settings.search.keywords.appearance.wallpaper": "background, image",
            "theming.tabs.font": "Font",
            "theming.tabs.wallpaper": "Wallpaper",
            "theming.tabs.theme": "Theme"
        })
    readonly property var sections: [
        {
            name: "sound",
            labelKey: "settings.sections.sound"
        },
        {
            name: "appearance",
            labelKey: "settings.sections.appearance"
        },
        {
            name: "desktop",
            labelKey: "settings.sections.desktop"
        }
    ]

    function tr(key) {
        return catalog[key] ?? key;
    }
    function index(sectionList) {
        return Search.entries(tr, sectionList ?? sections);
    }
    function ids(query) {
        return Search.find(index(), query).map(item => item.id);
    }

    function test_foldIgnoresCaseAndAccents() {
        compare(Search.fold("Modalità ÉCRAN"), "modalita ecran");
        compare(Search.words("Wi-Fi · rete’s"), ["wi", "fi", "rete", "s"]);
    }

    function test_entriesHoldSectionsTabsAndOptions() {
        const list = index();
        const sound = list.find(item => item.id === "sound//");
        compare(sound.path, ["Sound"]);
        const font = list.find(item => item.id === "appearance/font/");
        compare(font.path, ["Appearance", "Font"]);
        compare(font.tab, "font");
        const dock = list.find(item => item.key === "dockIconSize");
        compare(dock.path, ["Desktop", "Dock", "Icon size"]);
        compare(dock.section, "desktop");
        compare(dock.tab, "");
    }

    function test_leftOutSectionsAreNotIndexed() {
        const list = index([sections[0]]);
        verify(!list.some(item => item.section === "desktop"));
        verify(!list.some(item => item.section === "privacy"));
    }

    function test_findIsCaseAndAccentInsensitive() {
        compare(ids("DOCK")[0], ids("dock")[0]);
        compare(ids("Ïcön sïze"), ["desktop//dockIconSize"]);
    }

    function test_everyWordMustMatch() {
        compare(ids("dock size"), ["desktop//dockIconSize"]);
        compare(ids("dock volume"), []);
        compare(ids("   "), []);
    }

    function test_keywordsFindHandWrittenPages() {
        compare(ids("microphone"), ["sound//"]);
        compare(ids("background"), ["appearance/wallpaper/"]);
        compare(ids("mono"), ["appearance/font/"]);
    }

    function test_labelsRankAboveDescriptionsAndKeywords() {
        // "bar" is the label of barMedia, the group of the others in Bar, and only the hint of workspaceScroll.
        const found = ids("bar");
        compare(found[0], "desktop//barMedia");
        verify(found.indexOf("desktop//barMedia") < found.indexOf("desktop//workspaceScroll"));
        // "font": the Font tab (its label) before nothing else; "size": the Dock icon size label before the font keywords.
        compare(ids("font")[0], "appearance/font/");
        const size = ids("size");
        compare(size[0], "desktop//dockIconSize");
        verify(size.includes("appearance/font/"));
    }

    function test_wordsMatchAtTheirStartFirst() {
        const label = Search.field("Scroll to switch workspace");
        compare(Search.found(label, "work"), 1);
        // Inside a word counts half, and only from three letters on.
        compare(Search.found(label, "space"), 0.5);
        compare(Search.found(label, "ac"), 0);
        compare(Search.found(label, "volume"), 0);
        // "space" is inside the workspaceScroll label (2) and starts nothing; still found.
        verify(ids("space").includes("desktop//workspaceScroll"));
        compare(ids("ze"), []);
    }

    function test_joinedWordsMatch() {
        compare(Search.find(Search.entries(key => key === "settings.sections.sound" ? "Wi-Fi" : tr(key), [sections[0]]), "wifi").map(item => item.id), ["sound//"]);
    }
}
