-- Tablet posture. The shell decides when the internal display rotates (rotation.py apply), and touch and
-- stylus input rotate with it. The transform lives in a state file, so a config reload keeps it.

local M = {}

local state = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/desktop-session/rotation.lua"
local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local panel

local function saved()
    local ok, value = pcall(dofile, state)
    if ok and type(value) == "table" and type(value.transform) == "number" and value.transform >= 0 and value.transform <= 3 then
        return math.floor(value.transform)
    end
    return 0
end

local function apply(transform)
    local spec = {}
    for key, value in pairs(panel) do
        spec[key] = value
    end
    spec.transform = transform
    hl.monitor(spec)
    hl.config({
        input = {
            touchdevice = { transform = transform, output = panel.output },
            tablet = { transform = transform, output = panel.output },
        }
    })
end

-- Declares the internal display (in monitors.lua) instead of hl.monitor, with the saved rotation.
function M.monitor(spec)
    panel = spec
    apply(saved())
end

-- The tablet mode switch, by its name in `hyprctl devices` (local.lua). Bound locked, so a flip while the
-- screen is locked still counts.
function M.switch(name)
    hl.bind("switch:on:" .. name, hl.dsp.exec_cmd(shell .. " tablet on"), { locked = true })
    hl.bind("switch:off:" .. name, hl.dsp.exec_cmd(shell .. " tablet off"), { locked = true })
end

-- Entry point for `hyprctl eval` from rotation.py.
function desktop_rotate(transform)
    if panel then
        apply(transform)
    end
end

return M
