import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// The glass page of Settings → Appearance (panels/theming/ThemingView.qml), built the first time its tab shows.
ColumnLayout {
    id: page
    // The Theming panel: the tab and the actions shared by its pages.
    required property var panel
    readonly property Item focusItem: glassBack
    spacing: 10
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        ActionButton {
            id: glassBack
            iconName: "arrow-left"
            text: I18n.tr("theming.glassBack")
            onClicked: page.panel.showTab("theme")
        }
        Text {
            Layout.fillWidth: true
            text: I18n.tr("theming.glassTitle", [Theming.themes.find(t => t.id === Theming.current)?.name ?? Theming.current])
            textFormat: Text.PlainText
            elide: Text.ElideRight
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.textSize(14)
            font.bold: true
        }
        ActionButton {
            text: I18n.tr("theming.glassReset")
            enabled: (Theming.glass ?? []).some(entry => entry.value !== entry.default)
            onClicked: Theming.resetGlass()
        }
    }
    Text {
        Layout.fillWidth: true
        text: I18n.tr("theming.glassHint")
        wrapMode: Text.Wrap
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
    Flickable {
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        contentHeight: glassRows.implicitHeight
        boundsBehavior: Flickable.StopAtBounds
        ColumnLayout {
            id: glassRows
            width: parent.width
            spacing: 4
            Repeater {
                // By position, so the rows (and the focused slider) survive each refresh.
                model: (Theming.glass ?? []).length
                RowLayout {
                    id: glassRow
                    required property int index
                    readonly property var entry: Theming.glass?.[index] ?? {
                        option: "",
                        value: 0,
                        default: 0,
                        min: 0,
                        max: 1,
                        step: 0.05
                    }
                    Layout.fillWidth: true
                    spacing: 12
                    Text {
                        Layout.preferredWidth: 200
                        text: page.panel.glassLabel(glassRow.entry.option)
                        elide: Text.ElideRight
                        color: Theme.text
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(13)
                    }
                    ControlSlider {
                        id: glassSlider
                        // From the first move until the saved value comes back, the slider keeps
                        // its own value instead of snapping back to the old one.
                        property bool holding: false
                        Layout.fillWidth: true
                        from: glassRow.entry.min
                        to: glassRow.entry.max
                        stepSize: glassRow.entry.step
                        snapMode: Slider.SnapAlways
                        Accessible.name: page.panel.glassLabel(glassRow.entry.option)
                        Binding on value {
                            when: !glassSlider.pressed && !glassSlider.holding
                            value: glassRow.entry.value
                        }
                        function commit() {
                            glassCommit.stop();
                            if (Math.abs(value - glassRow.entry.value) > glassRow.entry.step / 2)
                                Theming.setGlass(glassRow.entry.option, value);
                            else
                                holding = false;
                        }
                        // Each change reloads Hyprland: a drag commits on release, arrow keys after a pause.
                        onMoved: {
                            holding = true;
                            if (!pressed)
                                glassCommit.restart();
                        }
                        onPressedChanged: if (!pressed && holding)
                            commit()
                        Connections {
                            target: glassRow
                            function onEntryChanged() {
                                if (!glassSlider.pressed && !glassCommit.running)
                                    glassSlider.holding = false;
                            }
                        }
                        Timer {
                            id: glassCommit
                            interval: 450
                            onTriggered: glassSlider.commit()
                        }
                    }
                    Text {
                        Layout.preferredWidth: 64
                        horizontalAlignment: Text.AlignRight
                        text: page.panel.glassText(glassRow.entry, glassSlider.value)
                        color: Math.abs(glassSlider.value - glassRow.entry.default) > glassRow.entry.step / 2 ? Theme.accent : Theme.muted
                        font.family: Theme.font
                        font.pixelSize: Theme.textSize(12)
                        HoverHandler {
                            id: valueHover
                        }
                        ToolTip.visible: valueHover.hovered
                        ToolTip.text: I18n.tr("theming.glassDefault", [page.panel.glassText(glassRow.entry, glassRow.entry.default)])
                    }
                }
            }
        }
        ScrollBar.vertical: ScrollBar {}
    }
}
