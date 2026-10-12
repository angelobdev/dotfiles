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

    SidePanelCard {
        ColumnLayout {
            anchors { fill: parent; margins: 16 }
            spacing: 14
            PanelHeader { Layout.fillWidth: true; title: "Batteria ed energia" }
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true; contentWidth: availableWidth; clip: true
                ColumnLayout {
                    width: parent.width; spacing: 12
                    RowLayout {
                        Icon { name: root.charging ? "battery-charging" : "battery"; Layout.preferredWidth: 30; Layout.preferredHeight: 30 }
                        Text { text: root.available ? Math.round(root.battery.percentage * 100) + "%" : "Nessuna batteria"; font.pixelSize: 36; font.family: Theme.font; color: Theme.text }
                    }
                    Text { visible: root.available; text: root.stateLabel; color: Theme.muted }
                    ProgressBar { Layout.fillWidth: true; visible: root.available; from: 0; to: 1; value: root.battery?.percentage ?? 0; palette.highlight: Theme.accent }
                    GridLayout {
                        visible: root.available; Layout.fillWidth: true
                        columns: 2; columnSpacing: 12; rowSpacing: 12
                        Text { text: root.charging ? "Potenza di ricarica" : root.discharging ? "Consumo" : "Flusso di energia"; color: Theme.muted; font.pixelSize: 12 }
                        Text { text: Math.abs(root.battery?.changeRate ?? 0).toFixed(1) + " W"; color: Theme.text; font.pixelSize: 12; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight }
                        Text { text: root.charging ? "Alla carica completa" : "Autonomia residua"; color: Theme.muted; font.pixelSize: 12 }
                        Text { text: root.charging ? root.duration(root.battery?.timeToFull) : root.discharging ? root.duration(root.battery?.timeToEmpty) : root.stateLabel; color: Theme.text; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.Wrap; horizontalAlignment: Text.AlignRight }
                        Text { text: "Energia disponibile"; color: Theme.muted; font.pixelSize: 12 }
                        Text { text: (root.battery?.energy ?? 0).toFixed(1) + " / " + (root.battery?.energyCapacity ?? 0).toFixed(1) + " Wh"; color: Theme.text; font.pixelSize: 12; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight }
                    }
                    Heading { text: "Profilo energetico"; font.pixelSize: 14; Layout.topMargin: 6 }
                    ActionButton { Layout.fillWidth: true; alignLeft: true; leftPadding: 12; iconName: "leaf"; text: "Risparmio energetico"; highlighted: PowerProfiles.profile === PowerProfile.PowerSaver; onClicked: PowerProfiles.profile = PowerProfile.PowerSaver }
                    ActionButton { Layout.fillWidth: true; alignLeft: true; leftPadding: 12; iconName: "balanced"; text: "Bilanciato"; highlighted: PowerProfiles.profile === PowerProfile.Balanced; onClicked: PowerProfiles.profile = PowerProfile.Balanced }
                    ActionButton { Layout.fillWidth: true; alignLeft: true; leftPadding: 12; iconName: "performance"; text: "Prestazioni"; enabled: PowerProfiles.hasPerformanceProfile; highlighted: PowerProfiles.profile === PowerProfile.Performance; onClicked: PowerProfiles.profile = PowerProfile.Performance }
                    Text { Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; color: Theme.muted; text: "Potenza e tempi sono stime aggiornate dal sistema." }
                }
            }
        }
    }
}
