import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import "../.."
import "../../components"
import "../../services"

// The store page of the Theming panel (panels/ThemingPanel.qml), built the first time its tab shows.
ColumnLayout {
    id: page
    // The Theming panel: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: storeSearch
    spacing: 10
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        ActionButton {
            iconName: "arrow-left"
            text: I18n.tr("theming.tabs.icons")
            onClicked: page.panel.showTab("icons")
        }
        InputField {
            id: storeSearch
            Layout.fillWidth: true
            // A recreated panel shows the search its results are for.
            text: Store.query
            placeholderText: Store.kind === "cursors" ? I18n.tr("store.searchCursors") : I18n.tr("store.searchIcons")
            onAccepted: Store.search(Store.kind, text)
        }
    }
    Text {
        Layout.fillWidth: true
        visible: Store.error !== "" || Store.message !== ""
        text: Store.error || Store.message
        textFormat: Text.PlainText
        color: Store.error !== "" ? Theme.danger : Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        wrapMode: Text.Wrap
    }
    GridView {
        id: storeGrid
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        cellWidth: Math.floor(width / Math.max(1, Math.floor(width / 260)))
        cellHeight: Theme.hit(292)
        // Keyed by entry: a new page arrives as added cards, so the grid keeps its place.
        model: ScriptModel {
            values: Store.items
            objectProp: "id"
        }
        onAtYEndChanged: if (atYEnd && count > 0)
            Store.next()
        delegate: Item {
            id: storeCard
            required property var modelData
            readonly property var folders: Store.foldersOf(modelData.id)
            property int file: modelData.files[0]?.index ?? 1
            width: storeGrid.cellWidth
            height: storeGrid.cellHeight
            Rectangle {
                anchors.fill: parent
                anchors.margins: 5
                radius: Theme.corner(12)
                color: Theme.tile
                clip: true
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 4
                    Image {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 110
                        source: storeCard.modelData.preview
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        sourceSize: Qt.size(440, 220)
                    }
                    Text {
                        Layout.fillWidth: true
                        text: storeCard.modelData.name
                        textFormat: Text.PlainText
                        color: Theme.text
                        elide: Text.ElideRight
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                        font.bold: true
                    }
                    Text {
                        Layout.fillWidth: true
                        text: I18n.tr("store.by", [storeCard.modelData.author]) + " · " + I18n.tr("store.downloads", [storeCard.modelData.downloads.toLocaleString(I18n.locale, "f", 0)])
                        textFormat: Text.PlainText
                        color: Theme.muted
                        elide: Text.ElideRight
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(11)
                    }
                    Item {
                        Layout.fillHeight: true
                    }
                    // The file on its own row (names are long), the buttons below it on the right.
                    ChoiceCombo {
                        Layout.fillWidth: true
                        // Narrower than its longest file name: the shown name ends with an ellipsis.
                        Layout.minimumWidth: 0
                        Layout.maximumWidth: parent.width
                        visible: storeCard.modelData.files.length > 1
                        Accessible.name: storeCard.modelData.name
                        options: storeCard.modelData.files.map(f => ({
                                    name: String(f.index),
                                    label: f.name
                                }))
                        current: String(storeCard.file)
                        onChosen: name => storeCard.file = Number(name)
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Item {
                            Layout.fillWidth: true
                        }
                        ActionButton {
                            visible: storeCard.folders.length > 0
                            text: I18n.tr("store.remove")
                            destructive: true
                            enabled: !Store.working
                            onClicked: Store.remove(storeCard.folders)
                        }
                        ActionButton {
                            text: Store.installing === storeCard.modelData.id ? I18n.tr("store.installing") : I18n.tr("store.install")
                            enabled: !Store.working && storeCard.modelData.files.length > 0
                            highlighted: true
                            onClicked: Store.install(storeCard.modelData.id, storeCard.file)
                        }
                    }
                }
            }
        }
        ScrollBar.vertical: ScrollBar {}
        Text {
            anchors.centerIn: parent
            visible: storeGrid.count === 0
            text: Store.searching ? I18n.tr("store.loading") : I18n.tr("store.empty")
            color: Theme.muted
        }
    }
    Text {
        Layout.fillWidth: true
        text: I18n.tr("store.hint")
        color: Theme.muted
        wrapMode: Text.Wrap
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
}
