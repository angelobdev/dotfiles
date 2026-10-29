import QtQuick
import QtQuick.Controls
import Quickshell
import "../.."

Menu {
    id: root
    property var menuEntry: null
    title: menuEntry?.text ?? ""
    enabled: menuEntry?.enabled ?? true
    popupType: Popup.Item
    focus: true
    cascade: true
    overlap: 2
    padding: 6
    implicitWidth: 252
    font.family: Theme.font
    font.pixelSize: 13
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    delegate: TrayMenuItem {}
    background: Rectangle {
        implicitWidth: 252
        implicitHeight: 12
        radius: Theme.corner(12)
        color: Theme.background
        border.width: Theme.frameWidth
        border.color: Theme.frameActive
    }
    QsMenuOpener {
        id: opener
        menu: root.visible ? root.menuEntry : null
    }
    MenuItem {
        text: I18n.tr("session.noActions")
        visible: opener.children.values.length === 0
        height: visible ? 32 : 0
        enabled: false
        font: root.font
        palette.windowText: Theme.muted
        background: Item {}
    }
    Component {
        id: separator
        MenuSeparator {
            implicitHeight: 9
            topPadding: 4
            bottomPadding: 4
            contentItem: Rectangle {
                implicitHeight: 1
                color: Theme.stroke
            }
            leftPadding: 6
            rightPadding: 6
        }
    }
    function remove(control, submenu) {
        if (!control)
            return;
        if (submenu)
            removeMenu(control);
        else
            removeItem(control);
        control.destroy();
    }
    Instantiator {
        model: opener.children
        delegate: QtObject {
            id: holder
            required property var modelData
            required property int index
            property var control: null
            property bool wasSubmenu: false
            readonly property bool submenu: modelData.hasChildren && !modelData.isSeparator
            readonly property bool isSeparator: modelData.isSeparator
            function rebuild() {
                root.remove(control, wasSubmenu);
                wasSubmenu = submenu;
                if (submenu) {
                    // Load only this level; QsMenuOpener requests descendants when opened.
                    const component = Qt.createComponent(Qt.resolvedUrl("TrayMenu.qml"));
                    control = component.createObject(root, {
                        menuEntry: modelData
                    });
                    if (control)
                        root.insertMenu(index, control);
                    else
                        console.warn(component.errorString());
                } else {
                    control = isSeparator ? separator.createObject(root.contentItem) : root.delegate.createObject(root.contentItem, {
                        entry: modelData
                    });
                    root.insertItem(index, control);
                }
            }
            onSubmenuChanged: if (control)
                rebuild()
            onIsSeparatorChanged: if (control)
                rebuild()
        }
        onObjectAdded: (index, object) => object.rebuild()
        onObjectRemoved: (index, object) => root.remove(object.control, object.wasSubmenu)
    }
}
