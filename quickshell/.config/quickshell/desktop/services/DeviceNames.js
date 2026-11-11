.pragma library

// Names a person would use for devices the system knows by identifiers. tr is I18n.tr (key, args), passed in so
// this stays testable; the raw identifiers stay for tooltips.

// The internal panel of a laptop, by the connector names config/displays.lua looks for.
function isPanel(name) {
    return /^(eDP|LVDS|DSI)-/.test(name ?? "");
}

// The internal panel is the built-in display; another monitor is its model, unless Hyprland only has a product code
// for it (0x41AA), then its connector.
function displayName(name, model, tr) {
    if (isPanel(name))
        return tr("displays.builtIn");
    const text = String(model ?? "").trim();
    return text !== "" && !/^0x[0-9a-f]+$/i.test(text) ? text : String(name ?? "");
}

// The active port of each sink and source, by node name, from `pactl -f json list` run in the C locale:
// { type, available (true, false or null when unknown), product (the monitor behind an HDMI port, from its
// ELD), jack (its presence is detected), description }. The port properties are only listed with the card.
function audioPorts(dump) {
    const cards = {};
    for (const card of dump?.cards ?? []) {
        let ports = card?.ports ?? {};
        if (Array.isArray(ports)) {
            const byName = {};
            for (const port of ports)
                byName[port?.name ?? ""] = port;
            ports = byName;
        }
        cards[card?.name ?? ""] = ports;
    }
    const result = {};
    for (const node of (dump?.sinks ?? []).concat(dump?.sources ?? [])) {
        const name = node?.active_port ?? "";
        const port = cards[node?.properties?.["device.name"] ?? ""]?.[name] ?? (node?.ports ?? []).find(entry => entry?.name === name);
        if (!node?.name || !port)
            continue;
        const properties = port.properties ?? {};
        result[node.name] = {
            type: String(properties["port.type"] ?? "").toLowerCase(),
            available: port.availability === "available" ? true : port.availability === "not available" ? false : null,
            product: String(properties["device.product.name"] ?? "").trim(),
            jack: (port.availability_group ?? properties["port.availability-group"] ?? "") !== "",
            description: String(port.description ?? "")
        };
    }
    return result;
}

// Whether a node is an HDMI or DisplayPort output: by its port when known, else by what PipeWire says of the node.
function isHdmi(node, port) {
    if (port?.type)
        return port.type === "hdmi";
    const properties = node?.properties ?? {};
    return /HDMI|DisplayPort/.test(properties["device.profile.description"] ?? "") || /^HDMI\b/.test(properties["node.nick"] ?? "");
}

// "HDMI / DisplayPort 2": the number the port, the profile or the ALSA name gives the output.
function hdmiName(node, port, tr) {
    const properties = node?.properties ?? {};
    for (const text of [port?.description, properties["device.profile.description"], properties["node.nick"], properties["alsa.name"]]) {
        const match = String(text ?? "").match(/(?:HDMI|DisplayPort)\D*?(\d+)/);
        if (match)
            return tr("audio.names.hdmiNumber", [match[1]]);
    }
    return tr("audio.names.hdmi");
}

// An HDMI or DisplayPort output whose port says nothing is plugged in.
function absent(node, port) {
    return isHdmi(node, port) && port?.available === false;
}

// The name of a sound device: the monitor behind an HDMI or DisplayPort output, else that output by number; the
// speakers, headphones and microphones of the computer itself; any other device (USB, Bluetooth, or a port this
// does not know) keeps the description PipeWire gives it.
function audioName(node, port, tr) {
    const properties = node?.properties ?? {};
    const description = node?.description || node?.name || "";
    if (isHdmi(node, port))
        return port?.available !== false && port?.product ? port.product : hdmiName(node, port, tr);
    if (/^(usb|bluetooth)$/.test(properties["device.bus"] ?? "") || !port)
        return description;
    if (port.type === "speaker")
        return tr("audio.names.speakers");
    if (port.type === "headphones")
        return tr("audio.names.headphones");
    if (port.type === "headset")
        return tr("audio.names.headsetMicrophone");
    if (port.type === "mic")
        return tr(port.jack ? "audio.names.headsetMicrophone" : "audio.names.microphone");
    return description;
}

// Labels that would read the same are told apart by a detail: [{ key, label, detail }] → { key: text }.
function distinct(entries) {
    const counts = {};
    for (const entry of entries)
        counts[entry.label] = (counts[entry.label] ?? 0) + 1;
    const result = {};
    for (const entry of entries)
        result[entry.key] = counts[entry.label] > 1 && entry.detail && entry.detail !== entry.label ? entry.label + " (" + entry.detail + ")" : entry.label;
    return result;
}
