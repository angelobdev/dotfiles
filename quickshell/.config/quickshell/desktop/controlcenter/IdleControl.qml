import QtQuick
import ".."
import "../services"

SwitchRow {
    icon: "coffee"
    title: I18n.tr("idle.keepAwake")
    status: Idle.keepAwake ? I18n.tr("idle.inhibited") : I18n.tr("idle.automatic")
    checked: Idle.keepAwake
    onToggled: checked => Idle.setKeepAwake(checked)
}
