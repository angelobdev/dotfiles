import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/notifications/NotificationDeck.js" as NotificationDeck

TestCase {
    name: "NotificationDeck"

    function card(id, appName, body) {
        return {
            id: id,
            appName: appName,
            body: body ?? ""
        };
    }

    function options(openDeck, heights) {
        return {
            openDeck: openDeck,
            heights: heights ?? {},
            fallback: 80,
            gap: 6,
            deckGap: 10
        };
    }

    function test_appsShareADeck() {
        compare(NotificationDeck.groupKey(card(1, "Signal Desktop")), "app:signal-desktop");
        compare(NotificationDeck.groupKey(card(2, "signal desktop")), "app:signal-desktop");
    }

    function test_browsersGroupBySite() {
        compare(NotificationDeck.groupKey(card(1, "Zen", "<a href=\"https://mail.example.com/inbox\">mail.example.com</a>\n\nNew mail")), "web:mail.example.com");
        compare(NotificationDeck.groupKey(card(2, "firefox", "www.youtube.com\n\nNew video")), "web:www.youtube.com");
        // No site in the body: the browser itself is the app.
        compare(NotificationDeck.groupKey(card(3, "Zen", "Download finished")), "app:zen");
        // A link is not a site unless its text says so.
        compare(NotificationDeck.groupKey(card(4, "Zen", "<a href=\"https://a.example.com\">click here</a>")), "app:zen");
    }

    function test_appsOtherThanBrowsersIgnoreTheBody() {
        compare(NotificationDeck.groupKey(card(1, "Mail", "example.com\n\nHello")), "app:mail");
    }

    function test_notifySendStandsAlone() {
        verify(NotificationDeck.groupKey(card(1, "notify-send")) !== NotificationDeck.groupKey(card(2, "notify-send")));
        verify(NotificationDeck.groupKey(card(1, "")) !== NotificationDeck.groupKey(card(2, "")));
    }

    function test_decksFollowTheirNewestCard() {
        const decks = NotificationDeck.group([card(5, "b"), card(4, "a"), card(3, "b"), card(2, "a")]);
        compare(decks.map(d => d.key), ["app:b", "app:a"]);
        compare(decks[0].items.map(i => i.id), [5, 3]);
        compare(decks[1].items.map(i => i.id), [4, 2]);
    }

    function test_closedDeckPeeks() {
        const decks = NotificationDeck.group([1, 2, 3, 4].map(id => card(id, "a")));
        const result = NotificationDeck.layout(decks, options("", {
            1: 100,
            2: 300
        }));
        const places = result.places;
        // Every card takes the height of the front one, whatever its own.
        compare(places[2].height, 100);
        compare(places[1].y, 0);
        compare(places[2].y, 10);
        compare(places[3].y, 20);
        compare(places[1].scale, 1);
        fuzzyCompare(places[2].scale, 0.965, 0.0001);
        fuzzyCompare(places[3].scale, 0.93, 0.0001);
        compare(places[2].opacity, 0.85);
        compare(places[3].opacity, 0.55);
        // The fourth card waits out of sight; the height counts only what is drawn.
        compare(places[4].opacity, 0);
        verify(!places[4].drawn);
        verify(places[1].front && !places[2].front);
        verify(places[1].z > places[2].z);
        compare(result.height, 120);
    }

    function test_openDeckIsAList() {
        const decks = NotificationDeck.group([card(1, "a"), card(2, "a"), card(3, "b")]);
        const result = NotificationDeck.layout(decks, options("app:a", {
            1: 100,
            2: 50,
            3: 80
        }));
        compare(result.places[1].y, 0);
        compare(result.places[2].y, 106);
        compare(result.places[2].height, 50);
        compare(result.places[2].scale, 1);
        compare(result.places[2].opacity, 1);
        // The next deck starts below the list.
        compare(result.places[3].y, 166);
        compare(result.height, 246);
    }

    function test_loneCardIsNotStacked() {
        const places = NotificationDeck.layout(NotificationDeck.group([card(1, "a"), card(2, "b"), card(3, "b")]), options("")).places;
        verify(!places[1].stacked);
        verify(places[2].stacked);
    }

    function test_deckAtFindsFrontCards() {
        const rects = NotificationDeck.layout(NotificationDeck.group([card(1, "a"), card(2, "a"), card(3, "b")]), options("")).rects;
        compare(rects[0].frontBottom, 80);
        compare(rects[1].top, 100);
        compare(NotificationDeck.deckAt(rects, 40, 6), "app:a");
        compare(NotificationDeck.deckAt(rects, 85, 6), "app:a");
        // The peek of the first deck belongs to neither front card.
        compare(NotificationDeck.deckAt(rects, 90, 6), "");
        compare(NotificationDeck.deckAt(rects, 95, 6), "app:b");
    }

    function test_collapseKeepsTheNewestOfClosedDecks() {
        const entries = [card(4, "a"), card(3, "b"), card(2, "a"), card(1, "b")];
        const closed = NotificationDeck.collapse(entries, []);
        compare(closed.entries.map(e => e.id), [4, 3]);
        compare(closed.counts[4], 2);
        compare(closed.keys[3], "app:b");
        const open = NotificationDeck.collapse(entries, ["app:a"]);
        compare(open.entries.map(e => e.id), [4, 2, 3]);
    }
}
