import QtQuick
import QtQuick.Effects
import Quickshell
import ".."
import "IconNames.js" as IconNames

Item {
    id: root
    required property string name
    property color color: Theme.text
    // Glyph being replaced; drawn underneath only while the new one fades in.
    property string previous: ""
    property string shown: ""
    property real progress: 1
    implicitWidth: 20
    implicitHeight: 20
    // State changes (mute, Wi-Fi strength, play/pause) cross-fade instead of swapping abruptly.
    onNameChanged: {
        if (shown !== "" && name !== shown && Theme.motionNormal > 0) {
            previous = shown;
            crossFade.restart();
        }
        shown = name;
    }
    Component.onCompleted: shown = name
    // The icon pack's symbolic glyph when the shell icons come from it, else the bundled drawing.
    function sourceFor(glyph) {
        if (!glyph)
            return "";
        if (Theme.iconSource === "pack") {
            const pack = IconNames.packSource(glyph, candidate => Quickshell.iconPath(candidate, true));
            if (pack)
                return pack;
        }
        return "../assets/icons/" + glyph + ".svg";
    }
    NumberAnimation {
        id: crossFade
        target: root
        property: "progress"
        from: 0
        to: 1
        duration: Theme.motionNormal
        easing.type: Easing.BezierSpline
        easing.bezierCurve: Theme.easeOut
    }
    Loader {
        anchors.fill: parent
        active: crossFade.running && root.previous !== ""
        sourceComponent: Item {
            opacity: 1 - root.progress
            Image {
                id: oldGlyph
                anchors.fill: parent
                source: root.sourceFor(root.previous)
                sourceSize: Qt.size(width * 2, height * 2)
                fillMode: Image.PreserveAspectFit
                visible: false
            }
            MultiEffect {
                anchors.fill: oldGlyph
                source: oldGlyph
                colorization: 1
                colorizationColor: root.color
            }
        }
    }
    Image {
        id: glyph
        anchors.fill: parent
        source: root.sourceFor(root.name)
        sourceSize: Qt.size(width * 2, height * 2)
        fillMode: Image.PreserveAspectFit
        visible: false
    }
    MultiEffect {
        anchors.fill: glyph
        source: glyph
        opacity: root.progress
        colorization: 1
        colorizationColor: root.color
    }
}
