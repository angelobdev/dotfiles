import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/i18n/Locale.js" as LocaleData

TestCase {
    name: "Locale"

    function test_the_session_language_comes_first() {
        compare(LocaleData.languageFromConfig('LANG="en_US.UTF-8"', { LANG: "it_IT.UTF-8" }), "it_IT");
        compare(LocaleData.languageFromConfig('LANG="it_IT.UTF-8"', { LANG: "C.UTF-8" }), "it_IT");
        compare(LocaleData.languageFromConfig("", {}), "en_US");
    }

    // An English UI with British dates: 24-hour clock and weeks from Monday.
    function test_dates_follow_lc_time() {
        const region = LocaleData.regionFromConfig('LANG="en_GB.UTF-8"', {}, "en_US");
        compare(region, "en_GB");
        compare(Qt.locale(region).firstDayOfWeek, Locale.Monday);
        verify(Qt.locale(region).timeFormat(Locale.ShortFormat).indexOf("AP") === -1);
        compare(LocaleData.regionFromConfig('LANG=it_IT.UTF-8\nLC_TIME=de_DE.UTF-8', {}, "it_IT"), "de_DE");
        compare(LocaleData.regionFromConfig("", { LANG: "en_US.UTF-8", LC_TIME: "it_IT.UTF-8" }, "en_US"), "it_IT");
    }

    function test_unusable_values_fall_back_to_the_language() {
        compare(LocaleData.regionFromConfig("LANG=C.UTF-8", {}, "en_US"), "en_US");
        compare(LocaleData.regionFromConfig("LANG=x;rm", {}, "it_IT"), "it_IT");
    }
}
