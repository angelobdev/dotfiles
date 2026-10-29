-- The assistant console, after the Omarchy 4.5 Quake console: the special workspace "ai" (Super + A runs
-- Claude Code there through desktop-ai) drops down under the bar over a dimmed desktop. Its windows are
-- tiled by the "console" layout below in one box at the top of the usable area, 60% of the height and
-- twice as wide, side by side when there are several, and always above the docked on-screen keyboard.
-- It closes on a workspace change, on a click or tap outside (the shell's catcher layer, desktop-shell
-- console hide), and when an app opens while it is shown: the app goes to the normal workspace instead.

local share = 0.6
local gap = 8

-- The logical height of a monitor below the bar, whatever the docked keyboard reserves at the bottom.
local function screen_height(monitor)
    local height = monitor.height / monitor.scale
    if monitor.transform % 2 == 1 then
        height = monitor.width / monitor.scale
    end
    local reserved = type(monitor.reserved) == "table" and monitor.reserved or {}
    return height - (reserved.top or 0)
end

hl.layout.register("console", {
    recalculate = function(ctx)
        local count = #ctx.targets
        if count == 0 then
            return
        end
        local area = ctx.area
        local monitor = ctx.targets[1].window and ctx.targets[1].window.monitor
        local height = area.h
        if monitor then
            height = math.min(math.floor(screen_height(monitor) * share), area.h)
        end
        local width = count == 1 and math.min(height * 2, area.w * 0.92) or area.w * 0.96
        local x = area.x + (area.w - width) / 2
        local column = (width - gap * (count - 1)) / count
        for index, target in ipairs(ctx.targets) do
            target:place({ x = x + (index - 1) * (column + gap), y = area.y, w = column, h = height })
        end
    end
})

-- Layouts registered from Lua are named with the "lua:" prefix.
hl.workspace_rule({ workspace = "special:ai", layout = "lua:console", no_border = true })

hl.config({
    decoration = { dim_special = 0.45 },
    binds = { hide_special_on_workspace_change = true },
})

local function console_on(monitor)
    local special = monitor and monitor.active_special_workspace
    return special ~= nil and special.name == "special:ai"
end

-- Also run by `desktop-shell console hide` when the shell's catcher layer is clicked or tapped.
function desktop_console_hide(name)
    for _, monitor in ipairs(hl.get_monitors()) do
        if (name == nil or monitor.name == name) and console_on(monitor) then
            monitor:set_special_workspace({})
        end
    end
end

-- desktop-ai, when Claude was moved out of the console: back in, tiled again, and the console shown on
-- the focused monitor.
function desktop_console_show()
    for _, window in ipairs(hl.get_windows()) do
        if window.class == "desktop-ai" and window.workspace and window.workspace.name ~= "special:ai" then
            hl.dispatch(hl.dsp.window.move({ workspace = "special:ai", follow = false, window = window }))
            if window.floating then
                hl.dispatch(hl.dsp.window.float({ action = "unset", window = window }))
            end
        end
    end
    if not console_on(hl.get_active_monitor()) then
        hl.dispatch(hl.dsp.workspace.toggle_special("ai"))
    end
end

-- Super + Shift + A: the active window goes into the console without showing it, or back out of it to
-- the normal workspace of its monitor, which the console then uncovers.
function desktop_console_move()
    local window = hl.get_active_window()
    if not window or not window.workspace then
        return
    end
    local monitor = window.monitor
    if window.workspace.name == "special:ai" then
        local target = monitor and monitor.active_workspace
        if target then
            hl.dispatch(hl.dsp.window.move({ workspace = target.id, window = window }))
            desktop_console_hide(monitor.name)
        end
    else
        hl.dispatch(hl.dsp.window.move({ workspace = "special:ai", follow = false, window = window }))
    end
end

-- A window born in the open console (Super + Return, the launcher, the dock) belongs on the workspace
-- under it. Claude itself, and windows moved in on purpose, stay.
hl.on("window.open", function(window)
    if not window or window.class == "desktop-ai" or not window.workspace
        or window.workspace.name ~= "special:ai" then
        return
    end
    local monitor = window.monitor
    local target = monitor and monitor.active_workspace
    if target then
        hl.dispatch(hl.dsp.window.move({ workspace = target.id, window = window }))
        desktop_console_hide(monitor.name)
    end
end)
