import QtQuick
import "Retry.js" as Retry

// The wait before a crashed watcher starts again: base after a run of a minute or more, doubled after each one
// that ended sooner (a helper that fails at start), up to a minute. The watcher calls started() and ended().
QtObject {
    id: root
    property int base: 2000
    property int failures: 0
    property double since: 0
    readonly property int interval: Retry.wait(base, failures)
    function started() {
        since = Date.now();
    }
    function ended() {
        failures = Retry.failures(failures, Date.now() - since);
    }
}
