hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = 1
})

-- Custom monitor

-- The internal display rotates in tablet mode (config/tablet.lua), with its own touchscreen and stylus.
require("config.tablet").monitor({
    output = "eDP-1",
    mode = "preferred",
    position = "auto",
    scale = "1.667"
}, { "elan2513:00-04f3:4302", "elan2513:00-04f3:4302-stylus" })

hl.monitor({
    output = "DP-1",
    mode = "preferred",
    position = "auto",
    scale = 1,
})
