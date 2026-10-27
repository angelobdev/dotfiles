pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "i18n/Locale.js" as LocaleData
import "i18n/Sources.js" as Sources

Singleton {
    id: root
    property string language: "en_US"
    readonly property var locale: Qt.locale(language)
    property var italian: ({})
    property var english: ({})

    function selectLanguage(text) {
        language = LocaleData.languageFromConfig(text, {
            LC_ALL: Quickshell.env("LC_ALL"),
            LC_MESSAGES: Quickshell.env("LC_MESSAGES"),
            LANG: Quickshell.env("LANG")
        });
    }
    function catalog(text) {
        try {
            const value = JSON.parse(text);
            if (value && typeof value === "object" && !Array.isArray(value))
                return value;
        } catch (error) {
            console.warn("Invalid translation catalog:", error);
        }
        return {};
    }
    function tr(key, args) {
        const selected = language === "it_IT" ? italian : english;
        return LocaleData.format(LocaleData.lookup(selected, key) ?? LocaleData.lookup(english, key) ?? key, args);
    }
    function plural(singular, plural, count, args) {
        return tr(count === 1 ? singular : plural, [count].concat(args || []));
    }
    function bindDescription(description) {
        let match = description.match(/^(Focus|Move) (left|right|up|down)$/);
        if (match)
            return tr(match[1] === "Focus" ? "bindings.focusDirection" : "bindings.moveDirection", [tr("directions." + match[2])]);
        match = description.match(/^Move to workspace (\d+)$/);
        if (match)
            return tr("bindings.moveToWorkspace", [match[1]]);
        const key = Sources.bindKeys[description];
        return typeof key === "string" ? tr(key) : description;
    }
    function networkDescription(description) {
        const key = Sources.networkKeys[description];
        return typeof key === "string" ? tr(key) : description;
    }
    FileView {
        id: systemLocale
        path: "/etc/locale.conf"
        blockLoading: true
        printErrors: false
        watchChanges: true
        onLoaded: root.selectLanguage(text())
        onLoadFailed: root.selectLanguage("")
        onFileChanged: reload()
    }
    FileView {
        id: itFile
        path: decodeURIComponent(Qt.resolvedUrl("i18n/it_IT.json").toString().replace(/^file:\/\//, ""))
        blockLoading: true
        watchChanges: true
        onLoaded: root.italian = root.catalog(text())
        onFileChanged: reload()
    }
    FileView {
        id: enFile
        path: decodeURIComponent(Qt.resolvedUrl("i18n/en_US.json").toString().replace(/^file:\/\//, ""))
        blockLoading: true
        watchChanges: true
        onLoaded: root.english = root.catalog(text())
        onFileChanged: reload()
    }
    Component.onCompleted: {
        selectLanguage(systemLocale.text());
        italian = catalog(itFile.text());
        english = catalog(enFile.text());
    }
}
