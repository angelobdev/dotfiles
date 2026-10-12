import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Services.UPower
import ".."
import "../components"
Overlay {
    id: root
    panelName: "battery"
    readonly property var battery: UPower.displayDevice
    readonly property bool available: (battery?.ready ?? false) && (battery?.isLaptopBattery ?? false)
    readonly property bool charging: battery?.state === UPowerDeviceState.Charging
    readonly property bool discharging: battery?.state === UPowerDeviceState.Discharging
    readonly property string stateLabel: {
        switch (battery?.state) {
        case UPowerDeviceState.Charging: return "In carica";
        case UPowerDeviceState.Discharging: return "Alimentazione a batteria";
        case UPowerDeviceState.FullyCharged: return "Carica completa";
        case UPowerDeviceState.Empty: return "Batteria scarica";
        case UPowerDeviceState.PendingCharge: return "Ricarica in attesa";
        case UPowerDeviceState.PendingDischarge: return "Scarica in attesa";
        default: return "Stato non disponibile";
        }
    }
    function duration(seconds) {
        if (!Number.isFinite(seconds) || seconds <= 0) return "Stima non disponibile";
        const minutes = Math.max(1, Math.round(seconds / 60));
        return (minutes >= 60 ? Math.floor(minutes / 60) + " h " : "") + (minutes % 60) + " min";
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(540, parent.width - 48)
        height: layout.implicitHeight + 44
        ColumnLayout {
            id: layout
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 22 }
            spacing: 14
            Heading { text: "Batteria ed energia" }
            Text { text: root.available ? Math.round(root.battery.percentage * 100) + "%" : "Nessuna batteria"; font.pixelSize: 42; font.family: Theme.font; color: Theme.text }
            Text { visible: root.available; text: root.stateLabel; color: Theme.muted }
            ProgressBar { Layout.fillWidth: true; visible: root.available; from: 0; to: 1; value: root.battery?.percentage ?? 0 }
            GridLayout {
                visible: root.available
                columns: 2; columnSpacing: 24; rowSpacing: 12
                Text { text: root.charging ? "Potenza di ricarica" : root.discharging ? "Consumo dalla batteria" : "Flusso di energia"; color: Theme.muted }
                Text { text: Math.abs(root.battery?.changeRate ?? 0).toFixed(1) + " W"; color: Theme.text }
                Text { text: root.charging ? "Alla carica completa" : "Autonomia residua"; color: Theme.muted }
                Text { text: root.charging ? root.duration(root.battery?.timeToFull) : root.discharging ? root.duration(root.battery?.timeToEmpty) : root.stateLabel; color: Theme.text }
                Text { text: "Energia disponibile"; color: Theme.muted }
                Text { text: (root.battery?.energy ?? 0).toFixed(1) + " / " + (root.battery?.energyCapacity ?? 0).toFixed(1) + " Wh"; color: Theme.text }
            }
            Heading { text: "Profilo energetico"; Layout.topMargin: 6 }
            RowLayout {
                ActionButton { text: "Risparmio"; highlighted: PowerProfiles.profile === PowerProfile.PowerSaver; onClicked: PowerProfiles.profile = PowerProfile.PowerSaver }
                ActionButton { text: "Bilanciato"; highlighted: PowerProfiles.profile === PowerProfile.Balanced; onClicked: PowerProfiles.profile = PowerProfile.Balanced }
                ActionButton { text: "Prestazioni"; enabled: PowerProfiles.hasPerformanceProfile; highlighted: PowerProfiles.profile === PowerProfile.Performance; onClicked: PowerProfiles.profile = PowerProfile.Performance }
            }
            Text { Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 12; color: Theme.muted; text: "Potenza e tempi sono stime UPower aggiornate dal sistema; possono richiedere alcuni istanti per stabilizzarsi." }
            ActionButton { text: "Chiudi"; onClicked: ShellState.close() }
        }
    }
}
