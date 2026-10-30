# Notifications

[← Docs](../README.md)

Popups stack in decks per app, or per site for browsers, and a notification center keeps the history across restarts.

## Popups

- Notification popups with icons and formatted text (`b`, `i`, `u`, `s`, `strong`, `em`, `br`); left-click invokes the default action when present, right-click hides the popup while retaining the notification. Other actions remain buttons; in the notification center, **Delete** is red and aligned with the title, and the default action remains available as a button. History survives shell restarts as archived entries (see [Do Not Disturb, Keep awake and notification history](../guide/interface.md#do-not-disturb-keep-awake-and-notification-history)); a swipe or a long press dismisses or hides a notification by touch. Images and HTML attributes are stripped from the text.
- Notification popups stack in decks, newest on top: one deck per app, one per site for browsers, while plain `notify-send` calls stand alone. A closed deck draws up to three cards, those behind peeking under the front one, whose body is cut to two lines; a deck of one keeps six. Hovering a front card opens its deck as a list, one deck at a time. While the pointer is on the stack nothing expires and new cards wait (30 s at most). Cards are always hidden one by one. The notification center groups the same way: the newest entry of a group carries **N more** and **Show less**.

## History

The notification center keeps up to 50 notifications from the last 7 days across shell restarts. Those from before a restart are marked **Archived**: they can be read and deleted, but their action buttons are gone, because the sending application bound them to the previous notification server. **Clear all** removes live and archived ones.
