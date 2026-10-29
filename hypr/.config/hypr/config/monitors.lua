hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = 1
})

-- Custom monitor

-- The internal display rotates in tablet mode (config/tablet.lua).
require("config.tablet").monitor({
    output = "eDP-1",
    mode = "preferred",
    position = "auto",
    scale = "1.667"
})

hl.monitor({
    output = "DP-1",
    mode = "preferred",
    position = "auto",
    scale = 1,
})
