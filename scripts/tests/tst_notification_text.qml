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

    function test_long_bodies_are_cut() {
        const body = "x".repeat(NotificationText.MAX_LENGTH + 100);
        compare(NotificationText.styled(body).length, NotificationText.MAX_LENGTH + 1);
    }
}
