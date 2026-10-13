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

ShellRoot {
    id: root
    readonly property var windows: JSON.parse(Quickshell.env("DESKTOP_SHARE_WINDOWS") || "[]")
    property bool windowTab: false
    property string chosenKind: ""
    property string chosenId: ""
    function choose(kind, id) {
        chosenKind = kind;
        chosenId = id;
    }
    function accept() {
        if (!chosenId)
            return;
        result.setText(JSON.stringify({
            kind: chosenKind,
            id: chosenId,
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
        color: "#28000000"
        WlrLayershell.layer: WlrLayer.Overlay
        WlrLayershell.namespace: "desktop-share-picker"
        WlrLayershell.keyboardFocus: WlrKeyboardFocus.Exclusive
        onVisibleChanged: if (visible)
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
                    text: "Condividi lo schermo"
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: "Scegli il monitor o la finestra da rendere visibile all’applicazione."
                    color: Theme.muted
                    font.pixelSize: 13
                }
                RowLayout {
                    ActionButton {
                        text: "Monitor"
                        highlighted: !root.windowTab
                        onClicked: {
                            root.windowTab = false;
                            root.chosenId = "";
                        }
                    }
                    ActionButton {
                        text: "Finestre"
                        highlighted: root.windowTab
                        onClicked: {
                            root.windowTab = true;
                            root.chosenId = "";
                        }
                    }
                }
                InputField {
                    id: search
                    Layout.fillWidth: true
                    placeholderText: "Cerca…"
                    Keys.onDownPressed: choices.currentIndex = Math.min(choices.count - 1, choices.currentIndex + 1)
                    Keys.onUpPressed: choices.currentIndex = Math.max(0, choices.currentIndex - 1)
                    onTextChanged: choices.currentIndex = 0
                    onAccepted: {
                        const entry = choices.model[choices.currentIndex];
                        if (entry) {
                            root.choose(entry.kind, entry.id);
                            root.accept();
                        }
                    }
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
                        highlighted: root.chosenId === modelData.id && root.chosenKind === modelData.kind
                        onClicked: {
                            choices.currentIndex = index;
                            root.choose(modelData.kind, modelData.id);
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}
                    Text {
                        anchors.centerIn: parent
                        visible: choices.count === 0
                        text: "Nessuna sorgente disponibile"
                        color: Theme.muted
                    }
                }
                RowLayout {
                    visible: Quickshell.env("DESKTOP_SHARE_ALLOW_TOKEN") === "1"
                    Text {
                        text: "Ricorda la scelta per questa applicazione"
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
                        text: "Annulla"
                        onClicked: Qt.quit()
                    }
                    ActionButton {
                        text: "Condividi"
                        highlighted: true
                        enabled: !!root.chosenId
                        onClicked: root.accept()
                    }
                }
            }
        }
    }
}
