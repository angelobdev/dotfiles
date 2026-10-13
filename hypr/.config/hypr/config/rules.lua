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

-- Chrome/Chromium, Firefox, and generic PiP windows share these titles.
-- Pinned floating windows stay above normal windows across workspaces.
hl.window_rule({
    name = "picture-in-picture",
    match = { title = "(?i)^(picture[- ]in[- ]picture|pip)$" },
    float = true,
    pin = true,
    move = { "monitor_w-window_w-20", "monitor_h-window_h-20" },
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
