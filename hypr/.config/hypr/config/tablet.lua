-- Tablet posture. The shell decides when the internal display rotates (rotation.py apply), and touch and
-- stylus input rotate with it. The transform lives in a state file, so a config reload keeps it.

local M = {}

local state = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/desktop-session/rotation.lua"
local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local panel
-- Touch and stylus devices of the internal display; without them every touchscreen and tablet follows it.
local devices = {}
-- Clamshell: the internal display is off while the lid is closed and another monitor is on.
local lid = false
local panel_off = false

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
    -- Always said: a rule without it keeps the panel off once a clamshell turned it off.
    spec.disabled = panel_off
    hl.monitor(spec)
    if #devices > 0 then
        for _, name in ipairs(devices) do
            hl.device({ name = name, transform = transform, output = panel.output })
        end
    else
        hl.config({
            input = {
                touchdevice = { transform = transform, output = panel.output },
                tablet = { transform = transform, output = panel.output },
            }
        })
    end
end

-- Declares the internal display (in monitors.lua) instead of hl.monitor, with the saved rotation. touch lists
-- its touchscreen and stylus by their `hyprctl devices` names, so an external touch monitor or drawing tablet
-- is neither rotated nor mapped to the panel.
function M.monitor(spec, touch)
    panel = spec
    devices = touch or {}
    apply(saved())
end

local function lid_closed()
    -- A config reload forgets the switch events: the kernel still knows.
    for _, name in ipairs({ "LID", "LID0", "LID1" }) do
        local file = io.open("/proc/acpi/button/lid/" .. name .. "/state")
        if file then
            local text = file:read("*a") or ""
            file:close()
            return text:find("closed") ~= nil
        end
    end
    return lid
end

local function other_monitor()
    for _, monitor in ipairs(hl.get_monitors()) do
        -- FALLBACK is the virtual output Hyprland makes when no real one is on: it shows nothing.
        if monitor.name ~= panel.output and monitor.name ~= "FALLBACK" and monitor.enabled then
            return true
        end
    end
    return false
end

-- Off with the lid closed while another monitor shows the desktop; on again once the lid opens or the last
-- other monitor goes. Without another monitor logind suspends on the lid, as before.
local function clamshell()
    if not panel then
        return
    end
    local off = lid and other_monitor()
    if off ~= panel_off then
        panel_off = off
        apply(saved())
    end
end

-- The lid switch, by its name in `hyprctl devices` (local.lua). Bound locked: the lock screen moves too.
function M.lid(name)
    lid = lid_closed()
    hl.bind("switch:on:" .. name, function()
        lid = true
        clamshell()
    end, { locked = true })
    hl.bind("switch:off:" .. name, function()
        lid = false
        clamshell()
    end, { locked = true })
    for _, event in ipairs({ "monitor.added", "monitor.removed" }) do
        hl.on(event, clamshell)
    end
    clamshell()
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
