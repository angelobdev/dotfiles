-- The layout of each workspace: tiling (dwindle, Hyprland's default here), scrolling or floating, cycled with
-- Super + Ctrl + L or a click on the focused workspace pill of the bar (desktop_workspace_layout_cycle). Kept in
-- $XDG_STATE_HOME/desktop-session/workspace-layouts.json, so a reload or the next login puts it back; the bar reads
-- the same file. Floating floats what the workspace holds and what opens there; leaving it tiles again only the
-- windows it floated.
local util = require("config.util")

local M = {}
local MODES = { "dwindle", "scrolling", "floating" }
local path = util.state_home() .. "/desktop-session/workspace-layouts.json"
-- Workspace id (a string) -> its mode, only for those not on dwindle.
local modes = {}
-- Workspace id -> the rule that makes its mode.
local rules = {}
-- Window address -> true: floated by a floating workspace.
local floated = {}

local function read()
    local file = io.open(path, "r")
    if not file then
        return
    end
    local text = file:read("a") or ""
    file:close()
    for id, mode in text:gmatch('"(%d+)"%s*:%s*"(%a+)"') do
        if mode == "scrolling" or mode == "floating" then
            modes[id] = mode
        end
    end
end

local function write()
    local entries = {}
    for id, mode in pairs(modes) do
        entries[#entries + 1] = string.format('"%s": "%s"', id, mode)
    end
    table.sort(entries)
    os.execute('mkdir -p "' .. util.state_home() .. '/desktop-session"')
    local file = io.open(path .. ".tmp", "w")
    if not file then
        return
    end
    file:write("{" .. table.concat(entries, ", ") .. "}\n")
    file:close()
    os.rename(path .. ".tmp", path)
end

local function windows(id)
    return hl.get_workspace_windows(tonumber(id)) or {}
end

local function apply(id, mode)
    if rules[id] then
        rules[id]:set_enabled(false)
        rules[id] = nil
    end
    -- Out of floating: the windows it floated go back to their tiles.
    for _, window in ipairs(windows(id)) do
        if floated[window.address] and mode ~= "floating" then
            floated[window.address] = nil
            if window.floating then
                hl.dispatch(hl.dsp.window.float({ window = "address:" .. window.address, action = "toggle" }))
            end
        end
    end
    if mode == "scrolling" then
        rules[id] = hl.workspace_rule({ workspace = id, layout = "scrolling" })
    elseif mode == "floating" then
        rules[id] = hl.window_rule({ name = "desktop-floating-workspace-" .. id, match = { workspace = id }, float = true })
        for _, window in ipairs(windows(id)) do
            if not window.floating then
                floated[window.address] = true
                hl.dispatch(hl.dsp.window.float({ window = "address:" .. window.address, action = "toggle" }))
            end
        end
    end
end

-- The focused workspace's id as a string, nil for a named or special one: they have no number to keep a mode under.
local function focused()
    local workspace = hl.get_active_workspace()
    if not workspace or not workspace.id or workspace.id < 1 then
        return nil
    end
    return tostring(workspace.id)
end

function M.set(mode)
    local id = focused()
    local known = false
    for _, name in ipairs(MODES) do
        known = known or name == mode
    end
    if not id or not known then
        return
    end
    apply(id, mode)
    modes[id] = mode ~= "dwindle" and mode or nil
    write()
    hl.dispatch(hl.dsp.event("desktop-workspace-layout " .. id .. " " .. mode))
    hl.dispatch(hl.dsp.event("desktop-osd workspaceLayout " .. mode))
end

function M.cycle()
    local id = focused()
    if not id then
        return
    end
    local current = modes[id] or "dwindle"
    local next = MODES[1]
    for index, mode in ipairs(MODES) do
        if mode == current then
            next = MODES[index % #MODES + 1]
        end
    end
    M.set(next)
end

read()
for id, mode in pairs(modes) do
    apply(id, mode)
end

-- For the bar, through hyprctl eval.
function desktop_workspace_layout_cycle()
    M.cycle()
end

-- For the commands of the launcher: one layout by name.
function desktop_workspace_layout_set(mode)
    M.set(mode)
end

return M
