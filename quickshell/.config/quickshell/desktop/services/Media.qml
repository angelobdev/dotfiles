pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.Mpris

Singleton {
    id: root
    property string selectedName: ""
    readonly property var players: Mpris.players.values
    readonly property var player: players.find(p => p.dbusName === selectedName) ?? players.find(p => p.isPlaying) ?? players[0] ?? null
    function select(name) {
        selectedName = name;
    }
    onPlayersChanged: if (!players.some(p => p.dbusName === selectedName))
        selectedName = ""
}
