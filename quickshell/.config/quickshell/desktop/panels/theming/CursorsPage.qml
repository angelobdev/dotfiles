import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"
import "../../components/FileUrl.js" as FileUrl

// The cursors page of Settings → Appearance (panels/theming/ThemingView.qml), built the first time its tab shows: each
// cursor theme with five of its own shapes (theme.py cursor_samples), drawn at the chosen size.
ColumnLayout {
    id: page
    // The Theming panel: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: cursorList
    readonly property int size: Theming.cursors.size ?? 24
    spacing: 10
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text {
            text: I18n.tr("theming.cursorSize")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        ChoiceChips {
            Accessible.name: I18n.tr("theming.cursorSize")
            options: (Theming.cursors.sizes ?? []).map(size => ({
                        name: String(size),
                        label: String(size)
                    }))
            current: String(page.size)
            onChosen: name => Theming.setCursor(undefined, Number(name))
        }
        Item {
            Layout.fillWidth: true
        }
        ActionButton {
            text: I18n.tr("store.getMore")
            onClicked: page.panel.openStore("cursors")
        }
        ActionButton {
            text: I18n.tr("theming.openCursors")
            onClicked: Theming.openFolder("icons")
        }
        ActionButton {
            text: I18n.tr("theming.rescan")
            onClicked: Theming.rescan("icons")
        }
    }
    ListView {
        id: cursorList
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        spacing: 3
        // "Theme default" first, showing the shapes of the theme's own cursor.
        model: [
            {
                id: "",
                name: I18n.tr("theming.themeDefaultNamed", [Theming.cursors.theme ?? ""]),
                samples: ((Theming.cursors.themes ?? []).find(t => t.id === Theming.cursors.theme)?.samples) ?? []
            }
        ].concat((Theming.cursors.themes ?? []).map(t => ({
                    id: t.id,
                    name: t.download ? I18n.tr("theming.cursorDownload", [t.name]) : t.name,
                    samples: t.samples ?? []
                })))
        keyNavigationEnabled: true
        highlightMoveDuration: Theme.motionNormal
        Keys.onReturnPressed: Theming.setCursor(model[currentIndex]?.id ?? "", undefined)
        Keys.onEnterPressed: Theming.setCursor(model[currentIndex]?.id ?? "", undefined)
        delegate: ActionButton {
            id: cursorRow
            required property var modelData
            required property int index
            readonly property bool selected: modelData.id === (Theming.cursors.chosen?.theme ?? "")
            width: cursorList.width
            implicitHeight: Math.max(52, page.size + 20)
            alignLeft: true
            highlighted: selected
            tone: "state"
            text: modelData.name
            rightPadding: 12 + samples.width
            onClicked: {
                cursorList.currentIndex = index;
                Theming.setCursor(modelData.id, undefined);
            }
            Component.onCompleted: if (selected)
                cursorList.currentIndex = index
            Row {
                id: samples
                anchors {
                    right: parent.right
                    rightMargin: 14
                    verticalCenter: parent.verticalCenter
                }
                spacing: 12
                Repeater {
                    model: cursorRow.modelData.samples
                    Image {
                        required property string modelData
                        width: page.size
                        height: page.size
                        source: modelData ? FileUrl.of(modelData) : ""
                        sourceSize: Qt.size(96, 96)
                        fillMode: Image.PreserveAspectFit
                        smooth: true
                        mipmap: true
                        asynchronous: true
                    }
                }
            }
        }
        ScrollBar.vertical: ScrollBar {}
    }
}
