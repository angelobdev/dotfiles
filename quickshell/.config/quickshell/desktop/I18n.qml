pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "i18n/Locale.js" as LocaleData

Singleton {
    id: root
    property string language: "en_US"
    readonly property var locale: Qt.locale(language)
    property var italian: ({})
    property var english: ({})

    function selectLanguage(text) {
        language = LocaleData.languageFromConfig(text, {
            LC_ALL: Quickshell.env("LC_ALL"), LC_MESSAGES: Quickshell.env("LC_MESSAGES"), LANG: Quickshell.env("LANG")
        });
    }
    function catalog(text) {
        try {
            const value = JSON.parse(text);
            if (value && typeof value === "object" && !Array.isArray(value)) return value;
        } catch (error) { console.warn("Invalid translation catalog:", error); }
        return {};
    }
    function tr(message, args) {
        const selected = language === "it_IT" ? italian : english;
        return LocaleData.format(selected[message] ?? english[message] ?? message, args);
    }
    function plural(singular, plural, count, args) {
        return tr(count === 1 ? singular : plural, [count].concat(args || []));
    }
    function bindDescription(description) {
        let match = description.match(/^(Focus|Sposta) (left|right|up|down)$/);
        if (match) return tr(match[1] === "Focus" ? "Focus %1" : "Sposta %1", [tr("direction." + match[2])]);
        match = description.match(/^Sposta al workspace (\d+)$/);
        if (match) return tr("Sposta al workspace %1", [match[1]]);
        return tr(description);
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
