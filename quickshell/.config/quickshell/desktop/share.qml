//@ pragma UseQApplication
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import "."
import "components"
import "services"

ShellRoot {
    id: root
    readonly property var windows: JSON.parse(Quickshell.env("DESKTOP_SHARE_WINDOWS") || "[]")
    property bool windowTab: false
    // The keyboard cursor is the selection: Enter and Share use the highlighted row.
    readonly property var current: choices.model[choices.currentIndex] ?? null
    function showTab(windows) {
        windowTab = windows;
        choices.currentIndex = 0;
    }
    function accept() {
        if (!current)
            return;
        result.setText(JSON.stringify({
            kind: current.kind,
            id: current.id,
            remember: remember.checked
        }));
    }
    FileView {
        id: result
        path: Quickshell.env("DESKTOP_SHARE_RESULT")
        printErrors: false
        onSaved: Qt.quit()
        onSaveFailed: Qt.quit()
    }
    PanelWindow {
        id: panel
        screen: Quickshell.screens.find(s => s.name === Hyprland.focusedMonitor?.name) || Quickshell.screens[0]
        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }
        exclusionMode: ExclusionMode.Ignore
        color: Theme.shareShade
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "desktop-share-picker"
        // In tablet mode: focus on demand, so touches reach the on-screen keyboard, and no focused search
        // field, which would open the keyboard over the picker just to choose a window.
        WlrLayershell.keyboardFocus: Tablet.active ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.Exclusive
        onVisibleChanged: if (visible && !Tablet.active)
            search.forceActiveFocus()
        contentItem.Keys.onEscapePressed: Qt.quit()
        Card {
            anchors.centerIn: parent
            width: Math.min(620, parent.width - 32)
            height: Math.min(580, parent.height - 76)
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 22
                spacing: 14
                Heading {
                    text: I18n.tr("sharing.title")
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: I18n.tr("sharing.chooseSourceHint")
                    color: Theme.muted
                    font.pixelSize: 13
                }
                RowLayout {
                    ActionButton {
                        text: I18n.tr("recording.display")
                        highlighted: !root.windowTab
                        onClicked: root.showTab(false)
                    }
                    ActionButton {
                        text: I18n.tr("hints.categories.windows")
                        highlighted: root.windowTab
                        onClicked: root.showTab(true)
                    }
                }
                InputField {
                    id: search
                    Layout.fillWidth: true
                    placeholderText: I18n.tr("common.searchPlaceholder")
                    Keys.onDownPressed: choices.currentIndex = Math.min(choices.count - 1, choices.currentIndex + 1)
                    Keys.onUpPressed: choices.currentIndex = Math.max(0, choices.currentIndex - 1)
                    onTextChanged: choices.currentIndex = 0
                    onAccepted: root.accept()
                }
                ListView {
                    id: choices
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 6
                    currentIndex: 0
                    model: (root.windowTab ? root.windows.map(w => ({
                                    id: w.id,
                                    label: w.title || w.app,
                                    app: w.app,
                                    kind: "window"
                                })) : Quickshell.screens.map(s => ({
                                    id: s.name,
                                    label: s.name + " · " + s.width + " × " + s.height,
                                    app: "",
                                    kind: "screen"
                                }))).filter(e => (e.label + " " + e.app).toLowerCase().includes(search.text.toLowerCase()))
                    delegate: ActionButton {
                        required property var modelData
                        required property int index
                        width: choices.width
                        implicitHeight: 48
                        text: modelData.label
                        alignLeft: true
                        iconSource: modelData.app ? Quickshell.iconPath(modelData.app, "application-x-executable") : ""
                        iconName: modelData.kind === "screen" ? "monitor" : ""
                        highlighted: choices.currentIndex === index
                        onClicked: choices.currentIndex = index
                    }
                    ScrollBar.vertical: ScrollBar {}
                    Text {
                        anchors.centerIn: parent
                        visible: choices.count === 0
                        text: I18n.tr("sharing.noSources")
                        color: Theme.muted
                    }
                }
                RowLayout {
                    visible: Quickshell.env("DESKTOP_SHARE_ALLOW_TOKEN") === "1"
                    Text {
                        text: I18n.tr("sharing.rememberChoice")
                        color: Theme.muted
                        Layout.fillWidth: true
                        font.pixelSize: 12
                    }
                    ControlSwitch {
                        id: remember
                    }
                }
                RowLayout {
                    Item {
                        Layout.fillWidth: true
                    }
                    ActionButton {
                        text: I18n.tr("common.cancel")
                        onClicked: Qt.quit()
                    }
                    ActionButton {
                        text: I18n.tr("sharing.share")
                        highlighted: true
                        enabled: !!root.current
                        onClicked: root.accept()
                    }
                }
            }
        }
    }
}
