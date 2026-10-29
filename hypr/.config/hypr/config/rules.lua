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

-- Floating windows keep their pixel size and place when the usable area of a monitor changes (rotation in
-- tablet mode, a new scale, the docked on-screen keyboard reserving the bottom): the assistant takes its
-- rule size again, limited to the usable area, and any other floating window that no longer fits there
-- moves in and shrinks to fit. Both stay inside the area left by the bar and the keyboard.
local function fit(window)
    local monitor = window.monitor
    if not (window.floating and window.mapped and monitor and window.fullscreen == 0) then
        return
    end
    local width, height = monitor.width / monitor.scale, monitor.height / monitor.scale
    if monitor.transform % 2 == 1 then
        width, height = height, width
    end
    local reserved = type(monitor.reserved) == "table" and monitor.reserved or {}
    local left, top = monitor.x + (reserved.left or 0), monitor.y + (reserved.top or 0)
    local usableWidth = width - (reserved.left or 0) - (reserved.right or 0)
    local usableHeight = height - (reserved.top or 0) - (reserved.bottom or 0)
    local at, x, y = window.at, window.size.x, window.size.y
    local assistantWindow = window.class == "desktop-ai"
    if assistantWindow then
        x, y = width * assistant.width, height * assistant.height
    elseif at.x >= left and at.y >= top and at.x + x <= left + usableWidth and at.y + y <= top + usableHeight then
        -- Still inside the usable area: left as it is, however large.
        return
    end
    x, y = math.floor(math.min(x, usableWidth * 0.95)), math.floor(math.min(y, usableHeight * 0.95))
    hl.dispatch(hl.dsp.window.resize({ x = x, y = y, window = window }))
    hl.dispatch(hl.dsp.window.move({
        x = math.floor(left + (usableWidth - x) / 2),
        y = math.floor(top + (usableHeight - y) / 2),
        window = window
    }))
end

-- Also called with `hyprctl eval` by the shell when the docked keyboard appears or goes.
function desktop_fit_floating()
    for _, window in ipairs(hl.get_windows()) do
        fit(window)
    end
end

hl.on("monitor.layout_changed", desktop_fit_floating)
hl.on("window.open", function(window)
    if window and window.class == "desktop-ai" then
        fit(window)
    end
end)

-- Transparent margins/backdrops stay clear; the glass surfaces receive blur.
hl.layer_rule({
    name = "desktop-glass",
    match = {
        -- The same surfaces Hyprglass glasses (plugins.lua), plus the bar.
        namespace = "^desktop-(bar|dock|overlay|notifications|osd|share-picker|osk|tray-menu|authentication|bluetooth-auth)$"
    },
    blur = true,
    ignore_alpha = 0.2,
})

-- The on-screen keyboard draws over the lock screen and takes touches there (2), so the password can be
-- typed in tablet mode; the shell shows it only while locked in that mode.
hl.layer_rule({
    name = "desktop-osk-lock",
    match = { namespace = "^desktop-osk$" },
    above_lock = 2,
})

-- The dock, panels, the OSD, notification toasts and the on-screen keyboard (re-mapped over panels) animate
-- themselves in Quickshell or not at all; a compositor fade on top would double the motion or flash.
hl.layer_rule({
    name = "desktop-shell-motion",
    match = {
        namespace = "^desktop-(dock|overlay|osd|notifications|osk)$"
    },
    no_anim = true,
})
