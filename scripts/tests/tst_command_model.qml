import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/services/CommandModel.js" as Model

TestCase {
    name: "CommandModel"

    readonly property var data: ({
            "system": {
                "label": "System"
            },
            "system.lock": {
                "label": "Lock screen",
                "session": "lock"
            },
            "system.reboot": {
                "label": "Restart",
                "session": "reboot",
                "alt": "system.firmware"
            },
            "system.firmware": {
                "label": "Restart to firmware setup",
                "session": "firmware",
                "when": "efi"
            },
            "system.profile": {
                "label": "Power profile",
                "rows": "powerProfiles"
            },
            "toggles": {
                "label": "Toggles"
            },
            "toggles.awake": {
                "label": "Keep awake",
                "state": "keepAwake",
                "call": ["keepAwake", "toggle"]
            },
            "toggles.rotation": {
                "label": "Rotation lock",
                "when": ["tablet", "!docked"],
                "call": ["rotationLock", "toggle"]
            },
            "empty": {
                "label": "Empty"
            },
            "empty.inner": {
                "label": "Inner",
                "when": "never",
                "run": ["true"]
            },
            "updates": {
                "label": "Updates"
            },
            "updates.restart": {
                "label": "Restart to apply updates",
                "enabled": "restartNeeded",
                "session": "reboot"
            },
            "bad id!": {
                "label": "Skipped",
                "run": ["true"]
            },
            "orphan.child": {
                "label": "Orphan",
                "run": ["true"]
            },
            "notAnObject": 3
        })
    readonly property var model: Model.parse(data)
    readonly property var state: ({
            efi: true,
            keepAwake: true,
            tablet: true,
            docked: false
        })

    function label(entry) {
        return entry.label;
    }
    function ids(entries) {
        return entries.map(entry => entry.id);
    }

    function test_parseKeepsOrderAndParents() {
        compare(model.order.length, 13);
        compare(model.items["system.lock"].parent, "system");
        compare(model.items["system"].parent, "");
        // A parent that does not exist puts the entry on the first level.
        compare(model.items["orphan.child"].parent, "");
        verify(!("bad id!" in model.items));
        verify(!("notAnObject" in model.items));
        compare(Model.parse(null).order.length, 0);
        compare(Model.parse([1, 2]).order.length, 0);
    }

    function test_kinds() {
        verify(Model.isCommand(model.items["system.lock"]));
        verify(Model.opens(model.items["system"]));
        verify(Model.opens(model.items["system.profile"]));
        verify(Model.hasRows(model.items["system.profile"]));
        verify(!Model.hasRows(model.items["system"]));
    }

    function test_conditions() {
        verify(Model.holds(undefined, state));
        verify(Model.holds("", state));
        verify(Model.holds("efi", state));
        verify(!Model.holds("!efi", state));
        verify(!Model.holds("missing", state));
        verify(Model.holds("!missing", state));
        verify(Model.holds(["tablet", "!docked"], state));
        verify(!Model.holds(["tablet", "docked"], state));
    }

    function test_firstLevelHidesEmptyCategories() {
        compare(ids(Model.children(model, "", state)), ["system", "toggles", "updates", "orphan.child"]);
    }

    function test_alternatesAreLeftOutOfTheirCategory() {
        compare(ids(Model.children(model, "system", state)), ["system.lock", "system.reboot", "system.profile"]);
    }

    function test_variantWithAlt() {
        const reboot = model.items["system.reboot"];
        compare(Model.variant(model, reboot, state, false).id, "system.reboot");
        compare(Model.variant(model, reboot, state, true).id, "system.firmware");
        // Without EFI the stand-in does not show: the entry stays itself.
        compare(Model.variant(model, reboot, { efi: false }, true).id, "system.reboot");
        compare(Model.variant(model, model.items["system.lock"], state, true).id, "system.lock");
    }

    function test_switchAndEnabled() {
        compare(Model.switchState(model.items["toggles.awake"], state), "on");
        compare(Model.switchState(model.items["toggles.awake"], {}), "off");
        compare(Model.switchState(model.items["system.lock"], state), "");
        verify(!Model.enabled(model.items["updates.restart"], state));
        verify(Model.enabled(model.items["updates.restart"], { restartNeeded: true }));
    }

    function test_whenWithAList() {
        compare(ids(Model.children(model, "toggles", state)), ["toggles.awake", "toggles.rotation"]);
        compare(ids(Model.children(model, "toggles", { docked: true, tablet: true })), ["toggles.awake"]);
    }

    function test_searchFindsCommandsAndStandIns() {
        // Both restarts match; the plain prefix match of the label comes first, then file order.
        compare(ids(Model.search(model, "restart", state, label)), ["system.reboot", "system.firmware", "updates.restart"]);
        // A category's name counts as another word of its commands.
        compare(ids(Model.search(model, "toggles", state, label)), ["toggles.awake", "toggles.rotation"]);
        // Hidden entries and those under a hidden category are not found.
        compare(ids(Model.search(model, "restart to firmware", { efi: false }, label)), []);
        compare(ids(Model.search(model, "inner", state, label)), []);
    }

    function test_searchWithinACategory() {
        compare(ids(Model.search(model, "restart", state, label, "updates")), ["updates.restart"]);
    }

    function test_searchIncludesProviderRows() {
        const rows = {
            "system.profile": [
                {
                    id: "system.profile.balanced",
                    parent: "system.profile",
                    label: "Balanced"
                },
                {
                    id: "system.profile.performance",
                    parent: "system.profile",
                    label: "Performance"
                }
            ]
        };
        compare(ids(Model.search(model, "perf", state, label, "", rows)), ["system.profile.performance"]);
        // Found by the name of their category too.
        compare(ids(Model.search(model, "power profile", state, label, "", rows)).length, 2);
    }

    function test_matchesCarryTheirTier() {
        const found = Model.matches(model, "lock", state, label);
        compare(found.map(match => match.entry.id), ["system.lock", "toggles.rotation"]);
        verify(found[0].tier < found[1].tier);
    }

}
