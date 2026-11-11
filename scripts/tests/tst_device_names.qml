import QtQuick
import QtTest
import "../../quickshell/.config/quickshell/desktop/services/DeviceNames.js" as DeviceNames

TestCase {
    name: "DeviceNames"

    // A catalog lookup that shows the key and its arguments.
    function tr(key, args) {
        return key + (args && args.length ? ":" + args.join(",") : "");
    }

    // A made-up laptop card as `pactl -f json list` shows it in the C locale (UCM port names, as on SOF).
    function dump() {
        const card = "alsa_card.pci-test";
        function port(name, type, availability, extra) {
            return Object.assign({
                description: name,
                availability: availability,
                availability_group: "",
                properties: {
                    "port.type": type
                }
            }, extra ?? {});
        }
        return {
            cards: [
                {
                    name: card,
                    ports: {
                        "[Out] HDMI1": port("HDMI / DisplayPort 1 Output", "hdmi", "available", {
                            availability_group: "HDMI/DP,pcm=3",
                            properties: {
                                "port.type": "hdmi",
                                "device.product.name": "ACME VIEW 27"
                            }
                        }),
                        "[Out] HDMI2": port("HDMI / DisplayPort 2 Output", "hdmi", "not available", {
                            availability_group: "HDMI/DP,pcm=4"
                        }),
                        "[Out] Speaker": port("Speaker", "speaker", "availability unknown"),
                        "[In] Mic1": port("Digital Microphone", "mic", "availability unknown"),
                        "[In] Mic2": port("Stereo Microphone", "mic", "not available", {
                            availability_group: "Mic"
                        })
                    }
                }
            ],
            sinks: [
                {
                    name: "out.hdmi1",
                    active_port: "[Out] HDMI1",
                    properties: {
                        "device.name": card
                    }
                },
                {
                    name: "out.hdmi2",
                    active_port: "[Out] HDMI2",
                    properties: {
                        "device.name": card
                    }
                },
                {
                    name: "out.speaker",
                    active_port: "[Out] Speaker",
                    properties: {
                        "device.name": card
                    }
                }
            ],
            sources: [
                {
                    name: "in.mic1",
                    active_port: "[In] Mic1",
                    properties: {
                        "device.name": card
                    }
                },
                {
                    name: "in.mic2",
                    active_port: "[In] Mic2",
                    properties: {
                        "device.name": card
                    }
                },
                {
                    name: "in.unknown",
                    active_port: "[In] Gone",
                    properties: {
                        "device.name": card
                    }
                }
            ]
        };
    }

    function node(name, description, properties) {
        return {
            name: name,
            description: description,
            properties: properties ?? {}
        };
    }

    function test_portsAreFoundThroughTheirCard() {
        const ports = DeviceNames.audioPorts(dump());
        compare(ports["out.hdmi1"].type, "hdmi");
        compare(ports["out.hdmi1"].available, true);
        compare(ports["out.hdmi1"].product, "ACME VIEW 27");
        compare(ports["out.hdmi2"].available, false);
        compare(ports["out.speaker"].available, null);
        compare(ports["in.mic1"].jack, false);
        compare(ports["in.mic2"].jack, true);
        verify(!("in.unknown" in ports));
    }

    function test_noListingIsNoPorts() {
        compare(Object.keys(DeviceNames.audioPorts(null)).length, 0);
        compare(Object.keys(DeviceNames.audioPorts({})).length, 0);
    }

    function test_anHdmiOutputTakesTheNameOfItsMonitor() {
        const ports = DeviceNames.audioPorts(dump());
        const hdmi = node("out.hdmi1", "Laptop HD Audio HDMI / DisplayPort 1 Output (Stereo)");
        compare(DeviceNames.audioName(hdmi, ports["out.hdmi1"], tr), "ACME VIEW 27");
        verify(!DeviceNames.absent(hdmi, ports["out.hdmi1"]));
    }

    function test_anEmptyHdmiOutputIsNamedByNumberAndAbsent() {
        const ports = DeviceNames.audioPorts(dump());
        const hdmi = node("out.hdmi2", "Laptop HD Audio HDMI / DisplayPort 2 Output (Stereo)");
        compare(DeviceNames.audioName(hdmi, ports["out.hdmi2"], tr), "audio.names.hdmiNumber:2");
        verify(DeviceNames.absent(hdmi, ports["out.hdmi2"]));
    }

    // Without the port (no pactl, or not read yet) the node itself says it is HDMI: named by number, never absent.
    function test_anHdmiOutputWithoutItsPortIsNamedByNumberOnly() {
        const hdmi = node("out.hdmi3", "Laptop HD Audio HDMI / DisplayPort 3 Output (Stereo)", {
            "device.profile.description": "HDMI / DisplayPort 3 Output",
            "node.nick": "HDMI 3"
        });
        compare(DeviceNames.audioName(hdmi, undefined, tr), "audio.names.hdmiNumber:3");
        verify(!DeviceNames.absent(hdmi, undefined));
        const unknown = {
            type: "hdmi",
            available: null,
            product: "",
            description: "HDMI / DisplayPort"
        };
        compare(DeviceNames.audioName(node("x", "Digital Stereo (HDMI)"), unknown, tr), "audio.names.hdmi");
        verify(!DeviceNames.absent(node("x", "Digital Stereo (HDMI)"), unknown));
    }

    function test_theBuiltInDevicesHavePlainNames() {
        const ports = DeviceNames.audioPorts(dump());
        compare(DeviceNames.audioName(node("out.speaker", "Laptop HD Audio Speaker"), ports["out.speaker"], tr), "audio.names.speakers");
        compare(DeviceNames.audioName(node("in.mic1", "Laptop HD Audio Digital Microphone"), ports["in.mic1"], tr), "audio.names.microphone");
        compare(DeviceNames.audioName(node("in.mic2", "Laptop HD Audio Stereo Microphone"), ports["in.mic2"], tr), "audio.names.headsetMicrophone");
        compare(DeviceNames.audioName(node("h", "Headphones"), {
            type: "headphones",
            jack: true
        }, tr), "audio.names.headphones");
    }

    function test_otherDevicesKeepTheirDescription() {
        const usb = node("usb", "ACME USB Headset", {
            "device.bus": "usb"
        });
        compare(DeviceNames.audioName(usb, {
            type: "mic",
            jack: false
        }, tr), "ACME USB Headset");
        compare(DeviceNames.audioName(node("bt", "ACME Buds", {
            "device.bus": "bluetooth"
        }), undefined, tr), "ACME Buds");
        compare(DeviceNames.audioName(node("line", "Line In"), {
            type: "line"
        }, tr), "Line In");
        compare(DeviceNames.audioName(node("bare.node", ""), undefined, tr), "bare.node");
    }

    function test_theLaptopPanelIsTheBuiltInDisplay() {
        for (const name of ["eDP-1", "LVDS-1", "DSI-1"])
            compare(DeviceNames.displayName(name, "0x1234", tr), "displays.builtIn");
        verify(DeviceNames.isPanel("eDP-2"));
        verify(!DeviceNames.isPanel("DP-1"));
        verify(!DeviceNames.isPanel(undefined));
    }

    function test_anotherMonitorIsItsModelElseItsConnector() {
        compare(DeviceNames.displayName("DP-1", "ACME VIEW 27", tr), "ACME VIEW 27");
        compare(DeviceNames.displayName("HDMI-A-1", " ", tr), "HDMI-A-1");
        compare(DeviceNames.displayName("HDMI-A-1", undefined, tr), "HDMI-A-1");
        compare(DeviceNames.displayName("DP-2", "0x0ABC", tr), "DP-2");
    }

    function test_labelsThatReadTheSameAreToldApart() {
        const names = DeviceNames.distinct([
            {
                key: 1,
                label: "ACME VIEW 27",
                detail: "HDMI / DisplayPort 1"
            },
            {
                key: 2,
                label: "ACME VIEW 27",
                detail: "HDMI / DisplayPort 2"
            },
            {
                key: 3,
                label: "Speakers",
                detail: "Laptop Speaker"
            }
        ]);
        compare(names[1], "ACME VIEW 27 (HDMI / DisplayPort 1)");
        compare(names[2], "ACME VIEW 27 (HDMI / DisplayPort 2)");
        compare(names[3], "Speakers");
    }
}
