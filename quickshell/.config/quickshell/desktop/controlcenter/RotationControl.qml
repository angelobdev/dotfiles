import QtQuick
import ".."
import "../services"

// Shown only where there is an accelerometer (Controls.qml reads "available").
SwitchRow {
    readonly property bool available: Tablet.available
    icon: Tablet.locked ? "rotate-lock" : "rotate"
    title: I18n.tr("tablet.rotationLock")
    status: Tablet.locked ? I18n.tr("tablet.locked") : Tablet.active ? I18n.tr("tablet.rotatesAutomatically") : I18n.tr("tablet.rotatesInTablet")
    checked: Tablet.locked
    onToggled: checked => Tablet.setLocked(checked)
}
