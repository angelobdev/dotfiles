import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// The font page of Settings → Appearance (panels/theming/ThemingView.qml), built the first time its tab shows.
ColumnLayout {
    id: page
    // The Theming panel: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: sansProxy.list
    spacing: 12
    RowLayout {
        Layout.fillWidth: true
        Text {
            Layout.fillWidth: true
            text: I18n.tr("theming.unified")
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.textSize(13)
        }
        ControlSwitch {
            checked: Theming.fonts.chosen?.unified === true
            onToggled: Theming.setUnified(checked)
            Accessible.name: I18n.tr("theming.unified")
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 16
        Repeater {
            model: [
                {
                    kind: "sans",
                    label: I18n.tr("theming.interfaceFont")
                },
                {
                    kind: "mono",
                    label: I18n.tr("theming.monospaceFont")
                }
            ]
            ColumnLayout {
                id: fontColumn
                required property var modelData
                required property int index
                readonly property string chosen: Theming.fonts.chosen?.[modelData.kind] ?? ""
                readonly property string themeFamily: Theming.fonts.theme?.[modelData.kind] ?? ""
                // With one font everywhere the interface list has nothing to choose.
                readonly property bool usable: modelData.kind === "mono" || Theming.fonts.chosen?.unified !== true
                Layout.fillWidth: true
                Layout.fillHeight: true
                enabled: usable
                opacity: usable ? 1 : 0.45
                spacing: 6
                Heading {
                    text: fontColumn.modelData.label
                    section: true
                }
                ListView {
                    id: fontList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 2
                    model: [""].concat(Theming.fonts[fontColumn.modelData.kind] ?? [])
                    keyNavigationEnabled: true
                    highlightMoveDuration: Theme.motionNormal
                    Keys.onReturnPressed: Theming.setFont(fontColumn.modelData.kind, model[currentIndex] ?? "")
                    Keys.onEnterPressed: Theming.setFont(fontColumn.modelData.kind, model[currentIndex] ?? "")
                    Keys.onRightPressed: if (fontColumn.index === 0)
                        monoProxy.list?.forceActiveFocus()
                    Keys.onLeftPressed: if (fontColumn.index === 1)
                        sansProxy.list?.forceActiveFocus()
                    delegate: ActionButton {
                        id: fontRow
                        required property string modelData
                        required property int index
                        readonly property bool selected: modelData === fontColumn.chosen
                        width: fontList.width
                        implicitHeight: Theme.hit(36)
                        alignLeft: true
                        text: modelData === "" ? I18n.tr("theming.themeDefaultNamed", [fontColumn.themeFamily]) : modelData
                        font.family: modelData === "" ? fontColumn.themeFamily : modelData
                        font.pixelSize: Theme.textSize(14)
                        highlighted: selected
                        tone: "state"
                        onClicked: {
                            fontList.currentIndex = index;
                            Theming.setFont(fontColumn.modelData.kind, modelData);
                        }
                        Component.onCompleted: if (selected)
                            fontList.currentIndex = index
                    }
                    Component.onCompleted: {
                        if (fontColumn.index === 0)
                            sansProxy.list = fontList;
                        else
                            monoProxy.list = fontList;
                    }
                    ScrollBar.vertical: ScrollBar {}
                }
                CustomEntry {
                    kind: fontColumn.modelData.kind
                    placeholder: I18n.tr("theming.otherFont")
                }
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        Text {
            text: I18n.tr("theming.size")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        ChoiceCombo {
            Accessible.name: I18n.tr("theming.size")
            options: [9, 10, 11, 12, 13].map(size => ({
                        name: String(size),
                        label: String(size)
                    }))
            current: String(Theming.fonts.effective?.size ?? "")
            onChosen: name => Theming.setSize(Number(name))
        }
        // The shell's own text (bar, panels, notifications), applied at once; apps follow the size on the left.
        Text {
            text: I18n.tr("theming.shellText")
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
        }
        ChoiceCombo {
            Accessible.name: I18n.tr("theming.shellText")
            options: [1, 1.15, 1.3, 1.5].map(scale => ({
                        name: String(scale),
                        label: Math.round(scale * 100) + "%"
                    }))
            current: String(Theme.textScale)
            onChosen: name => Theming.setTextScale(Number(name))
        }
        Item {
            Layout.fillWidth: true
        }
        ActionButton {
            outlined: true
            text: I18n.tr("theming.openFonts")
            onClicked: Theming.openFolder("fonts")
        }
        ActionButton {
            outlined: true
            text: I18n.tr("theming.rescan")
            onClicked: Theming.rescan("fonts")
        }
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: previewColumn.implicitHeight + 20
        radius: Theme.corner(12)
        color: Theme.background
        ColumnLayout {
            id: previewColumn
            anchors {
                fill: parent
                margins: 10
            }
            spacing: 4
            Text {
                Layout.fillWidth: true
                text: I18n.tr("theming.previewSans")
                elide: Text.ElideRight
                color: Theme.text
                font.family: Theming.fonts.effective?.sans ?? Theme.font
                font.pixelSize: Math.round((Theming.fonts.effective?.size ?? 10) * 1.6)
            }
            Text {
                Layout.fillWidth: true
                text: "0O 1lI {} [] => fn main() { println!(\"hello\"); }"
                textFormat: Text.PlainText
                elide: Text.ElideRight
                color: Theme.muted
                font.family: Theming.fonts.effective?.mono ?? "monospace"
                font.pixelSize: Math.round((Theming.fonts.effective?.size ?? 10) * 1.5)
            }
        }
    }
    // The two font lists are created by a Repeater; these let arrow keys move between them.
    QtObject {
        id: sansProxy
        property var list: null
    }
    QtObject {
        id: monoProxy
        property var list: null
    }
}
