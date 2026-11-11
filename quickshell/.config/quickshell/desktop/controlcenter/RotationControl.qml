import QtQuick
import ".."
import "../services"

// Shown only in tablet mode on a machine with an accelerometer: the lock does nothing in laptop mode
// (Controls.qml reads "available").
SwitchRow {
    readonly property bool available: Tablet.available && Tablet.active
    icon: Tablet.locked ? "rotate-lock" : "rotate"
    title: I18n.tr("tablet.rotationLock")
    status: Tablet.locked ? I18n.tr("tablet.locked") : I18n.tr("tablet.rotatesAutomatically")
    checked: Tablet.locked
    onToggled: checked => Tablet.setLocked(checked)
}
