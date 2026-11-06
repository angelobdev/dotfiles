-- Every monitor at its preferred mode, placed automatically, unscaled. A machine profile (config/machines/)
-- declares the internal display of its model; ~/.config/desktop/hypr.lua can declare any monitor.
hl.monitor({
    output = "",
    mode = "preferred",
    position = "auto",
    scale = 1
})
