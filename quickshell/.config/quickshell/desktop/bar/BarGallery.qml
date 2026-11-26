pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Layouts
import ".."
import "../components"
import "../services"
import "BarLayoutModel.js" as BarLayoutModel
import "widgets/Registry.js" as Registry

// The widgets not on the bar yet, while it is edited: Add puts one at the end of the chosen section, or a
// card is dragged to the place it should take.
Card {
    id: root
    required property var panel
    // The section Add puts a widget in.
    property string section: "right"
    signal closeRequested
    implicitHeight: content.implicitHeight + 2 * Theme.dialogPadding
    ColumnLayout {
        id: content
        anchors {
            fill: parent
            margins: Theme.dialogPadding
        }
        spacing: 14
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Heading {
                    text: I18n.tr("bar.gallery.title")
                }
                Text {
                    Layout.fillWidth: true
                    text: I18n.tr("bar.gallery.subtitle")
                    wrapMode: Text.WordWrap
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(12)
                }
            }
            PanelIconButton {
                iconName: "close"
                tooltip: I18n.tr("common.close")
                onClicked: root.closeRequested()
            }
        }
        Flow {
            Layout.fillWidth: true
            spacing: 6
            Text {
                height: Theme.hit(30)
                verticalAlignment: Text.AlignVCenter
                text: I18n.tr("bar.gallery.addTo")
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
                rightPadding: 4
            }
            Repeater {
                model: BarLayoutModel.sections
                ActionButton {
                    required property string modelData
                    implicitHeight: Theme.hit(30)
                    text: I18n.tr(BarLayoutModel.sectionKey(modelData))
                    highlighted: root.section === modelData
                    tone: "state"
                    onClicked: root.section = modelData
                }
            }
        }
        Text {
            Layout.fillWidth: true
            visible: grid.count === 0
            text: I18n.tr("bar.gallery.empty")
            wrapMode: Text.WordWrap
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(13)
        }
        GridLayout {
            Layout.fillWidth: true
            columns: Math.max(1, Math.floor(width / 200))
            columnSpacing: 8
            rowSpacing: 8
            Repeater {
                id: grid
                model: BarLayout.available()
                Rectangle {
                    id: card
                    required property string modelData
                    readonly property var widget: Registry.find(modelData)
                    readonly property string name: I18n.tr(Registry.nameKey(modelData))
                    Layout.fillWidth: true
                    Layout.preferredHeight: cardContent.implicitHeight + 20
                    radius: Theme.corner(12)
                    color: dragArea.containsMouse ? Theme.raised : Theme.tile
                    MouseArea {
                        id: dragArea
                        property point pressPoint
                        anchors.fill: parent
                        hoverEnabled: true
                        preventStealing: true
                        cursorShape: root.panel.drag ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                        onPressed: mouse => pressPoint = Qt.point(mouse.x, mouse.y)
                        onPositionChanged: mouse => {
                            const point = mapToItem(root.panel.stage, mouse.x, mouse.y);
                            if (root.panel.drag)
                                root.panel.moveDrag(point);
                            else if (pressed && Math.abs(mouse.x - pressPoint.x) + Math.abs(mouse.y - pressPoint.y) > 6)
                                root.panel.startDrag({
                                    from: "gallery",
                                    id: card.modelData
                                }, point);
                        }
                        onReleased: {
                            if (root.panel.drag)
                                root.panel.endDrag();
                        }
                    }
                    RowLayout {
                        id: cardContent
                        anchors {
                            fill: parent
                            margins: 10
                        }
                        spacing: 10
                        Icon {
                            name: card.widget?.glyph ?? ""
                            color: Theme.text
                            Layout.preferredWidth: Theme.hit(20)
                            Layout.preferredHeight: Theme.hit(20)
                            Layout.alignment: Qt.AlignTop
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                Layout.fillWidth: true
                                text: card.name
                                elide: Text.ElideRight
                                color: Theme.text
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(13)
                                font.weight: Font.DemiBold
                            }
                            Text {
                                Layout.fillWidth: true
                                text: I18n.tr(Registry.descriptionKey(card.modelData))
                                wrapMode: Text.WordWrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                                color: Theme.muted
                                font.family: Theme.font
                                font.pixelSize: Theme.textSize(11)
                            }
                        }
                        CompactIconButton {
                            iconName: "plus"
                            tooltip: I18n.tr("bar.gallery.add", [card.name])
                            Layout.alignment: Qt.AlignTop
                            onClicked: BarLayout.add(card.modelData, root.section, BarLayout.current[root.section].length)
                        }
                    }
                }
            }
        }
    }
}
