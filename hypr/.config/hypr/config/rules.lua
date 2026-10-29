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

-- desktop-ai launches Claude Code in Kitty; Super+A toggles this special workspace.
local assistant = { width = 0.6, height = 0.7 }
hl.window_rule({
    name = "desktop-ai",
    match = { class = "^desktop-ai$" },
    workspace = "special:ai",
    float = true,
    size = { "monitor_w*" .. assistant.width, "monitor_h*" .. assistant.height },
    center = true,
})

-- Floating windows keep their pixel size when a monitor changes shape (rotation in tablet mode, a new
-- scale): the assistant takes its rule size again, and any other floating window larger than its
-- monitor shrinks to 90% of it. Both are centred.
hl.on("monitor.layout_changed", function()
    for _, window in ipairs(hl.get_windows()) do
        local monitor = window.monitor
        if window.floating and window.mapped and monitor and window.fullscreen == 0 then
            local width, height = monitor.width / monitor.scale, monitor.height / monitor.scale
            if monitor.transform % 2 == 1 then
                width, height = height, width
            end
            local x, y
            if window.class == "desktop-ai" then
                x, y = width * assistant.width, height * assistant.height
            elseif window.size.x > width or window.size.y > height then
                x, y = math.min(window.size.x, width * 0.9), math.min(window.size.y, height * 0.9)
            end
            if x then
                hl.dispatch(hl.dsp.window.resize({ x = math.floor(x), y = math.floor(y), window = window }))
                hl.dispatch(hl.dsp.window.center({ window = window }))
            end
        end
    end
end)

-- Transparent margins/backdrops stay clear; the glass surfaces receive blur.
hl.layer_rule({
    name = "desktop-glass",
    match = {
        namespace = "^desktop-(bar|dock|overlay|notifications|osd|share-picker)$"
    },
    blur = true,
    ignore_alpha = 0.2,
})

-- The dock, panels, the OSD and notification toasts animate themselves in Quickshell; a compositor fade on top would double the motion.
hl.layer_rule({
    name = "desktop-shell-motion",
    match = {
        namespace = "^desktop-(dock|overlay|osd|notifications)$"
    },
    no_anim = true,
})
