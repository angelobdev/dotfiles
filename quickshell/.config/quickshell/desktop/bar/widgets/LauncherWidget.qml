import QtQuick
import Quickshell
import Quickshell.Io
import "../.."
import ".."

BarButton {
    id: root
    property var bar
    property bool shown: true
    // The distribution logo: the icon that os-release names (Fedora has one in the icon theme), else the icon
    // pack distributor-logo-<ID> (Papirus has one for Arch), else start-here.
    property string logo: Quickshell.iconPath("start-here")
    iconSource: logo
    iconSize: 18
    implicitWidth: Theme.hit(32)
    tooltip: I18n.tr("launcher.title")
    onClicked: ShellState.toggle("launcher", root.bar.screen)
    FileView {
        path: "/etc/os-release"
        blockLoading: true
        printErrors: false
        onLoaded: {
            const values = {};
            for (const line of text().split("\n")) {
                const match = line.match(/^(ID|LOGO)=(.*)$/);
                // Quotes, and anything else an icon name cannot hold, go.
                if (match)
                    values[match[1]] = match[2].replace(/[^A-Za-z0-9._-]/g, "");
            }
            root.logo = (values.LOGO ? Quickshell.iconPath(values.LOGO, true) : "") || Quickshell.iconPath("distributor-logo-" + (values.ID ?? ""), "start-here");
        }
    }
}
