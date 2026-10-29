import QtQuick
import ".."
import "../services"

SwitchRow {
    icon: Notices.quiet ? "bell-off" : "bell"
    title: I18n.tr("notifications.doNotDisturb")
    status: Notices.quiet ? I18n.tr("notifications.silenced") : I18n.tr("notifications.enabled")
    checked: Notices.quiet
    onToggled: checked => Notices.setQuiet(checked)
}
