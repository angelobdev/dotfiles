import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
Overlay {
    panelName: "audio"
    Card {
        anchors.centerIn: parent
        width: Math.min(620, parent.width - 48)
        height: Math.min(640, parent.height - 96)
        ColumnLayout {
            anchors { fill: parent; margins: 22 }
            spacing: 14
            Heading { text: "Volume e dispositivi" }
            ScrollView {
                Layout.fillWidth: true; Layout.fillHeight: true
                contentWidth: availableWidth; clip: true
                ColumnLayout {
                    width: parent.width; spacing: 12
                    Heading { text: "Uscita" }
                    RowLayout {
                        ActionButton { iconName: Audio.muted ? "volume-muted" : "volume-high"; tooltip: "Attiva/disattiva audio"; enabled: !!Audio.sink; highlighted: Audio.muted; onClicked: Audio.toggleMute() }
                        Slider { Layout.fillWidth: true; from: 0; to: 1; value: Audio.volume / 100; enabled: !!Audio.sink; onMoved: Audio.setVolume(value) }
                        Text { text: Audio.volume + "%"; color: Theme.text; Layout.preferredWidth: 44 }
                    }
                    Repeater {
                        model: Audio.outputs
                        ActionButton {
                            required property var modelData
                            Layout.fillWidth: true; alignLeft: true; implicitHeight: 42
                            text: modelData.description || modelData.name; iconName: "volume-high"
                            highlighted: Audio.sink?.id === modelData.id
                            tooltip: modelData.name
                            onClicked: Audio.selectOutput(modelData)
                        }
                    }
                    Text { visible: Audio.outputs.length === 0; text: "Nessuna uscita audio disponibile"; color: Theme.muted }
                    Heading { text: "Ingresso"; Layout.topMargin: 12 }
                    RowLayout {
                        ActionButton { iconName: "microphone"; tooltip: "Attiva/disattiva microfono"; enabled: !!Audio.source; highlighted: Audio.source?.audio?.muted ?? false; onClicked: Audio.toggleMic() }
                        Slider { Layout.fillWidth: true; from: 0; to: 1; value: Audio.inputVolume / 100; enabled: !!Audio.source; onMoved: Audio.setInputVolume(value) }
                        Text { text: Audio.inputVolume + "%"; color: Theme.text; Layout.preferredWidth: 44 }
                    }
                    Repeater {
                        model: Audio.inputs
                        ActionButton {
                            required property var modelData
                            Layout.fillWidth: true; alignLeft: true; implicitHeight: 42
                            text: modelData.description || modelData.name; iconName: "microphone"
                            highlighted: Audio.source?.id === modelData.id
                            tooltip: modelData.name
                            onClicked: Audio.selectInput(modelData)
                        }
                    }
                    Text { visible: Audio.inputs.length === 0; text: "Nessun ingresso audio disponibile"; color: Theme.muted }
                    Text { Layout.fillWidth: true; wrapMode: Text.Wrap; text: "Seleziona il dispositivo predefinito. Il routing degli stream è gestito da WirePlumber."; color: Theme.muted; font.pixelSize: 12 }
                }
            }
            ActionButton { text: "Chiudi"; onClicked: ShellState.close() }
        }
    }
}
