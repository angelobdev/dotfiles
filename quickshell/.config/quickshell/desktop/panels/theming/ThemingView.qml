import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../.."
import "../../components"
import "../../services"

// Appearance: the theme, wallpaper, font, icons and cursors tabs, the glass and store pages, and the restart
// banner. Settings shows it as a section (panels/SettingsPanel.qml); its pages call back through `panel`.
ColumnLayout {
    id: root
    // The section title, shown left of the tab chips.
    property string title: ""
    // The section is on screen: Ctrl+Tab and the Theming refresh are for it only.
    property bool active: false
    property string tab: ShellState.recall("theming/tab", "theme")
    onTabChanged: ShellState.remember("theming/tab", tab)
    // "glass" is a page of the Theme tab, reached from the card of a theme with liquid glass.
    // "store" is a page of the Cursors or Icons tab: the KDE Store, for cursor or icon themes (Store.kind).
    readonly property var tabs: ["theme", "wallpaper", "font", "icons", "cursors", "glass", "store"]
    readonly property var cycle: ["theme", "wallpaper", "font", "icons", "cursors"]
    // The tab a page belongs to: glass to Theme, the store to the kind it shows.
    readonly property string shownTab: tab === "glass" ? "theme" : tab === "store" ? (Store.kind === "cursors" ? "cursors" : "icons") : tab
    spacing: 14
    function showTab(name) {
        tab = name;
        if (name === "wallpaper")
            Theming.makeThumbs();
        // The tab shown by then: a later showTab in the same turn (IPC right after opening) wins, so focus never
        // stays on a hidden page, where Enter would act on it.
        Qt.callLater(() => {
            const page = [themePage, wallpaperPage, fontPage, iconsPage, cursorsPage, glassPage, storePage][tabs.indexOf(root.tab)];
            page?.item?.focusItem?.forceActiveFocus();
        });
    }
    // Opening the section: fresh lists, and the remembered tab.
    function activate() {
        Theming.refresh();
        showTab(tab);
    }
    // A tab by name, or store-icons / store-cursors for the KDE Store page; anything else opens as activate().
    function open(name) {
        if (name === "store-icons" || name === "store-cursors") {
            Theming.refresh();
            openStore(name.slice(6));
        } else if (cycle.includes(name)) {
            Theming.refresh();
            showTab(name);
        } else {
            activate();
        }
    }
    function openStore(kind) {
        if (Store.kind !== kind || Store.items.length === 0)
            Store.search(kind, "");
        Store.refreshInstalled();
        showTab("store");
    }
    function cycleTab(step) {
        const from = Math.max(0, cycle.indexOf(shownTab));
        showTab(cycle[(from + step + cycle.length) % cycle.length]);
    }
    // Labels of the glass options theme.py offers (GLASS_TUNING); an unknown one shows its own name.
    function glassLabel(option) {
        const labels = {
            blur_strength: I18n.tr("theming.glassOptions.blurStrength"),
            refraction_strength: I18n.tr("theming.glassOptions.refractionStrength"),
            chromatic_aberration: I18n.tr("theming.glassOptions.chromaticAberration"),
            edge_thickness_px: I18n.tr("theming.glassOptions.edgeThicknessPx"),
            edge_height: I18n.tr("theming.glassOptions.edgeHeight"),
            fresnel_reflection: I18n.tr("theming.glassOptions.fresnelReflection"),
            specular_strength: I18n.tr("theming.glassOptions.specularStrength"),
            bevel_strength: I18n.tr("theming.glassOptions.bevelStrength"),
            noise_strength: I18n.tr("theming.glassOptions.noiseStrength")
        };
        return labels[option] ?? option;
    }
    function glassText(entry, value) {
        return entry.step >= 1 ? String(Math.round(value)) + " px" : Number(value).toFixed(2);
    }
    // A theme without liquid glass (another theme chosen meanwhile) has no glass page.
    Connections {
        target: Theming
        function onGlassChanged() {
            if (root.tab === "glass" && !Theming.glass)
                root.showTab("theme");
        }
    }
    // Ctrl+Tab and Ctrl+Shift+Tab switch tabs from any page.
    Shortcut {
        enabled: root.active
        sequences: ["Ctrl+Tab", "Ctrl+PgDown"]
        onActivated: root.cycleTab(1)
    }
    Shortcut {
        enabled: root.active
        sequences: ["Ctrl+Shift+Tab", "Ctrl+PgUp"]
        onActivated: root.cycleTab(-1)
    }
    RowLayout {
        Layout.fillWidth: true
        Heading {
            Layout.fillWidth: true
            text: root.title
        }
        ChoiceChips {
            Layout.fillWidth: false
            options: [
                {
                    name: "theme",
                    label: I18n.tr("theming.tabs.theme")
                },
                {
                    name: "wallpaper",
                    label: I18n.tr("theming.tabs.wallpaper")
                },
                {
                    name: "font",
                    label: I18n.tr("theming.tabs.font")
                },
                {
                    name: "icons",
                    label: I18n.tr("theming.tabs.icons")
                },
                {
                    name: "cursors",
                    label: I18n.tr("theming.tabs.cursors")
                }
            ]
            current: root.shownTab
            onChosen: name => root.showTab(name)
        }
    }
    StackLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: root.tabs.indexOf(root.tab)
        // A swipe over the page switches tab, as Ctrl+Tab does.
        TabSwipe {
            onSwiped: step => root.cycleTab(step)
        }
        // Each page is built the first time its tab shows, then kept (the section opens on one tab).
        // Theme: a card per theme with a small mock-up of its surfaces and accent, and its colours.
        Loader {
            id: themePage
            property bool visited: false
            active: visited || root.tab === "theme"
            onLoaded: visited = true
            sourceComponent: ThemePage {
                panel: root
            }
        }
        // Wallpaper: the set of the current theme, then "Custom…" for any image.
        Loader {
            id: wallpaperPage
            property bool visited: false
            active: visited || root.tab === "wallpaper"
            onLoaded: visited = true
            sourceComponent: WallpaperPage {
                panel: root
            }
        }
        // Font: interface and monospace families, each shown in itself, and the size.
        Loader {
            id: fontPage
            property bool visited: false
            active: visited || root.tab === "font"
            onLoaded: visited = true
            sourceComponent: FontPage {
                panel: root
            }
        }
        // Icons: each pack with its own sample icons, and where the shell glyphs come from.
        Loader {
            id: iconsPage
            property bool visited: false
            active: visited || root.tab === "icons"
            onLoaded: visited = true
            sourceComponent: IconsPage {
                panel: root
            }
        }
        // Cursors: each theme with five of its own shapes at the chosen size, and the size.
        Loader {
            id: cursorsPage
            property bool visited: false
            active: visited || root.tab === "cursors"
            onLoaded: visited = true
            sourceComponent: CursorsPage {
                panel: root
            }
        }
        // Glass: the Hyprglass options of the current theme, each saved as it is released.
        Loader {
            id: glassPage
            property bool visited: false
            active: visited || root.tab === "glass"
            onLoaded: visited = true
            sourceComponent: GlassPage {
                panel: root
            }
        }
        // Store: cursor or icon themes from store.kde.org, most downloaded first; each card installs one of
        // its files, and removes what it installed.
        Loader {
            id: storePage
            property bool visited: false
            active: visited || root.tab === "store"
            onLoaded: visited = true
            sourceComponent: StorePage {
                panel: root
            }
        }
    }
    // Fonts and icons reach the shell after a restart; the rest of the desktop has them already.
    Rectangle {
        Layout.fillWidth: true
        visible: Theming.restartTab !== ""
        implicitHeight: restartRow.implicitHeight + 16
        radius: Theme.corner(12)
        color: Theme.tile
        RowLayout {
            id: restartRow
            anchors {
                fill: parent
                margins: 8
                leftMargin: 14
            }
            Text {
                Layout.fillWidth: true
                text: I18n.tr("theming.restartHint")
                wrapMode: Text.Wrap
                color: Theme.muted
                font.family: Theme.font
                font.pixelSize: Theme.textSize(12)
            }
            ActionButton {
                text: I18n.tr("theming.restart")
                onClicked: Theming.restartShell()
            }
        }
    }
    Text {
        Layout.fillWidth: true
        visible: Theming.error !== ""
        text: Theming.error
        textFormat: Text.PlainText
        wrapMode: Text.Wrap
        color: Theme.danger
        font.pixelSize: Theme.textSize(12)
    }
    Text {
        // Wraps instead of widening the layout past the panel (wide theme fonts, long translations).
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        text: Theming.busy ? I18n.tr("theming.working") : Tablet.active ? "" : I18n.tr("theming.navigationHint")
        color: Theme.muted
        font.family: Theme.font
        font.pixelSize: Theme.textSize(12)
    }
}
