import QtQuick
import QtQuick.Layouts
import ".."

// A square switch of the Control Center: icon, name and state. A tap toggles it; a tile with details shows
// a chevron that opens them, as do a long press and a right click.
Rectangle {
    id: root
    property string icon: ""
    property string title: ""
    property string status: ""
    property bool checked: false
    property bool available: true
    property bool hasDetails: false
    property bool detailsOpen: false
    signal toggled
    signal detailsRequested
    implicitHeight: Theme.hit(84)
    radius: Theme.corner(14)
    color: checked ? Qt.alpha(Theme.accent, 0.22) : Theme.tile
    border.color: checked ? Theme.accent : Theme.stroke
    opacity: available ? 1 : 0.55
    activeFocusOnTab: true
    Keys.onSpacePressed: if (available)
        toggled()
    Keys.onReturnPressed: if (available)
        toggled()
    Keys.onMenuPressed: if (hasDetails)
        detailsRequested()
    Accessible.role: Accessible.CheckBox
    Accessible.name: title
    Accessible.checked: checked
    ColumnLayout {
        anchors {
            fill: parent
            margins: 12
        }
        spacing: 3
        Icon {
            name: root.icon
            color: root.checked ? Theme.accent : Theme.text
            Layout.preferredWidth: 22
            Layout.preferredHeight: 22
        }
        Item {
            Layout.fillHeight: true
        }
        Text {
            Layout.fillWidth: true
            text: root.title
            elide: Text.ElideRight
            font.family: Theme.font
            font.pixelSize: 13
            color: Theme.text
        }
        Text {
            Layout.fillWidth: true
            text: root.status
            elide: Text.ElideRight
            font.family: Theme.font
            font.pixelSize: 11
            color: Theme.muted
        }
    }
    MouseArea {
        property bool held: false
        anchors.fill: parent
        enabled: root.available
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        pressAndHoldInterval: 500
        onPressed: held = false
        onPressAndHold: {
            held = true;
            if (root.hasDetails)
                root.detailsRequested();
        }
        onClicked: mouse => {
            if (held)
                return;
            if (mouse.button === Qt.RightButton) {
                if (root.hasDetails)
                    root.detailsRequested();
            } else {
                root.toggled();
            }
        }
    }
    // Above the tap area, so a tap on the chevron opens the details instead of toggling.
    Item {
        visible: root.hasDetails && root.available
        anchors {
            top: parent.top
            right: parent.right
        }
        width: Theme.hit(40)
        height: Theme.hit(40)
        Icon {
            anchors.centerIn: parent
            name: root.detailsOpen ? "chevron-up" : "chevron-down"
            color: Theme.muted
            width: 16
            height: 16
        }
        // A MouseArea takes the press, so the tile below neither toggles nor sees a long press (a TapHandler
        // only grabs passively and let both happen).
        MouseArea {
            anchors.fill: parent
            onClicked: root.detailsRequested()
        }
    }
}
