pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// The system time zone (timezone.py), read when the calendar panel opens and changed from it. suggested is the
// zone of the weather forecast when the forecast follows where the computer is (no weatherCity) and its offset
// differs from the system one.
Singleton {
    id: root
    readonly property string helper: Quickshell.env("HOME") + "/.local/libexec/desktop/timezone.py"
    property string current: ""
    // Minutes east of UTC.
    property int offset: 0
    property var zones: []
    property string error: ""
    // Bumped after a change, so clocks redraw before their next minute.
    property int revision: 0
    // A change was made in this session: apps already open keep the old zone until they restart.
    property bool changed: false
    readonly property bool busy: setter.running
    readonly property var suggested: {
        const zone = Weather.data.timezone ?? "";
        if (Config.weatherCity !== "" || zone === "" || zone === current)
            return null;
        const entry = zones.find(candidate => candidate.name === zone);
        return entry && entry.offset !== offset ? entry : null;
    }
    function refresh() {
        if (!reader.running)
            reader.running = true;
    }
    function set(zone) {
        if (setter.running || zone === current)
            return;
        error = "";
        setter.command = ["python3", helper, "set", zone];
        setter.running = true;
    }
    // UTC, UTC+1, UTC−5, UTC+5:30.
    function label(minutes) {
        if (minutes === 0)
            return I18n.tr("timezone.utc");
        const value = Math.abs(minutes);
        const rest = value % 60;
        return I18n.tr("timezone.offset", [(minutes < 0 ? "−" : "+") + Math.floor(value / 60) + (rest ? ":" + String(rest).padStart(2, "0") : "")]);
    }
    // America/Argentina/Buenos_Aires as America / Argentina / Buenos Aires.
    function displayName(name) {
        return name.replace(/_/g, " ").replace(/\//g, " / ");
    }
    Process {
        id: reader
        command: ["python3", root.helper, "list"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const value = JSON.parse(text);
                    root.current = value.current;
                    root.offset = value.offset ?? 0;
                    root.zones = value.zones;
                } catch (failure) {}
            }
        }
    }
    Process {
        id: setter
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const value = JSON.parse(text);
                    root.current = value.current;
                    root.offset = value.offset ?? root.offset;
                    // The JavaScript engine keeps the offset it read; Qt itself follows /etc/localtime.
                    Date.timeZoneUpdated();
                    root.revision += 1;
                    root.changed = true;
                } catch (failure) {}
            }
        }
        stderr: StdioCollector {
            onStreamFinished: {
                if (text.trim() !== "")
                    root.error = text.trim();
            }
        }
    }
}
