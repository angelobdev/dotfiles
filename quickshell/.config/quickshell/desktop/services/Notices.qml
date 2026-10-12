pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.Notifications
Singleton {
    id: root
    property bool quiet: false
    property var popupIds: []
    readonly property var popups: server.trackedNotifications.values.filter(n => popupIds.includes(n.id))
    readonly property var notifications: server.trackedNotifications
    NotificationServer {
        id: server
        bodySupported: true
        bodyMarkupSupported: false
        actionsSupported: true
        persistenceSupported: true
        onNotification: n => {
            n.tracked = true;
            if (!n.lastGeneration) root.popupIds = root.popupIds.filter(id => id !== n.id).concat(n.id).slice(-3);
        }
    }
    function hidePopup(id) { popupIds = popupIds.filter(value => value !== id); }
    function clear() {
        const items = server.trackedNotifications.values.slice();
        for (const n of items) n.dismiss();
    }
}
