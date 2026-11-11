import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/services/BindKeys.js" as BindKeys

TestCase {
    name: "BindKeys"
    // As hyprctl binds -j gives them, lowercased by HyprSettings.
    readonly property var taken: [
        {
            mask: 64,
            key: "b",
            description: "Browser"
        },
        {
            mask: 65,
            key: "b",
            description: "Battery & power"
        },
        {
            mask: 64,
            key: "period",
            description: "Emoji"
        },
        {
            mask: 64,
            key: "f12",
            description: "My test"
        }
    ]

    function test_validKeys() {
        verify(BindKeys.valid("SUPER + B"));
        verify(BindKeys.valid("super + shift + period"));
        verify(BindKeys.valid("XF86AudioMute"));
        verify(!BindKeys.valid("HYPER + B"));
        verify(!BindKeys.valid("SUPER +"));
        verify(!BindKeys.valid("SUPER + B C"));
        verify(!BindKeys.valid(""));
    }

    function test_theMaskAddsTheModifiers() {
        compare(BindKeys.combo("SUPER + SHIFT + b"), {
            mask: 65,
            key: "b"
        });
        compare(BindKeys.combo("ctrl + alt + Delete"), {
            mask: 12,
            key: "delete"
        });
    }

    function test_takenKeysNameTheirBinds() {
        compare(BindKeys.takenBy(taken, "SUPER + b", "x"), ["Browser"]);
        compare(BindKeys.takenBy(taken, "SUPER + SHIFT + B", "x"), ["Battery & power"]);
        compare(BindKeys.takenBy(taken, "SUPER + CTRL + B", "x"), []);
        compare(BindKeys.takenBy(taken, "nonsense +", "x"), []);
    }

    function test_keysHaveReadableNames() {
        const tr = key => "<" + key + ">";
        compare(BindKeys.keyName("XF86Calculator", tr), "<keys.calculator>");
        compare(BindKeys.keyName("XF86AudioRaiseVolume", tr), "<keys.volumeUp>");
        compare(BindKeys.keyName("XF86MonBrightnessDown", tr), "<keys.brightnessDown>");
        compare(BindKeys.keyName("XF86AudioPrev", tr), "<keys.previousTrack>");
        compare(BindKeys.keyName("Return", tr), "<keys.enter>");
        compare(BindKeys.keyName("Print", tr), "<keys.print>");
        compare(BindKeys.keyName("space", tr), "<keys.space>");
        compare(BindKeys.keyName("mouse:272", tr), "<keys.leftMouse>");
        compare(BindKeys.keyName("period", tr), ".");
        compare(BindKeys.keyName("comma", tr), ",");
        compare(BindKeys.keyName("Left", tr), "←");
    }

    function test_unknownKeysKeepTheirName() {
        const tr = key => "<" + key + ">";
        compare(BindKeys.keyName("F5", tr), "F5");
        compare(BindKeys.keyName("XF86Launch9", tr), "XF86Launch9");
        compare(BindKeys.keyName("constructor", tr), "constructor");
        compare(BindKeys.keyName(undefined, tr), "");
    }

    function test_theRowsOwnBindIsNotAConflict() {
        // The bind this row saved carries its description: not reported against itself.
        compare(BindKeys.takenBy(taken, "SUPER + F12", "My test"), []);
        compare(BindKeys.takenBy(taken.concat([{
                mask: 64,
                key: "f12",
                description: "My test"
            }]), "SUPER + F12", "My test"), ["My test"]);
    }
}
