-- Tablet posture of a 2-in-1. The shell decides when the internal display rotates (rotation.py apply), and touch
-- and stylus input rotate with it. The display itself, its rotation kept in a state file across reloads, is
-- config/displays.lua's; a machine profile (config/machines/) names the panel, its touch devices and the switch.

local displays = require("config.displays")

local M = {}

local shell = require("config.util").shell
-- Touch and stylus devices of the internal display; without them every touchscreen and tablet follows it.
local devices = {}

displays.on_transform(function(transform, output)
    if #devices > 0 then
        for _, name in ipairs(devices) do
            hl.device({ name = name, transform = transform, output = output })
        end
    else
        hl.config({
            input = {
                touchdevice = { transform = transform, output = output },
                tablet = { transform = transform, output = output },
            }
        })
    end
end)

-- Declares the internal display (displays.panel) with its touchscreen and stylus by their `hyprctl devices`
-- names, so an external touch monitor or drawing tablet is neither rotated nor mapped to the panel.
function M.monitor(spec, touch)
    devices = touch or {}
    displays.panel(spec)
end

-- Kept for machine profiles written before config/displays.lua.
M.lid = displays.lid

-- The tablet mode switch, by its name in `hyprctl devices`. Bound locked, so a flip while the screen is locked
-- still counts.
function M.switch(name)
    hl.bind("switch:on:" .. name, hl.dsp.exec_cmd(shell .. " tablet on"), { locked = true })
    hl.bind("switch:off:" .. name, hl.dsp.exec_cmd(shell .. " tablet off"), { locked = true })
end

-- Entry point for `hyprctl eval` from rotation.py.
function desktop_rotate(transform)
    displays.rotate(transform)
end

return M
