import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.folderlistmodel
import Quickshell
import Quickshell.Io
import ".."
import "../components"

Overlay {
    id: root
    panelName: "wallpaper"
    dialog: true
    property url selectedUrl: ""
    property string selectedPath: ""
    property string failure: ""
    function fileUrl(path) {
        return "file://" + path.split("/").map(encodeURIComponent).join("/");
    }
    function navigate(url) {
        folder.folder = url;
        selectedUrl = "";
        selectedPath = "";
        failure = "";
        files.currentIndex = -1;
    }
    function openEntry(index) {
        if (index < 0 || index >= folder.count)
            return;
        if (folder.isFolder(index))
            navigate(folder.get(index, "fileUrl"));
        else {
            selectedUrl = folder.get(index, "fileUrl");
            selectedPath = folder.get(index, "filePath");
        }
    }
    function apply(reset) {
        if (operation.running || (!reset && !selectedPath))
            return;
        failure = "";
        operation.command = [Quickshell.env("HOME") + "/.local/bin/desktop-wallpaper", reset ? "--reset" : selectedPath];
        operation.running = true;
    }
    onOpened: {
        failure = "";
        files.forceActiveFocus();
    }
    FolderListModel {
        id: folder
        folder: root.fileUrl(Quickshell.env("HOME"))
        nameFilters: ["*.png", "*.jpg", "*.jpeg", "*.webp", "*.jxl", "*.avif", "*.bmp", "*.tif", "*.tiff"]
        caseSensitive: false
        showDirsFirst: true
        showDotAndDotDot: false
        showHidden: false
        showOnlyReadable: true
    }
    Process {
        id: operation
        stderr: StdioCollector {
            id: errors
        }
        onExited: (code, status) => {
            if (code === 0) {
                if (ShellState.panel === root.panelName)
                    ShellState.close();
            } else
                root.failure = errors.text.trim() || I18n.tr("wallpaper.errors.setFailed");
        }
    }
    Card {
        anchors.centerIn: parent
        width: Math.min(900, parent.width - 48)
        height: Math.min(650, parent.height - 96)
        ColumnLayout {
            anchors {
                fill: parent
                margins: Theme.dialogPadding
            }
            spacing: 12
            Heading {
                text: I18n.tr("wallpaper.title")
            }
            RowLayout {
                ActionButton {
                    text: "↑"
                    tooltip: I18n.tr("wallpaper.parentFolder")
                    enabled: !operation.running
                    onClicked: root.navigate(folder.parentFolder)
                }
                ActionButton {
                    text: I18n.tr("wallpaper.home")
                    enabled: !operation.running
                    onClicked: root.navigate(root.fileUrl(Quickshell.env("HOME")))
                }
                ActionButton {
                    text: I18n.tr("wallpaper.collection")
                    enabled: !operation.running
                    onClicked: root.navigate(root.fileUrl(Quickshell.env("HOME") + "/.local/share/wallpapers"))
                }
                InputField {
                    id: path
                    Layout.fillWidth: true
                    text: decodeURIComponent(folder.folder.toString().replace(/^file:\/\//, ""))
                    placeholderText: I18n.tr("wallpaper.folderPlaceholder")
                    enabled: !operation.running
                    onAccepted: root.navigate(root.fileUrl(text.startsWith("~/") ? Quickshell.env("HOME") + text.slice(1) : text.startsWith("/") ? text : Quickshell.env("HOME") + "/" + text))
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 16
                ListView {
                    id: files
                    Layout.preferredWidth: 320
                    Layout.fillHeight: true
                    clip: true
                    spacing: 3
                    model: folder
                    enabled: !operation.running
                    Keys.onReturnPressed: root.openEntry(currentIndex)
                    Keys.onEnterPressed: root.openEntry(currentIndex)
                    Keys.onPressed: event => {
                        if (event.key === Qt.Key_Backspace) {
                            root.navigate(folder.parentFolder);
                            event.accepted = true;
                        }
                    }
                    delegate: ActionButton {
                        required property string fileName
                        required property string filePath
                        required property url fileUrl
                        required property bool fileIsDir
                        required property int index
                        width: files.width
                        implicitHeight: 40
                        text: fileName
                        iconName: fileIsDir ? "folder" : "image"
                        alignLeft: true
                        highlighted: files.currentIndex === index
                        onClicked: {
                            files.currentIndex = index;
                            root.openEntry(index);
                            files.forceActiveFocus();
                        }
                    }
                    ScrollBar.vertical: ScrollBar {}
                    Text {
                        anchors.centerIn: parent
                        visible: folder.count === 0
                        text: I18n.tr("wallpaper.empty")
                        color: Theme.muted
                        font.pixelSize: 12
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: Theme.background
                    radius: 14
                    clip: true
                    Image {
                        id: preview
                        anchors {
                            fill: parent
                            margins: 10
                        }
                        source: root.selectedUrl
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        sourceSize: Qt.size(1000, 700)
                    }
                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 32
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                        text: root.selectedPath ? (preview.status === Image.Error ? I18n.tr("wallpaper.previewUnavailable") : "") : I18n.tr("wallpaper.previewHint")
                        color: Theme.muted
                    }
                }
            }
            Text {
                Layout.fillWidth: true
                text: root.selectedPath
                elide: Text.ElideMiddle
                color: Theme.muted
                textFormat: Text.PlainText
                font.pixelSize: 12
            }
            Text {
                visible: root.failure !== ""
                Layout.fillWidth: true
                text: root.failure
                wrapMode: Text.Wrap
                color: Theme.danger
                textFormat: Text.PlainText
            }
            RowLayout {
                ActionButton {
                    text: I18n.tr("wallpaper.restoreDefault")
                    enabled: !operation.running
                    onClicked: root.apply(true)
                }
                Item {
                    Layout.fillWidth: true
                }
                ActionButton {
                    text: operation.running ? I18n.tr("wallpaper.applying") : I18n.tr("wallpaper.apply")
                    highlighted: true
                    enabled: !!root.selectedPath && !operation.running
                    onClicked: root.apply(false)
                }
                ActionButton {
                    text: I18n.tr("common.close")
                    onClicked: ShellState.close()
                }
            }
        }
    }
}
