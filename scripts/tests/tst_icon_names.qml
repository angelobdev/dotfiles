import QtQuick
import QtTest
import Qt.labs.folderlistmodel
import "../../quickshell/.config/quickshell/desktop/components/IconNames.js" as IconNames

TestCase {
    name: "IconNames"
    when: glyphs.status === FolderListModel.Ready

    FolderListModel {
        id: glyphs
        folder: Qt.resolvedUrl("../../quickshell/.config/quickshell/desktop/assets/icons")
        nameFilters: ["*.svg"]
        showDirs: false
    }

    // Every bundled glyph has pack names, and no name points at a glyph that does not exist.
    function test_mapping_matches_the_bundled_glyphs() {
        const files = [];
        for (let i = 0; i < glyphs.count; i++)
            files.push(glyphs.get(i, "fileBaseName"));
        compare(Object.keys(IconNames.names).sort(), files.sort());
        for (const glyph of files)
            verify(IconNames.names[glyph].every(name => name.endsWith("-symbolic")), glyph);
    }

    function test_first_resolved_name_wins() {
        compare(IconNames.packSource("battery-50", name => name === "battery-good-symbolic" ? "/b.svg" : ""), "/b.svg");
        compare(IconNames.packSource("battery-50", () => ""), "");
        compare(IconNames.packSource("unknown", () => "/x.svg"), "");
    }
}
