-- The internal display of a laptop and the monitors around it: display modes (Super + P, panels/DisplayPanel.qml),
-- the lid (clamshell), the refresh per power source (panels/BatteryPanel.qml) and the panel's rotation, which
-- config/tablet.lua drives. A desktop without an internal display gets none of it: every mode leaves its
-- monitors alone.

local M = {}

-- An empty XDG_STATE_HOME counts as unset, as in installed.lua and the installer.
local state_home = os.getenv("XDG_STATE_HOME")
if not state_home or state_home == "" then
    state_home = os.getenv("HOME") .. "/.local/state"
end
local folder = state_home .. "/desktop-session"
local state = folder .. "/rotation.lua"
-- The display mode chosen with Super + P, kept across reloads and logins.
local display_state = folder .. "/display.lua"
local MODES = { extend = true, mirror = true, external = true, internal = true }
-- The internal display's refresh, chosen in the battery panel for battery and for mains power: "vrr" (variable,
-- at the preferred mode) or a fixed mode such as "2880x1800@48.00". Without a choice it runs at its preferred
-- mode, VRR off.
local refresh_state = folder .. "/refresh.lua"
-- Kernel names of internal displays, for a machine that declares none (M.panel).
local INTERNAL = { "^eDP%-", "^LVDS%-", "^DSI%-" }
-- What monitors.lua sets every monitor to, also for the internal display when it is found by its name.
M.DEFAULT = { mode = "preferred", position = "auto", scale = 1 }

local panel
-- Declared by a machine profile (M.panel), or found by its name.
local declared = false
-- Monitors declared with M.monitor: what extend and mirror give back after a mode turned them off.
local specs = {}
-- Clamshell: the internal display is off while the lid is closed and another monitor is on.
local lid = false
local panel_off = false
-- The transform last applied, so a refresh change keeps the rotation in effect.
local current = 0
-- Called after each rule of the panel with its transform and output: tablet.lua rotates touch input with it.
local transform_hook
-- The panel's scale and position chosen in Settings (M.configure, from settings.lua), over its own rule. Its mode
-- stays with the refresh per power source.
local panel_settings = {}

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
                local supply = io.open("/sys/class/power_supply/" .. name .. "/online")
                if supply then
                    online = online or (supply:read("l") or "") == "1"
                    supply:close()
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
    for key, value in pairs(panel_settings) do
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
    if transform_hook then
        transform_hook(transform, panel.output)
    end
end

local function internal(name)
    for _, pattern in ipairs(INTERNAL) do
        if name:match(pattern) then
            return true
        end
    end
    return false
end

-- Without a declared panel, the first internal display Hyprland knows, at the defaults of monitors.lua. At the
-- first load there may be no monitor yet: monitor.added asks again.
local function find_panel()
    if panel then
        return true
    end
    for _, monitor in ipairs(hl.get_monitors({ all = true })) do
        if internal(monitor.name) then
            panel = { output = monitor.name }
            for key, value in pairs(M.DEFAULT) do
                panel[key] = value
            end
            apply(saved())
            return true
        end
    end
    return false
end

local function display_mode()
    local ok, value = pcall(dofile, display_state)
    if ok and type(value) == "table" and MODES[value.mode] then
        return value.mode
    end
    return "extend"
end

-- The kernel's lid state, "open" or "closed", or nil on a machine without a lid.
local function lid_state()
    for _, name in ipairs({ "LID", "LID0", "LID1" }) do
        local file = io.open("/proc/acpi/button/lid/" .. name .. "/state")
        if file then
            local text = file:read("*a") or ""
            file:close()
            return text:find("closed") and "closed" or "open"
        end
    end
end

local function lid_closed()
    -- A config reload forgets the switch events: the kernel still knows.
    local known = lid_state()
    if known then
        return known == "closed"
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

-- A monitor as extend and mirror give it back: its own rule (M.monitor), else the defaults.
local function restored(name, mirror)
    local spec = { output = name }
    for key, value in pairs(specs[name] or M.DEFAULT) do
        spec[key] = value
    end
    spec.output = name
    -- disabled and mirror are always said: a rule without them keeps the previous mode's.
    spec.disabled = false
    spec.mirror = mirror
    return spec
end

-- What each other monitor was last set to, so events caused by setting it do not set it again. A monitor seen
-- for the first time in extend mode is left to its rules (monitors.lua, ~/.config/desktop/hypr.lua).
local arranged = {}

-- The other monitors as the display mode wants them: beside the panel (extend), showing it (mirror), or off
-- (internal). The panel is off with the lid closed, or in external mode, while another monitor shows the
-- desktop; it comes back once the lid opens, the mode changes or the last other monitor goes. Without another
-- monitor logind suspends on the lid, as before, and every mode is the same.
function M.arrange()
    if not find_panel() then
        return
    end
    local mode = display_mode()
    local present = {}
    for _, monitor in ipairs(hl.get_monitors({ all = true })) do
        local name = monitor.name
        if name ~= panel.output and name ~= "FALLBACK" then
            present[name] = true
            local before = arranged[name] or "extend"
            if before ~= mode then
                if mode == "internal" then
                    hl.monitor({ output = name, disabled = true })
                elseif mode == "mirror" then
                    hl.monitor(restored(name, panel.output))
                else
                    hl.monitor(restored(name, ""))
                end
            end
            arranged[name] = mode
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

local watching = false

local function watch()
    if watching then
        return
    end
    watching = true
    for _, event in ipairs({ "monitor.added", "monitor.removed" }) do
        hl.on(event, function()
            M.arrange()
        end)
    end
end

-- Declares the internal display (a machine profile, instead of hl.monitor), with the saved rotation.
function M.panel(spec)
    panel = spec
    declared = true
    apply(saved())
    watch()
end

-- Declares another monitor (instead of hl.monitor), so extend and mirror give its own rule back.
function M.monitor(spec)
    specs[spec.output] = spec
    hl.monitor(spec)
end

-- A monitor as Settings sets it (settings.lua): on the internal display only scale and position, over its rule
-- (its mode is the refresh per power source); on another, a whole rule, through M.monitor, at the defaults
-- for what is not said.
function M.configure(name, fields)
    if type(name) ~= "string" or type(fields) ~= "table" then
        return
    end
    if internal(name) or (panel and panel.output == name) then
        panel_settings = { scale = fields.scale, position = fields.position }
        if find_panel() then
            apply(current)
        end
        return
    end
    local spec = { output = name }
    for key, value in pairs(M.DEFAULT) do
        spec[key] = value
    end
    for _, key in ipairs({ "mode", "position", "scale" }) do
        if fields[key] ~= nil then
            spec[key] = fields[key]
        end
    end
    M.monitor(spec)
end

-- The lid switch, by its name in `hyprctl devices`. Bound locked: the lock screen moves too.
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

-- For tablet.lua: rotates the panel, and calls hook(transform, output) after each rule of it.
function M.rotate(transform)
    if find_panel() then
        apply(transform)
    end
end

function M.on_transform(hook)
    transform_hook = hook
end

function M.has_panel()
    return find_panel()
end

-- Found by its name when no machine profile declares it; a laptop lid by the kernel's name for it.
function M.setup()
    if not declared then
        find_panel()
        watch()
    end
    if lid_state() then
        M.lid("Lid Switch")
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
    if find_panel() then
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
    if find_panel() and (refresh() or "") ~= applied_refresh then
        apply(current)
    end
end

return M
