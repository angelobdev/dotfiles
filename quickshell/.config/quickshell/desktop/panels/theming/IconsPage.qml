import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"
import "../../components/FileUrl.js" as FileUrl

// The icons page of the Theming panel (panels/ThemingPanel.qml), built the first time its tab shows.
ColumnLayout {
    id: page
    // The Theming panel: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: iconList
    spacing: 10
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text {
            text: I18n.tr("theming.cursor")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        ChoiceCombo {
            Accessible.name: I18n.tr("theming.cursor")
            options: [
                {
                    name: "",
                    label: I18n.tr("theming.themeDefaultNamed", [Theming.cursors.theme ?? ""])
                }
            ].concat((Theming.cursors.themes ?? []).map(t => ({
                        name: t.id,
                        label: t.download ? I18n.tr("theming.cursorDownload", [t.name]) : t.name
                    })))
            current: Theming.cursors.chosen?.theme ?? ""
            onChosen: name => Theming.setCursor(name, undefined)
        }
        ChoiceChips {
            Accessible.name: I18n.tr("theming.cursorSize")
            options: (Theming.cursors.sizes ?? []).map(size => ({
                        name: String(size),
                        label: String(size)
                    }))
            current: String(Theming.cursors.size ?? 24)
            onChosen: name => Theming.setCursor(undefined, Number(name))
        }
        Item {
            Layout.fillWidth: true
        }
        ActionButton {
            text: I18n.tr("store.getMore")
            onClicked: page.panel.openStore("cursors")
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text {
            text: I18n.tr("theming.shellIcons")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        ChoiceCombo {
            Accessible.name: I18n.tr("theming.shellIcons")
            options: [
                {
                    name: "desktop",
                    label: I18n.tr("theming.shellIconsDesktop")
                },
                {
                    name: "pack",
                    label: I18n.tr("theming.shellIconsPack")
                }
            ]
            current: Theme.iconSource
            onChosen: name => Theming.setShellIcons(name)
        }
        Item {
            Layout.fillWidth: true
        }
        ActionButton {
            text: I18n.tr("store.getMore")
            onClicked: page.panel.openStore("icons")
        }
        ActionButton {
            text: I18n.tr("theming.openIcons")
            onClicked: Theming.openFolder("icons")
        }
        ActionButton {
            text: I18n.tr("theming.rescan")
            onClicked: Theming.rescan("icons")
        }
    }
    ListView {
        id: iconList
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 3
        model: [
            {
                id: "",
                name: I18n.tr("theming.themeDefaultNamed", [Theming.icons.theme ?? ""]),
                samples: (Theming.icons.themes.find(t => t.id === Theming.icons.theme)?.samples) ?? []
            }
        ].concat(Theming.icons.themes)
        keyNavigationEnabled: true
        highlightMoveDuration: Theme.motionNormal
        Keys.onReturnPressed: Theming.setIcons(model[currentIndex]?.id ?? "")
        Keys.onEnterPressed: Theming.setIcons(model[currentIndex]?.id ?? "")
        delegate: ActionButton {
            id: iconRow
            required property var modelData
            required property int index
            readonly property bool selected: (modelData.id || null) === (Theming.icons.chosen ?? null)
            width: iconList.width
            implicitHeight: 52
            alignLeft: true
            highlighted: selected
            text: modelData.name
            rightPadding: 12 + samples.width
            onClicked: {
                iconList.currentIndex = index;
                Theming.setIcons(modelData.id);
            }
            Component.onCompleted: if (selected)
                iconList.currentIndex = index
            Row {
                id: samples
                anchors {
                    right: parent.right
                    rightMargin: 14
                    verticalCenter: parent.verticalCenter
                }
                spacing: 10
                Repeater {
                    model: iconRow.modelData.samples
                    Image {
                        required property string modelData
                        width: 28
                        height: 28
                        source: modelData ? FileUrl.of(modelData) : ""
                        sourceSize: Qt.size(56, 56)
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                    }
                }
            }
        }
        ScrollBar.vertical: ScrollBar {}
    }
    CustomEntry {
        kind: "icons"
        placeholder: I18n.tr("theming.otherIcons")
    }
}
