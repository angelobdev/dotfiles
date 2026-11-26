import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// What changed in the desktop: the changelog sections of the versions installed since the last one seen, opened once
// after an update (services/Release.qml), or the notes of the installed version from About.
Overlay {
    id: root
    panelName: "whatsnew"
    dialog: true
    Card {
        anchors.centerIn: parent
        width: Math.min(Theme.dialogMedium, parent.width - 48)
        height: Math.min(layout.implicitHeight + 2 * Theme.dialogPadding, parent.height - 96)
        ColumnLayout {
            id: layout
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 14
            PanelHeader {
                Layout.fillWidth: true
                title: Release.version === "" ? I18n.tr("whatsNew.title") : I18n.tr("whatsNew.titleVersion", [Release.version])
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: notes.implicitHeight
                contentWidth: availableWidth
                clip: true
                ColumnLayout {
                    id: notes
                    width: parent.width
                    spacing: 10
                    Repeater {
                        model: Release.sections
                        ColumnLayout {
                            id: entry
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            Layout.topMargin: index > 0 ? 8 : 0
                            spacing: 6
                            Heading {
                                section: true
                                text: entry.modelData.date === "" ? entry.modelData.version : I18n.tr("whatsNew.heading", [entry.modelData.version, entry.modelData.date])
                            }
                            // The changelog of this repository, written as Markdown for this view and for GitHub.
                            Text {
                                Layout.fillWidth: true
                                text: entry.modelData.notes
                                textFormat: Text.MarkdownText
                                wrapMode: Text.Wrap
                                color: Theme.text
                                linkColor: Theme.accent
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(13)
                                onLinkActivated: link => Qt.openUrlExternally(link)
                            }
                        }
                    }
                }
            }
            ActionButton {
                Layout.alignment: Qt.AlignRight
                text: I18n.tr("whatsNew.done")
                outlined: true
                highlighted: true
                onClicked: ShellState.close()
            }
        }
    }
}
