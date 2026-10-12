import QtQuick
import QtQuick.Effects
import ".."
Item {
    id: root
    required property string name
    property color color: Theme.text
    implicitWidth: 20
    implicitHeight: 20
    Image {
        id: glyph
        anchors.fill: parent
        source: root.name ? "../assets/icons/" + root.name + ".svg" : ""
        sourceSize: Qt.size(width * 2, height * 2)
        fillMode: Image.PreserveAspectFit
        visible: false
    }
    MultiEffect { anchors.fill: glyph; source: glyph; colorization: 1; colorizationColor: root.color }
}
