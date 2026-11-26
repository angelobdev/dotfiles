import QtQuick
import "../.."
import "../../services"
import ".."

// The weather now (the calendar panel shows the rest); a click opens the calendar.
BarButton {
    id: root
    property var bar
    readonly property bool shown: Weather.enabled && Weather.ready
    iconName: Weather.ready ? Weather.icon(Weather.data.current.code, Weather.data.current.day) : "cloud"
    text: Weather.ready ? Weather.data.current.temp + "°" : ""
    tooltip: Weather.ready ? Weather.condition(Weather.data.current.code) + (Weather.data.place ? " · " + Weather.data.place : "") : I18n.tr("bar.widgets.weather.name")
    onClicked: ShellState.toggle("calendar", root.bar.screen)
    Component.onCompleted: Weather.refresh()
    // Weather moves slowly: once every half hour while the widget is on the bar.
    Timer {
        interval: 30 * 60 * 1000
        repeat: true
        running: Weather.enabled
        onTriggered: Weather.refresh()
    }
}
