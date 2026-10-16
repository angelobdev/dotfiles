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
    function control(action) {
        const target = player;
        const commands = {
            "play-pause": ["canTogglePlaying", "togglePlaying"],
            "play": ["canPlay", "play"],
            "pause": ["canPause", "pause"],
            "next": ["canGoNext", "next"],
            "previous": ["canGoPrevious", "previous"],
            "stop": ["canControl", "stop"]
        };
        const command = commands[action];
        if (!target || !target.canControl || !command || !target[command[0]])
            return false;
        target[command[1]]();
        return true;
    }
    onPlayersChanged: if (!players.some(p => p.dbusName === selectedName))
        selectedName = ""
}
