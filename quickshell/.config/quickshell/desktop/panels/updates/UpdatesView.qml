import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// Available updates: what would be updated (packages, Flatpak apps, the new commits of this repository), when it
// was checked, Check now, and Update, which applies the switched-on sections in the background (Updates.apply: one
// password or fingerprint prompt when root is needed) and shows its progress and log here. The updates panel (its bar
// icon) and Settings → Updates show it.
ColumnLayout {
    id: root
    // On screen (kept for its hosts; the lists come from the Updates service).
    property bool shown: false
    readonly property Item focusItem: root
    // Package rows shown at most; the list says how many more there are.
    readonly property int packageRows: 100
    spacing: 12
    // Sections switched off for the next Update; all of them are on by default.
    property var skipped: ({})
    // What Update applies: the sections with updates that are switched on. The repository only when it can be
    // fast-forwarded; it goes first, and the rest is applied by its new version.
    readonly property var keys: {
        const keys = [];
        if (Updates.packages.length > 0 && !skipped.system)
            keys.push("system");
        if (Updates.flatpaks.length > 0 && !skipped.flatpak)
            keys.push("flatpak");
        if (Updates.firmware.length > 0 && !skipped.firmware)
            keys.push("firmware");
        if (Updates.pullable && !skipped.repository)
            keys.push("repository");
        return keys;
    }
    function toggle(key, on) {
        const next = Object.assign({}, skipped);
        next[key] = !on;
        skipped = next;
    }
    readonly property var applied: Updates.applyState
    // A new release on the way: its changelog takes the place of the commits (a maintainer between releases sees those).
    readonly property var notes: Array.isArray(Updates.repository.notes) ? Updates.repository.notes.filter(note => note && typeof note.notes === "string") : []
    readonly property bool release: typeof Updates.repository.latest === "string" && Updates.repository.latest !== "" && Updates.repository.latest !== Updates.repository.version
    function result() {
        if (Updates.applying)
            return I18n.tr("updates.apply.applying");
        if (applied.finished === undefined)
            return applied.status === -1 ? I18n.tr("updates.apply.stopped") : "";
        if (applied.status === 0)
            return I18n.tr(applied.compositor ? "updates.apply.lastDoneCompositor" : "updates.apply.lastDone", [root.moment(applied.finished * 1000)]);
        if (applied.status === -1)
            return I18n.tr("updates.apply.stopped");
        // A known cause (updates.py FAILURES) says what to do instead of the status number.
        if (typeof applied.reason === "string" && applied.reason !== "")
            return I18n.tr("updates.apply.failed", [I18n.tr(root.reasonKey(applied.reason))]);
        return I18n.tr("updates.apply.lastFailed", [applied.status]);
    }
    function reasonKey(reason) {
        return "updates.apply.reasons." + reason;
    }
    function restartKey(reason) {
        return "updates.restart." + reason;
    }
    // A time today, or a day and a time.
    function moment(milliseconds) {
        const date = new Date(milliseconds);
        if (date.toDateString() === new Date().toDateString())
            return I18n.locale.toString(date, I18n.timeFormat);
        return I18n.locale.toString(date, I18n.tr("assistant.dayFormat") + " " + I18n.timeFormat);
    }
    function when(milliseconds) {
        const date = new Date(milliseconds);
        if (date.toDateString() === new Date().toDateString())
            return I18n.tr("updates.checkedAt", [I18n.locale.toString(date, I18n.timeFormat)]);
        return I18n.tr("updates.checkedOn", [I18n.locale.toString(date, I18n.tr("assistant.dayFormat") + " " + I18n.timeFormat)]);
    }
    function summary() {
        if (Updates.count === 0)
            return I18n.tr("updates.upToDate");
        const parts = [];
        if (Updates.packages.length > 0)
            parts.push(I18n.plural("updates.summary.packages.one", "updates.summary.packages.other", Updates.packages.length));
        if (Updates.flatpaks.length > 0)
            parts.push(I18n.plural("updates.summary.flatpaks.one", "updates.summary.flatpaks.other", Updates.flatpaks.length));
        if (Updates.firmware.length > 0)
            parts.push(I18n.plural("updates.summary.firmware.one", "updates.summary.firmware.other", Updates.firmware.length));
        if (Updates.behind > 0 && root.release)
            parts.push(I18n.tr("updates.summary.release", [Updates.repository.latest]));
        else if (Updates.behind > 0)
            parts.push(I18n.plural("updates.summary.commits.one", "updates.summary.commits.other", Updates.behind));
        return parts.join(" · ");
    }
    // A heading with the switch that keeps its section in or out of the next Update.
    component Section: RowLayout {
        property alias text: heading.text
        property string key
        property bool switchable: true
        Layout.fillWidth: true
        spacing: 10
        Heading {
            id: heading
            Layout.fillWidth: true
            section: true
        }
        ControlSwitch {
            visible: parent.switchable
            enabled: !Updates.applying
            checked: !root.skipped[parent.key]
            onToggled: root.toggle(parent.key, checked)
        }
    }
    component Entry: RowLayout {
        property string name
        property string version
        Layout.fillWidth: true
        spacing: 10
        Text {
            Layout.fillWidth: true
            text: parent.name
            elide: Text.ElideRight
            color: Theme.text
            font.family: Theme.font
            font.pixelSize: Theme.textSize(12)
            textFormat: Text.PlainText
        }
        Text {
            text: parent.version
            color: Theme.muted
            font.family: Theme.font
            font.pixelSize: Theme.textSize(11)
            textFormat: Text.PlainText
        }
    }
    Text {
        Layout.fillWidth: true
        text: root.summary()
        color: Theme.text
        font.family: Theme.font
        font.pixelSize: Theme.textSize(15)
        wrapMode: Text.Wrap
    }
    // A restart is needed for what an update replaced, with the reasons and the session menu one click away.
    Rectangle {
        Layout.fillWidth: true
        visible: Updates.restartNeeded && !Updates.applying
        implicitHeight: restartRow.implicitHeight + 20
        radius: Theme.corner(10)
        color: Theme.active
        RowLayout {
            id: restartRow
            anchors {
                fill: parent
                margins: 10
                leftMargin: 12
            }
            spacing: 10
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Text {
                    Layout.fillWidth: true
                    text: I18n.tr("updates.restart.title")
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(13)
                    font.weight: Font.DemiBold
                }
                Text {
                    Layout.fillWidth: true
                    text: Updates.restartReasons.map(reason => I18n.tr(root.restartKey(reason))).join(" ")
                    wrapMode: Text.Wrap
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(12)
                }
            }
            ActionButton {
                highlighted: true
                text: I18n.tr("updates.restart.action")
                onClicked: ShellState.open("power")
            }
        }
    }
    Text {
        Layout.fillWidth: true
        visible: Updates.compositor
        text: I18n.tr("updates.compositor")
        color: Theme.danger
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        wrapMode: Text.Wrap
    }
    ScrollView {
        id: scroll
        visible: Updates.count > 0
        Layout.fillWidth: true
        Layout.fillHeight: true
        Layout.preferredHeight: Math.min(list.implicitHeight, 320)
        Layout.minimumHeight: Math.min(list.implicitHeight, 120)
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            id: list
            width: scroll.availableWidth
            spacing: 6
            // Each section is its heading and switch over a card of its entries, as on the option pages; the
            // scroll view around them stays the one element that scrolls.
            Section {
                visible: Updates.packages.length > 0
                text: I18n.tr("updates.packagesHeading")
                key: "system"
            }
            GroupCard {
                Layout.fillWidth: true
                visible: Updates.packages.length > 0
                verticalPadding: 10
                spacing: 6
                // The first ones only: a release upgrade lists a thousand packages and more, each one a row built
                // at once in this column. The count of the rest follows, as for the commits.
                Repeater {
                    model: Updates.packages.slice(0, root.packageRows)
                    Entry {
                        required property var modelData
                        name: modelData.name
                        version: modelData.version
                    }
                }
                Text {
                    visible: Updates.packages.length > root.packageRows
                    text: I18n.tr("updates.packagesMore", [Updates.packages.length - root.packageRows])
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(11)
                }
            }
            Section {
                visible: Updates.flatpaks.length > 0
                text: I18n.tr("updates.flatpaksHeading")
                key: "flatpak"
                Layout.topMargin: 12
            }
            GroupCard {
                Layout.fillWidth: true
                visible: Updates.flatpaks.length > 0
                verticalPadding: 10
                spacing: 6
                Repeater {
                    model: Updates.flatpaks
                    Entry {
                        required property var modelData
                        name: modelData.id
                        version: modelData.version
                    }
                }
            }
            Section {
                visible: Updates.firmware.length > 0
                text: I18n.tr("updates.firmwareHeading")
                key: "firmware"
                Layout.topMargin: 12
            }
            GroupCard {
                Layout.fillWidth: true
                visible: Updates.firmware.length > 0
                verticalPadding: 10
                spacing: 6
                Repeater {
                    model: Updates.firmware
                    Entry {
                        required property var modelData
                        name: modelData.name
                        version: modelData.current ? modelData.current + " → " + modelData.version : modelData.version
                    }
                }
            }
            Section {
                visible: Updates.behind > 0
                text: I18n.tr("updates.repositoryHeading", [Updates.repository.upstream ?? ""])
                key: "repository"
                switchable: Updates.pullable
                Layout.topMargin: 12
            }
            GroupCard {
                Layout.fillWidth: true
                // Not an empty tile when the check found no commit subjects to list.
                visible: Updates.behind > 0 && (Updates.commits.length > 0 || root.notes.length > 0 || Updates.repository.ahead > 0 || Updates.repository.dirty === true)
                verticalPadding: 10
                spacing: 6
                // What stops the fast-forward of the updates screen, as found at the check.
                Text {
                    Layout.fillWidth: true
                    visible: Updates.repository.ahead > 0 || Updates.repository.dirty === true
                    // A clone on main past the last release waits for the next one; any other clone is merged by hand.
                    text: I18n.tr(Updates.repository.ahead > 0 ? (String(Updates.repository.upstream ?? "").endsWith("/stable") ? "updates.repositoryNewer" : "updates.repositoryAhead") : "updates.repositoryDirty")
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(11)
                    wrapMode: Text.Wrap
                }
                Text {
                    Layout.fillWidth: true
                    visible: root.release
                    text: I18n.tr("updates.repositoryRelease", [Updates.repository.version || "—", Updates.repository.latest ?? ""])
                    color: Theme.text
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(12)
                    font.weight: Font.DemiBold
                    textFormat: Text.PlainText
                }
                Repeater {
                    model: Updates.behind > 0 ? root.notes : []
                    ColumnLayout {
                        id: note
                        required property var modelData
                        Layout.fillWidth: true
                        spacing: 4
                        Heading {
                            visible: root.notes.length > 1
                            section: true
                            text: note.modelData.version
                        }
                        // The changelog of this repository, written as Markdown for this view and for GitHub.
                        Text {
                            Layout.fillWidth: true
                            text: note.modelData.notes
                            textFormat: Text.MarkdownText
                            wrapMode: Text.Wrap
                            color: Theme.text
                            linkColor: Theme.accent
                            font.family: Theme.font
                            font.pixelSize: Theme.textSize(12)
                            onLinkActivated: link => Qt.openUrlExternally(link)
                        }
                    }
                }
                Repeater {
                    model: Updates.behind > 0 && root.notes.length === 0 ? Updates.commits : []
                    Entry {
                        required property var modelData
                        name: modelData.subject
                        version: modelData.hash
                    }
                }
                Text {
                    visible: root.notes.length === 0 && Updates.behind > Updates.commits.length && Updates.commits.length > 0
                    text: I18n.tr("updates.repositoryMore", [Updates.behind - Updates.commits.length])
                    color: Theme.muted
                    font.family: Theme.font
                    font.pixelSize: Theme.textSize(11)
                }
            }
        }
    }
    Repeater {
        model: Updates.errors
        Text {
            required property string modelData
            Layout.fillWidth: true
            text: modelData
            color: Theme.danger
            font.family: Theme.font
            font.pixelSize: Theme.textSize(11)
            wrapMode: Text.Wrap
            textFormat: Text.PlainText
        }
    }
    // The last Update: its progress, its result and, while it runs or when it failed, the end of its log.
    Text {
        Layout.fillWidth: true
        visible: text !== ""
        text: root.result()
        color: Updates.applying || root.applied.status === 0 ? Theme.text : Theme.danger
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
        wrapMode: Text.Wrap
    }
    Rectangle {
        Layout.fillWidth: true
        visible: Updates.applyLog.length > 0 && (Updates.applying || root.applied.status !== 0)
        implicitHeight: logText.implicitHeight + 16
        radius: Theme.corner(10)
        color: Theme.tile
        Text {
            id: logText
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
                margins: 8
            }
            text: Updates.applyLog.slice(-8).join("\n")
            textFormat: Text.PlainText
            wrapMode: Text.WrapAnywhere
            color: Theme.text
            font.family: "monospace"
            font.pixelSize: Theme.textSize(10)
        }
    }
    Text {
        Layout.fillWidth: true
        text: Updates.checking ? I18n.tr("updates.checking") : Updates.checked > 0 ? root.when(Updates.checked) : I18n.tr("updates.never")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(11)
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        ActionButton {
            outlined: true
            Layout.fillWidth: true
            text: I18n.tr("updates.checkNow")
            enabled: !Updates.checking
            onClicked: Updates.check()
        }
        ActionButton {
            // Nothing to install: only "Check now" remains (the installing state stays visible while it runs).
            visible: Updates.count > 0 || Updates.applying
            Layout.fillWidth: true
            highlighted: true
            iconName: "update"
            text: Updates.applying ? I18n.tr("updates.apply.applying") : I18n.tr("updates.install")
            enabled: !Updates.applying && root.keys.length > 0
            onClicked: Updates.apply(root.keys)
        }
    }
}
