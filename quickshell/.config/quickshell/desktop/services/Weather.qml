pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import ".."

// Weather for the calendar panel (weather.py: Open-Meteo, the place from GeoClue or Config.weatherCity),
// asked when the panel opens; weather.py keeps it 30 minutes, so opening it often costs nothing.
Singleton {
    id: root
    property var data: ({})
    readonly property bool ready: !!data.current
    readonly property bool enabled: Config.weatherEnabled

    function refresh() {
        if (enabled && !reader.running)
            reader.running = true;
    }
    // WMO weather codes, as Open-Meteo reports them.
    function kind(code) {
        if (code === 0)
            return "clear";
        if (code <= 2)
            return "partly";
        if (code === 3)
            return "cloudy";
        if (code === 45 || code === 48)
            return "fog";
        if (code >= 51 && code <= 57)
            return "drizzle";
        if (code >= 61 && code <= 67)
            return "rain";
        if (code >= 80 && code <= 82)
            return "showers";
        if (code >= 71 && code <= 77 || code === 85 || code === 86)
            return "snow";
        return code >= 95 ? "storm" : "cloudy";
    }
    function icon(code, day) {
        return ({
                clear: day === false ? "night" : "sun",
                partly: day === false ? "cloud" : "cloud-sun",
                cloudy: "cloud",
                fog: "fog",
                drizzle: "rain",
                rain: "rain",
                showers: "rain",
                snow: "snow",
                storm: "storm"
            })[kind(code)];
    }
    function condition(code) {
        return ({
                clear: I18n.tr("weather.conditions.clear"),
                partly: I18n.tr("weather.conditions.partly"),
                cloudy: I18n.tr("weather.conditions.cloudy"),
                fog: I18n.tr("weather.conditions.fog"),
                drizzle: I18n.tr("weather.conditions.drizzle"),
                rain: I18n.tr("weather.conditions.rain"),
                showers: I18n.tr("weather.conditions.showers"),
                snow: I18n.tr("weather.conditions.snow"),
                storm: I18n.tr("weather.conditions.storm")
            })[kind(code)];
    }
    Process {
        id: reader
        command: ["python3", Quickshell.env("HOME") + "/.local/libexec/desktop/weather.py", "now"].concat(Config.weatherCity !== "" ? [Config.weatherCity] : [])
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const value = JSON.parse(text);
                    if (value && typeof value === "object")
                        root.data = value;
                } catch (failure) {}
            }
        }
    }
}
