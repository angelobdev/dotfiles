-- Tablet posture. The shell decides when the internal display rotates (rotation.py apply), and touch and
-- stylus input rotate with it. The transform lives in a state file, so a config reload keeps it.

local M = {}

local state = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/desktop-session/rotation.lua"
-- The display mode chosen with Super + P (panels/DisplayPanel.qml), kept across reloads and logins.
local display_state = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/desktop-session/display.lua"
local MODES = { extend = true, mirror = true, external = true, internal = true }
-- The internal display's refresh, chosen in the battery panel for battery and for mains power: "vrr" (variable,
-- at the preferred mode) or a fixed mode such as "2880x1800@48.00". Without a choice it runs at its preferred
-- mode, VRR off.
local refresh_state = (os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")) .. "/desktop-session/refresh.lua"
local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local panel
-- Touch and stylus devices of the internal display; without them every touchscreen and tablet follows it.
local devices = {}
-- Clamshell: the internal display is off while the lid is closed and another monitor is on.
local lid = false
local panel_off = false
-- The transform last applied, so a refresh change keeps the rotation in effect.
local current = 0

local function saved()
    local ok, value = pcall(dofile, state)
    if ok and type(value) == "table" and type(value.transform) == "number" and value.transform >= 0 and value.transform <= 3 then
        return math.floor(value.transform)
    end
    return 0
end

local function valid_refresh(choice)
    return type(choice) == "string" and (choice == "vrr" or choice:match("^%d+x%d+@%d+%.?%d*$") ~= nil)
end

local function refresh_choices()
    local ok, value = pcall(dofile, refresh_state)
    local choices = {}
    if ok and type(value) == "table" then
        for _, source in ipairs({ "battery", "ac" }) do
            -- `refresh` is the single choice saved before there was one per power source.
            local choice = value[source] or value.refresh
            if valid_refresh(choice) then
                choices[source] = choice
            end
        end
    end
    return choices
end

-- On battery when a battery-powered machine has no mains supply online; anything else counts as mains.
local function scan_battery()
    local list = io.popen("ls /sys/class/power_supply 2>/dev/null")
    if not list then
        return false
    end
    local mains, online = false, false
    for name in list:lines() do
        local kind = io.open("/sys/class/power_supply/" .. name .. "/type")
        if kind then
            local text = kind:read("l") or ""
            kind:close()
            if text == "Mains" or text == "USB" then
                mains = true
                local state = io.open("/sys/class/power_supply/" .. name .. "/online")
                if state then
                    online = online or (state:read("l") or "") == "1"
                    state:close()
                end
            end
        end
    end
    list:close()
    return mains and not online
end

-- The power source, read once (a popen blocks the compositor) and then told by the shell on every change, so
-- rotations and monitor changes read no files.
local battery = nil

local function on_battery()
    if battery == nil then
        battery = scan_battery()
    end
    return battery
end

local function refresh()
    return refresh_choices()[on_battery() and "battery" or "ac"]
end
-- The choice last applied, so a power change that keeps it does not set the mode again.
local applied_refresh = false

local function apply(transform)
    local spec = {}
    for key, value in pairs(panel) do
        spec[key] = value
    end
    current = transform
    spec.transform = transform
    local choice = refresh()
    applied_refresh = choice or ""
    if choice and choice ~= "vrr" then
        spec.mode = choice
    end
    -- misc.vrr, not the monitor rule: Hyprland applies the option at once, a rule's vrr only now and then.
    hl.config({ misc = { vrr = choice == "vrr" and 1 or 0 } })
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
    for _, event in ipairs({ "monitor.added", "monitor.removed" }) do
        hl.on(event, function()
            M.arrange()
        end)
    end
end

local function display_mode()
    local ok, value = pcall(dofile, display_state)
    if ok and type(value) == "table" and MODES[value.mode] then
        return value.mode
    end
    return "extend"
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

-- What each other monitor was last set to, so events caused by setting it do not set it again.
local arranged = {}

-- The other monitors as the display mode wants them: beside the panel (extend), showing it (mirror), or off
-- (internal). The panel is off with the lid closed, or in external mode, while another monitor shows the
-- desktop; it comes back once the lid opens, the mode changes or the last other monitor goes. Without another
-- monitor logind suspends on the lid, as before, and every mode is the same.
function M.arrange()
    if not panel then
        return
    end
    local mode = display_mode()
    local present = {}
    for _, monitor in ipairs(hl.get_monitors({ all = true })) do
        local name = monitor.name
        if name ~= panel.output and name ~= "FALLBACK" then
            present[name] = true
            if arranged[name] ~= mode then
                arranged[name] = mode
                if mode == "internal" then
                    hl.monitor({ output = name, disabled = true })
                -- disabled and mirror are always said: a rule without them keeps the previous mode's.
                elseif mode == "mirror" then
                    hl.monitor({ output = name, mode = "preferred", position = "auto", scale = 1, disabled = false, mirror = panel.output })
                else
                    hl.monitor({ output = name, mode = "preferred", position = "auto", scale = 1, disabled = false, mirror = "" })
                end
            end
        end
    end
    for name in pairs(arranged) do
        if not present[name] then
            arranged[name] = nil
        end
    end
    local off = (lid or mode == "external") and other_monitor()
    if off ~= panel_off then
        panel_off = off
        apply(saved())
    end
end

-- Entry point for `hyprctl eval` from the display picker.
function desktop_display_mode(mode)
    if not MODES[mode] then
        return
    end
    local file = io.open(display_state, "w")
    if file then
        file:write('return { mode = "' .. mode .. '" }\n')
        file:close()
    end
    M.arrange()
end

-- Entry point for `hyprctl eval` from the battery panel: the power source ("battery" or "ac") and its choice,
-- "vrr", a fixed mode, or "" for the preferred mode.
function desktop_refresh(source, choice)
    if (source ~= "battery" and source ~= "ac") or (choice ~= "" and not valid_refresh(choice)) then
        return
    end
    local choices = refresh_choices()
    choices[source] = choice ~= "" and choice or nil
    local file = io.open(refresh_state, "w")
    if file then
        local fields = {}
        for _, key in ipairs({ "battery", "ac" }) do
            if choices[key] then
                table.insert(fields, key .. ' = "' .. choices[key] .. '"')
            end
        end
        file:write("return { " .. table.concat(fields, ", ") .. " }\n")
        file:close()
    end
    if panel then
        apply(current)
    end
end

-- Called by the shell when the power source changes ("battery" or "ac"; read again without one): the other
-- source's choice, if it differs.
function desktop_refresh_power(source)
    if source == "battery" or source == "ac" then
        battery = source == "battery"
    else
        battery = scan_battery()
    end
    if panel and (refresh() or "") ~= applied_refresh then
        apply(current)
    end
end

-- The lid switch, by its name in `hyprctl devices` (local.lua). Bound locked: the lock screen moves too.
function M.lid(name)
    lid = lid_closed()
    hl.bind("switch:on:" .. name, function()
        lid = true
        M.arrange()
    end, { locked = true })
    hl.bind("switch:off:" .. name, function()
        lid = false
        M.arrange()
    end, { locked = true })
    M.arrange()
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
