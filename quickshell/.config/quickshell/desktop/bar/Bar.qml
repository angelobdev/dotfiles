pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Effects
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland
import Quickshell.Wayland
import ".."
import "../components"
import "../services"
import "tray"
import "BarLayoutModel.js" as BarLayoutModel
import "widgets/Registry.js" as Registry

// The bar: widgets in five sections (left, center-left, center, center-right, right; services/BarLayout.qml)
// over one of four backgrounds (Theme.barStyle). While it is edited, its surface grows down the screen for the
// section labels, the gallery and the trash, and reserves no more than before.
PanelWindow {
    id: bar
    readonly property var monitor: Hyprland.monitorFor(screen)
    // Keep the surface mapped: Hyprspace restores its alpha when it closes.
    // An invisible bar must neither reserve space nor intercept preview clicks, but its corner still closes
    // the overview.
    // Hidden by the overview, or by the user (Super + B): no reserved space and no input but the corner, and
    // nothing drawn, while the surface stays mapped.
    readonly property bool compositorHidden: BarVisibility.hidden(screen.name) || BarVisibility.userHidden
    readonly property string style: Theme.barStyle
    readonly property bool pills: style === "pills"
    readonly property bool merged: pills && Config.barMergeCenter
    readonly property int stripHeight: Theme.barReserved
    readonly property bool editing: BarLayout.editingScreen === screen.name
    readonly property var sectionIds: BarLayout.layoutFor(screen.name)
    // The room between sections; wider while edited, so their outlines stay apart.
    readonly property int sectionGap: editing ? 10 : pills ? 8 : 5
    // The title widget registers itself, for the window menu the shell is asked to open.
    property Item titleWidget: null
    readonly property var trayMenu: trayMenuWindow
    readonly property var windowMenu: windowMenuWindow
    readonly property Item stage: stageItem
    // A widget being dragged ({ from: "bar", section, index, id } or { from: "gallery", id }), the pointer in
    // stage coordinates, and where it would land ({ section, index, caretX } or { trash: true }).
    property var drag: null
    property point dragPoint: Qt.point(0, 0)
    property var dropTarget: null
    property string gallerySection: ""
    function focusWorkspace(id) {
        Hyprland.dispatch("hl.dsp.focus({ monitor = " + JSON.stringify(screen.name) + " })");
        Hyprland.dispatch("hl.dsp.focus({ workspace = " + id + " })");
    }
    function sectionItem(key) {
        return ({
                left: leftSection,
                centerLeft: centerLeftSection,
                center: centerSection,
                centerRight: centerRightSection,
                right: rightSection
            })[key];
    }
    // The left edge of a section in stage (and strip) coordinates.
    function sectionX(key) {
        const section = sectionItem(key);
        return content.x + (section.parent === centerBlock ? centerBlock.x : 0) + section.x;
    }
    function slotAt(x) {
        for (const key of BarLayoutModel.sections) {
            const section = sectionItem(key);
            if (!section.shows)
                continue;
            for (const slot of section.geometry(stageItem))
                if (x >= slot.x && x < slot.x + slot.width)
                    return {
                        section: key,
                        index: slot.index,
                        id: bar.sectionIds[key][slot.index]
                    };
        }
        return null;
    }
    function startDrag(source, point) {
        drag = source;
        moveDrag(point);
    }
    function moveDrag(point) {
        dragPoint = point;
        if (point.y <= stripHeight + 12) {
            let best = "";
            let distance = Infinity;
            for (const key of BarLayoutModel.sections) {
                const section = sectionItem(key);
                if (!section.shows)
                    continue;
                const start = sectionX(key);
                const away = point.x < start ? start - point.x : Math.max(0, point.x - start - section.width);
                if (away < distance) {
                    distance = away;
                    best = key;
                }
            }
            if (best === "") {
                dropTarget = null;
                return;
            }
            const slots = sectionItem(best).geometry(stageItem);
            const k = BarLayoutModel.dropIndex(slots.map(slot => slot.x + slot.width / 2), point.x);
            const last = slots[slots.length - 1];
            dropTarget = {
                section: best,
                index: k < slots.length ? slots[k].index : sectionIds[best].length,
                caretX: k < slots.length ? slots[k].x - 4 : last ? last.x + last.width + 1 : sectionX(best) + 8
            };
        } else if (drag?.from === "bar" && trash.contains(trash.mapFromItem(stageItem, point.x, point.y))) {
            dropTarget = {
                trash: true
            };
        } else {
            dropTarget = null;
        }
    }
    function endDrag() {
        const source = drag;
        const target = dropTarget;
        cancelDrag();
        if (!source || !target)
            return;
        if (target.trash)
            BarLayout.removeAt(source.section, source.index);
        else if (source.from === "bar")
            BarLayout.move(source.section, source.index, target.section, target.index);
        else
            BarLayout.add(source.id, target.section, target.index);
    }
    function cancelDrag() {
        drag = null;
        dropTarget = null;
    }
    function openGallery(key) {
        BarLayout.latch();
        gallery.section = key;
        gallerySection = key;
    }
    function sectionName(key) {
        return I18n.tr(BarLayoutModel.sectionKey(key));
    }
    function openWidgetMenu(slot, point) {
        const entries = [
            {
                kind: "heading",
                text: I18n.tr(Registry.nameKey(slot.id))
            }
        ];
        for (const key of BarLayoutModel.sections)
            if (key !== slot.section)
                entries.push({
                    text: I18n.tr("bar.menu.moveTo", [sectionName(key)]),
                    action: () => BarLayout.move(slot.section, slot.index, key, BarLayout.current[key].length)
                });
        entries.push({
            kind: "separator"
        }, {
            text: I18n.tr("bar.menu.addHere"),
            action: () => bar.openGallery(slot.section)
        }, {
            text: I18n.tr("bar.menu.remove"),
            destructive: true,
            action: () => BarLayout.removeAt(slot.section, slot.index)
        });
        barMenu.popup(stageItem, point.x, point.y, entries);
    }
    // A right click or a long press on the empty bar.
    function openBarMenu(x, y) {
        const preset = name => ({
                    text: I18n.tr(BarLayoutModel.presetKey(name)),
                    checked: BarLayout.isPreset(name),
                    action: () => BarLayout.usePreset(name)
                });
        const entries = [
            {
                kind: "heading",
                text: I18n.tr("bar.menu.title")
            },
            {
                text: I18n.tr("bar.menu.edit"),
                glyph: "controls",
                action: () => BarLayout.begin(bar.screen.name, true)
            },
            {
                kind: "separator"
            },
            preset("classic"), preset("centered"), preset("minimal")];
        if (pills)
            entries.push({
                kind: "separator"
            }, {
                text: I18n.tr("bar.menu.mergeCenter"),
                checked: Config.barMergeCenter,
                action: () => Config.set("barMergeCenter", !Config.barMergeCenter, false)
            });
        barMenu.popup(stageItem, x, y, entries);
    }
    anchors {
        top: true
        left: true
        right: true
    }
    implicitHeight: editing ? screen.height : stripHeight
    color: "transparent"
    exclusiveZone: compositorHidden ? 0 : stripHeight
    mask: compositorHidden ? cornerInput : null
    WlrLayershell.namespace: "desktop-bar"
    // Latched editing takes the keyboard on a click, for Escape.
    WlrLayershell.keyboardFocus: editing && BarLayout.latched ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
    onEditingChanged: {
        if (!editing) {
            gallerySection = "";
            cancelDrag();
        }
    }
    Region {
        id: cornerInput
        item: corner
    }
    // Resting the pointer in the top-left corner toggles the overview of this monitor, once per visit. Not
    // in tablet mode, where a touch moves the pointer. The handler leaves clicks to the button under it.
    Item {
        id: corner
        z: 1
        width: 8
        height: 8
        // The overview, only with its plugin's part installed.
        HoverHandler {
            id: cornerHover
            enabled: !Tablet.active && Installed.has("plugins", "hyprspace")
        }
    }
    Timer {
        interval: 220
        running: cornerHover.hovered
        onTriggered: {
            BarVisibility.wake();
            Quickshell.execDetached(["hyprctl", "eval", "if desktop_overview then desktop_overview(" + JSON.stringify(bar.screen.name) + ") end"]);
        }
    }
    TrayMenuWindow {
        id: trayMenuWindow
        screen: bar.screen
    }
    WindowMenuWindow {
        id: windowMenuWindow
        screen: bar.screen
    }
    BarMenuWindow {
        id: barMenu
        screen: bar.screen
    }
    Connections {
        target: ShellState
        function onPanelChanged() {
            if (ShellState.panel !== "") {
                trayMenuWindow.dismiss();
                windowMenuWindow.dismiss();
                barMenu.dismiss();
            }
        }
        function onWindowMenuRequested(screenName) {
            if (screenName === bar.screen.name)
                windowMenuWindow.popup(bar.titleWidget?.anchorItem ?? content, 0, bar.stripHeight);
        }
    }
    Item {
        id: stageItem
        anchors.fill: parent
        opacity: BarVisibility.userHidden ? 0 : 1
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.motionFast
            }
        }
        focus: true
        Keys.onEscapePressed: BarLayout.cancel()
        // Latched editing ends with a press outside the bar, the gallery and the hint.
        MouseArea {
            anchors.fill: parent
            enabled: bar.editing && BarLayout.latched
            onPressed: BarLayout.finish()
        }
        Item {
            id: strip
            width: parent.width
            height: bar.stripHeight
            // The empty part of the bar: a double click cycles the bar style, a right click or a long press
            // opens the bar menu.
            Item {
                anchors.fill: parent
                TapHandler {
                    enabled: !bar.editing
                    onDoubleTapped: BarStyle.toggle()
                    onLongPressed: bar.openBarMenu(point.position.x, point.position.y)
                }
                TapHandler {
                    enabled: !bar.editing
                    acceptedButtons: Qt.RightButton
                    onTapped: (eventPoint, button) => bar.openBarMenu(eventPoint.position.x, eventPoint.position.y)
                }
            }
            Rectangle {
                anchors.fill: parent
                opacity: bar.style === "shade" ? 1 : 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Theme.easeOut
                    }
                }
                gradient: Gradient {
                    GradientStop {
                        position: 0
                        color: Theme.barShadeTop
                    }
                    GradientStop {
                        position: 1
                        color: Theme.barShadeBottom
                    }
                }
            }
            Rectangle {
                x: Theme.barInset
                y: Theme.barInset
                width: parent.width - 2 * Theme.barInset
                height: Theme.barHeight
                radius: Theme.corner(14)
                color: Theme.surface
                border.width: 1
                border.color: Theme.stroke
                opacity: bar.style === "floating" ? 1 : 0
                visible: opacity > 0
                Behavior on opacity {
                    NumberAnimation {
                        duration: Theme.motionNormal
                        easing.type: Easing.BezierSpline
                        easing.bezierCurve: Theme.easeOut
                    }
                }
            }
            // The pills: one per section that shows, or one for the whole center block when merged.
            Repeater {
                model: bar.pills ? (bar.merged ? ["left", "block", "right"] : BarLayoutModel.sections) : []
                Rectangle {
                    id: pill
                    required property string modelData
                    readonly property Item target: modelData === "block" ? centerBlock : bar.sectionItem(modelData)
                    readonly property real start: modelData === "block" ? content.x + centerBlock.x : bar.sectionX(modelData)
                    readonly property real extent: modelData === "block" ? centerBlock.width : Math.min(target.width, target.naturalWidth)
                    visible: target.shows && extent > 0
                    x: start - 4
                    y: Theme.barInset + 1
                    width: extent + 8
                    height: Theme.barHeight - 2
                    radius: Theme.corner(14)
                    color: Theme.surface
                    border.width: 1
                    border.color: Theme.stroke
                }
            }
            Item {
                id: content
                readonly property int margin: bar.style === "floating" ? Theme.barInset + 8 : bar.pills ? Theme.barInset + 4 : 8
                x: margin
                y: Theme.barInset
                width: parent.width - 2 * margin
                height: Theme.barHeight
                // Transparent, everything on the bar gets a soft halo in the other text colour. Over a dark or a
                // light backdrop it barely shows; over a part of the wallpaper unlike the strip average it keeps
                // the outline.
                layer.enabled: BarStyle.transparent
                layer.effect: MultiEffect {
                    shadowEnabled: true
                    shadowColor: BarStyle.halo
                    shadowBlur: 0.5
                    blurMax: 8
                }
                BarSection {
                    id: leftSection
                    key: "left"
                    panel: bar
                    ids: bar.sectionIds.left
                    height: parent.height
                    // The window title takes what the center block (or the right section) leaves.
                    width: fills ? Math.max(fixedWidth, (centerBlock.shows ? centerBlock.x : rightSection.x) - bar.sectionGap) : naturalWidth
                }
                Row {
                    id: centerBlock
                    height: parent.height
                    spacing: bar.sectionGap
                    readonly property bool shows: centerLeftSection.shows || centerSection.shows || centerRightSection.shows
                    visible: shows
                    x: BarLayoutModel.centerX(content.width, width, leftSection.shows ? leftSection.fixedWidth : 0, rightSection.shows ? (rightSection.fills ? rightSection.fixedWidth : rightSection.naturalWidth) : 0, bar.sectionGap)
                    BarSection {
                        id: centerLeftSection
                        key: "centerLeft"
                        panel: bar
                        ids: bar.sectionIds.centerLeft
                        height: parent.height
                        width: fills ? Math.min(naturalWidth, Math.max(fixedWidth, Theme.hit(360))) : naturalWidth
                    }
                    BarSection {
                        id: centerSection
                        key: "center"
                        panel: bar
                        ids: bar.sectionIds.center
                        height: parent.height
                        width: fills ? Math.min(naturalWidth, Math.max(fixedWidth, Theme.hit(360))) : naturalWidth
                    }
                    BarSection {
                        id: centerRightSection
                        key: "centerRight"
                        panel: bar
                        ids: bar.sectionIds.centerRight
                        height: parent.height
                        width: fills ? Math.min(naturalWidth, Math.max(fixedWidth, Theme.hit(360))) : naturalWidth
                    }
                }
                BarSection {
                    id: rightSection
                    readonly property real leftEdge: centerBlock.shows ? centerBlock.x + centerBlock.width : leftSection.shows ? (leftSection.fills ? leftSection.fixedWidth : leftSection.naturalWidth) : 0
                    key: "right"
                    panel: bar
                    ids: bar.sectionIds.right
                    anchors.right: parent.right
                    height: parent.height
                    width: fills ? Math.max(fixedWidth, Math.min(naturalWidth, content.width - leftEdge - bar.sectionGap)) : naturalWidth
                }
            }
            // Edit mode: the outline, the name and the + of every section.
            Repeater {
                model: bar.editing ? BarLayoutModel.sections : []
                Item {
                    id: outline
                    required property string modelData
                    readonly property Item section: bar.sectionItem(modelData)
                    readonly property bool target: bar.dropTarget?.section === modelData
                    visible: section.shows
                    x: bar.sectionX(modelData) - 4
                    y: Theme.barInset + 1
                    width: section.width + 8
                    height: Theme.barHeight - 2
                    z: 1
                    Rectangle {
                        anchors.fill: parent
                        radius: Theme.corner(12)
                        color: Qt.alpha(Theme.accent, outline.target ? 0.16 : 0.06)
                        border.width: 1
                        border.color: Qt.alpha(Theme.accent, outline.target ? 1 : 0.5)
                    }
                    Rectangle {
                        anchors {
                            top: parent.bottom
                            topMargin: 8
                            horizontalCenter: parent.horizontalCenter
                        }
                        width: label.implicitWidth + 14
                        height: label.implicitHeight + 6
                        radius: Theme.corner(6)
                        color: Theme.accent
                        Text {
                            id: label
                            anchors.centerIn: parent
                            text: bar.sectionName(outline.modelData) + " · " + bar.sectionIds[outline.modelData].length
                            color: Theme.accentText
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(11)
                            font.weight: Font.DemiBold
                        }
                    }
                }
            }
            // Presses on the widgets while editing: a drag moves one, a right click opens its menu.
            MouseArea {
                id: catcher
                property var pressedSlot: null
                property point pressPoint: Qt.point(0, 0)
                x: content.x
                width: content.width
                height: parent.height
                z: 2
                enabled: bar.editing
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                preventStealing: true
                cursorShape: bar.drag ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                onPressed: mouse => {
                    const point = mapToItem(stageItem, mouse.x, mouse.y);
                    pressedSlot = bar.slotAt(point.x);
                    pressPoint = point;
                    if (mouse.button === Qt.RightButton && pressedSlot)
                        bar.openWidgetMenu(pressedSlot, point);
                }
                onPositionChanged: mouse => {
                    const point = mapToItem(stageItem, mouse.x, mouse.y);
                    if (bar.drag)
                        bar.moveDrag(point);
                    else if (pressedSlot && (mouse.buttons & Qt.LeftButton) && Math.abs(point.x - pressPoint.x) + Math.abs(point.y - pressPoint.y) > 6)
                        bar.startDrag(Object.assign({
                            from: "bar"
                        }, pressedSlot), point);
                }
                onReleased: {
                    if (bar.drag)
                        bar.endDrag();
                    pressedSlot = null;
                }
                onCanceled: {
                    bar.cancelDrag();
                    pressedSlot = null;
                }
            }
            Repeater {
                model: bar.editing ? BarLayoutModel.sections : []
                CompactIconButton {
                    required property string modelData
                    readonly property Item section: bar.sectionItem(modelData)
                    visible: section.shows
                    x: bar.sectionX(modelData) + section.width - width - 1
                    y: Theme.barInset + (Theme.barHeight - height) / 2
                    z: 3
                    iconName: "plus"
                    iconSize: Theme.hit(14)
                    implicitWidth: Theme.hit(26)
                    implicitHeight: Theme.hit(26)
                    tooltip: I18n.tr("bar.edit.add", [bar.sectionName(modelData)])
                    onClicked: bar.openGallery(modelData)
                }
            }
            Rectangle {
                visible: bar.dropTarget?.section !== undefined
                x: bar.dropTarget?.caretX ?? 0
                y: Theme.barInset + (Theme.barHeight - height) / 2
                z: 4
                width: 3
                height: Theme.hit(24)
                radius: 1.5
                color: Theme.accent
            }
        }
        Rectangle {
            id: trash
            readonly property bool target: bar.dropTarget?.trash === true
            visible: bar.drag?.from === "bar"
            anchors.horizontalCenter: parent.horizontalCenter
            y: bar.stripHeight + 44
            width: Math.min(340, parent.width - 40)
            height: 60
            radius: Theme.radius
            color: target ? Qt.alpha(Theme.danger, 0.28) : Theme.surface
            border.width: 1
            border.color: Qt.alpha(Theme.danger, target ? 1 : 0.6)
            RowLayout {
                anchors.centerIn: parent
                spacing: 10
                Icon {
                    name: "trash"
                    color: Theme.text
                    Layout.preferredWidth: 18
                    Layout.preferredHeight: 18
                }
                Text {
                    text: I18n.tr("bar.edit.remove")
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(13)
                }
            }
        }
        BarGallery {
            id: gallery
            panel: bar
            visible: bar.editing && bar.gallerySection !== "" && bar.drag?.from !== "bar"
            anchors.horizontalCenter: parent.horizontalCenter
            y: bar.stripHeight + 44
            width: Math.min(Theme.dialogWide, parent.width - 40)
            height: implicitHeight
            onCloseRequested: bar.gallerySection = ""
        }
        // What editing is about, and how it ends.
        Rectangle {
            visible: bar.editing
            anchors.horizontalCenter: parent.horizontalCenter
            y: parent.height - height - 28
            width: hint.implicitWidth + 32
            height: hint.implicitHeight + 20
            radius: Theme.radius
            color: Theme.surface
            border.width: 1
            border.color: Theme.stroke
            MouseArea {
                anchors.fill: parent
            }
            RowLayout {
                id: hint
                anchors.centerIn: parent
                spacing: 12
                Text {
                    text: BarLayout.latched ? I18n.tr("bar.edit.hintLatched") : I18n.tr("bar.edit.hint")
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(13)
                }
                ActionButton {
                    visible: BarLayout.latched
                    outlined: true
                    text: I18n.tr("common.cancel")
                    onClicked: BarLayout.cancel()
                }
                ActionButton {
                    visible: BarLayout.latched
                    highlighted: true
                    text: I18n.tr("bar.edit.done")
                    onClicked: BarLayout.finish()
                }
            }
        }
        // The widget under the pointer while it is dragged.
        Rectangle {
            visible: bar.drag !== null
            x: bar.dragPoint.x - width / 2
            y: bar.dragPoint.y - height / 2
            z: 10
            width: ghost.implicitWidth + 20
            height: Theme.hit(32)
            radius: Theme.corner(10)
            color: Theme.raised
            border.width: 1
            border.color: Theme.accent
            RowLayout {
                id: ghost
                anchors.centerIn: parent
                spacing: 8
                Icon {
                    name: Registry.find(bar.drag?.id ?? "")?.glyph ?? ""
                    color: Theme.text
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                }
                Text {
                    text: bar.drag ? I18n.tr(Registry.nameKey(bar.drag.id)) : ""
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(12)
                }
            }
        }
    }
}
