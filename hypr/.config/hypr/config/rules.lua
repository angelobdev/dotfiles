hl.window_rule({
    name = "suppress-maximize",
    match = { class = ".*" },
    suppress_event = "maximize"
})

hl.window_rule({
    name = "xwayland-drag-fix",
    match = {
        class = "^$",
        title = "^$",
        xwayland = true,
        float = true,
        fullscreen = false,
        pin = false
    },
    no_focus = true,
})

-- Transparent margins/backdrops stay clear; the glass surfaces receive blur.
hl.layer_rule({
    name = "desktop-glass",
    match = {
        namespace = "^desktop-(bar|overlay|notifications|osd|share-picker)$"
    },
    blur = true,
    ignore_alpha = 0.2,
})
