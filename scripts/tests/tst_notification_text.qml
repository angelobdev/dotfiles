import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/notifications/NotificationText.js" as NotificationText

TestCase {
    name: "NotificationText"

    function test_the_styled_subset_is_kept() {
        compare(NotificationText.styled("<b>bold</b> <strong>x</strong> <em>y</em><br/>z"), "<b>bold</b> <b>x</b> <i>y</i><br>z");
    }

    function test_other_tags_and_attributes_go() {
        compare(NotificationText.styled("<a href=\"https://example.com\">link</a> <img src=\"x.png\"/>"), "link ");
    }

    // Plain-text bodies: the text between a < and a > is no tag and stays.
    function test_angle_brackets_in_plain_text_are_shown() {
        compare(NotificationText.styled("a < b and c > d"), "a &lt; b and c &gt; d");
        compare(NotificationText.styled("<3 -> ok"), "&lt;3 -&gt; ok");
    }

    // An & that starts no entity is escaped; real entities pass through.
    function test_bare_ampersands_are_shown() {
        compare(NotificationText.styled("Q&A with AT&T"), "Q&amp;A with AT&amp;T");
        compare(NotificationText.styled("https://x.com/?a=1&b=2"), "https://x.com/?a=1&amp;b=2");
        compare(NotificationText.styled("Tom & Jerry"), "Tom &amp; Jerry");
        compare(NotificationText.styled("&amp; &#39; &#x27; &eacute;"), "&amp; &#39; &#x27; &eacute;");
    }

    function test_long_bodies_are_cut() {
        const body = "x".repeat(NotificationText.MAX_LENGTH + 100);
        compare(NotificationText.styled(body).length, NotificationText.MAX_LENGTH + 1);
    }

    function test_age_counts_minutes_then_hours_of_the_same_day() {
        const now = new Date(2026, 10, 11, 15, 0).getTime();
        compare(NotificationText.age(now - 30 * 1000, now), {
            unit: "now",
            count: 0
        });
        // A clock that ran ahead still reads as now.
        compare(NotificationText.age(now + 5000, now).unit, "now");
        compare(NotificationText.age(now - 60 * 1000, now), {
            unit: "minutes",
            count: 1
        });
        compare(NotificationText.age(now - 59 * 60 * 1000, now).count, 59);
        compare(NotificationText.age(now - 60 * 60 * 1000, now), {
            unit: "hours",
            count: 1
        });
        compare(NotificationText.age(new Date(2026, 10, 11, 0, 5).getTime(), now), {
            unit: "hours",
            count: 14
        });
    }

    function test_age_names_yesterday_then_a_date() {
        const now = new Date(2026, 10, 11, 0, 30).getTime();
        // Under an hour stays in minutes across midnight; past it, the day before is yesterday.
        compare(NotificationText.age(new Date(2026, 10, 10, 23, 50).getTime(), now).unit, "minutes");
        compare(NotificationText.age(new Date(2026, 10, 10, 23, 0).getTime(), now).unit, "yesterday");
        compare(NotificationText.age(new Date(2026, 10, 10, 0, 0).getTime(), now).unit, "yesterday");
        compare(NotificationText.age(new Date(2026, 10, 9, 23, 59).getTime(), now).unit, "date");
    }

    function test_age_of_an_unknown_time_is_null() {
        compare(NotificationText.age(undefined, Date.now()), null);
        compare(NotificationText.age(NaN, Date.now()), null);
    }

    // "Updates" / "Updates": the app line goes when it only repeats the title, whatever the case or spaces.
    function test_app_line_left_out_when_it_repeats_the_title() {
        verify(NotificationText.repeatsTitle("Aggiornamenti", "Aggiornamenti"));
        verify(NotificationText.repeatsTitle(" updates", "Updates "));
        verify(!NotificationText.repeatsTitle("Mail", "New message"));
        // An empty title repeats nothing, so the app line stays.
        verify(!NotificationText.repeatsTitle("", ""));
        verify(!NotificationText.repeatsTitle("Mail", "  "));
    }
}
