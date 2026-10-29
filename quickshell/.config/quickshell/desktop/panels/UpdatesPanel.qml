import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ".."
import "../components"
import "../services"

// Available updates, opened from the bar icon that shows while there are any (or desktop-shell toggle
// updates): what would be updated, when it was checked, and Update, which opens a terminal for dnf and
// Flatpak (desktop-updates upgrade).
Overlay {
    id: root
    panelName: "updates"
    function when(milliseconds) {
        const date = new Date(milliseconds);
        if (date.toDateString() === new Date().toDateString())
            return I18n.tr("updates.checkedAt", [I18n.locale.toString(date, I18n.tr("assistant.timeFormat"))]);
        return I18n.tr("updates.checkedOn", [I18n.locale.toString(date, I18n.tr("assistant.dayTimeFormat"))]);
    }
    function summary() {
        if (Updates.count === 0)
            return I18n.tr("updates.upToDate");
        const parts = [];
        if (Updates.packages.length > 0)
            parts.push(I18n.plural("updates.summary.packages.one", "updates.summary.packages.other", Updates.packages.length));
        if (Updates.flatpaks.length > 0)
            parts.push(I18n.plural("updates.summary.flatpaks.one", "updates.summary.flatpaks.other", Updates.flatpaks.length));
        return parts.join(" · ");
    }
    component Entry: RowLayout {
        property string name
        property string version
        Layout.fillWidth: true
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: parent.name
            elide: Text.ElideRight
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: 12
            textFormat: Text.PlainText
        }
        Text {
            text: parent.version
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: 11
            textFormat: Text.PlainText
        }
    }
    SidePanelCard {
        height: Math.min(layout.implicitHeight + 2 * Theme.panelPadding, parent.height - 76)
        ColumnLayout {
            id: layout
            anchors.fill: parent
            anchors.margins: Theme.panelPadding
            spacing: 12
            PanelHeader {
                title: I18n.tr("updates.title")
                Layout.fillWidth: true
            }
            Text {
                Layout.fillWidth: true
                text: root.summary()
                color: Theme.text
                font.family: Theme.font
                font.pixelSize: 15
                wrapMode: Text.Wrap
            }
            Text {
                Layout.fillWidth: true
                visible: Updates.compositor
                text: I18n.tr("updates.compositor")
                color: Theme.danger
                font.family: Theme.font
                font.pixelSize: 12
                wrapMode: Text.Wrap
            }
            ScrollView {
                id: scroll
                visible: Updates.count > 0
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: Math.min(list.implicitHeight, 320)
                Layout.minimumHeight: Math.min(list.implicitHeight, 120)
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    id: list
                    width: scroll.availableWidth
                    spacing: 6
                    Heading {
                        visible: Updates.packages.length > 0
                        text: I18n.tr("updates.packagesHeading")
                        font.pixelSize: 13
                    }
                    Repeater {
                        model: Updates.packages
                        Entry {
                            required property var modelData
                            name: modelData.name
                            version: modelData.version
                        }
                    }
                    Heading {
                        visible: Updates.flatpaks.length > 0
                        text: I18n.tr("updates.flatpaksHeading")
                        font.pixelSize: 13
                        Layout.topMargin: 6
                    }
                    Repeater {
                        model: Updates.flatpaks
                        Entry {
                            required property var modelData
                            name: modelData.id
                            version: modelData.version
                        }
                    }
                }
            }
            Repeater {
                model: Updates.errors
                Text {
                    required property string modelData
                    Layout.fillWidth: true
                    text: modelData
                    color: Theme.danger
                    font.family: Theme.font
                    font.pixelSize: 11
                    wrapMode: Text.Wrap
                    textFormat: Text.PlainText
                }
            }
            Text {
                Layout.fillWidth: true
                text: Updates.checking ? I18n.tr("updates.checking") : Updates.checked > 0 ? root.when(Updates.checked) : I18n.tr("updates.never")
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: 11
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 8
                ActionButton {
                    Layout.fillWidth: true
                    text: I18n.tr("updates.checkNow")
                    enabled: !Updates.checking
                    onClicked: Updates.check()
                }
                ActionButton {
                    Layout.fillWidth: true
                    highlighted: true
                    iconName: "update"
                    text: I18n.tr("updates.install")
                    enabled: Updates.count > 0
                    onClicked: {
                        ShellState.close();
                        Updates.upgrade();
                    }
                }
            }
        }
    }
}
