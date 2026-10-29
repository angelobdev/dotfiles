pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.Notifications
import ".."

Singleton {
    id: root
    readonly property bool quiet: SessionState.quiet
    property var popupIds: []
    readonly property var popups: server.trackedNotifications.values.filter(n => popupIds.includes(n.id))
    readonly property var notifications: server.trackedNotifications
    // The history outlives shell restarts as archived entries: readable and removable, but without
    // actions, since the sending app bound those to the server that has gone.
    readonly property int historyLimit: 50
    readonly property real historyAge: 7 * 24 * 3600 * 1000
    property var archived: []
    property bool historyLoaded: false
    // Arrival times of live notifications, by id; the server keeps none.
    property var arrived: ({})
    readonly property int liveCount: server.trackedNotifications.values.length
    // Live notifications newest first, then the archive; ids keep delegates when the list changes.
    readonly property var entries: server.trackedNotifications.values.slice().reverse().concat(archived).slice(0, historyLimit)
    function setQuiet(value) {
        SessionState.set("quiet", value);
    }
    // IPC and the shortcut: "toggle", "on" or "off", with an OSD of the new state.
    function request(action) {
        if (!["toggle", "on", "off"].includes(action))
            return false;
        setQuiet(action === "toggle" ? !quiet : action === "on");
        Osd.showState(quiet ? "bell-off" : "bell", I18n.tr("notifications.doNotDisturb"), I18n.tr(quiet ? "common.on" : "common.off"));
        return true;
    }
    function hidePopup(id) {
        popupIds = popupIds.filter(value => value !== id);
    }
    function forget(id) {
        archived = archived.filter(entry => entry.id !== id);
        saveHistory.restart();
    }
    function clear() {
        const items = server.trackedNotifications.values.slice();
        for (const n of items)
            n.dismiss();
        archived = [];
        saveHistory.restart();
    }
    function archive(n) {
        const time = arrived[n.id] ?? Date.now();
        // Icons served by the notification itself (image://) do not survive the server.
        const icon = n.appIcon && !n.appIcon.startsWith("image:") ? n.appIcon : "";
        return {
            id: "archived-" + time + "-" + n.id,
            source: n.id,
            archived: true,
            appName: n.appName ?? "",
            appIcon: icon,
            desktopEntry: n.desktopEntry ?? "",
            summary: n.summary ?? "",
            body: n.body ?? "",
            time: time,
            actions: []
        };
    }
    onLiveCountChanged: saveHistory.restart()
    Timer {
        id: saveHistory
        interval: 500
        onTriggered: {
            // Until the file has been read, saving would replace the history with an empty one.
            if (!root.historyLoaded)
                return;
            const live = server.trackedNotifications.values.slice().reverse().map(n => root.archive(n));
            history.entries = live.concat(root.archived).slice(0, root.historyLimit).map(entry => ({
                        source: entry.source,
                        appName: entry.appName,
                        appIcon: entry.appIcon,
                        desktopEntry: entry.desktopEntry,
                        summary: entry.summary,
                        body: entry.body,
                        time: entry.time
                    }));
            historyFile.writeAdapter();
        }
    }
    FileView {
        id: historyFile
        path: SessionState.stateDir + "/notifications.json"
        atomicWrites: true
        printErrors: false
        adapter: JsonAdapter {
            id: history
            property var entries: []
        }
        onLoaded: {
            const now = Date.now();
            // A config reload keeps the live notifications; their saved copies are not archived again.
            const live = server.trackedNotifications.values.map(n => n.id);
            root.archived = Array.from(history.entries ?? []).filter(entry => entry && typeof entry.time === "number" && now - entry.time < root.historyAge && !live.includes(entry.source)).slice(0, root.historyLimit).map((entry, index) => Object.assign({}, entry, {
                    id: "archived-" + entry.time + "-" + index,
                    archived: true,
                    actions: []
                }));
            root.historyLoaded = true;
        }
        onLoadFailed: root.historyLoaded = true
    }
    NotificationServer {
        id: server
        bodySupported: true
        bodyMarkupSupported: true
        actionsSupported: true
        persistenceSupported: true
        onNotification: n => {
            n.tracked = true;
            root.arrived = Object.assign({}, root.arrived, {
                [n.id]: Date.now()
            });
            if (!n.lastGeneration)
                root.popupIds = root.popupIds.filter(id => id !== n.id).concat(n.id).slice(-3);
        }
    }
}
