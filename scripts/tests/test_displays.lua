-- config/displays.lua and config/tablet.lua with a stub of Hyprland's hl table: the hyprctl eval entry points
-- (refresh per power source, display modes, rotation) that --verify-config never runs, because they only run
-- inside callbacks, and the machines without a profile: a laptop found by its panel's name, a desktop.
-- Run by check.sh with XDG_STATE_HOME set to an empty temporary directory.
local state = assert(os.getenv("XDG_STATE_HOME"), "XDG_STATE_HOME must name a temporary directory")
assert(os.execute('mkdir -p "' .. state .. '/desktop-session"'))

local popens = 0
local popen = io.popen
io.popen = function(...)
    popens = popens + 1
    return popen(...)
end

local here = arg[0]:match("(.*/)") or "./"
local base = here .. "../../hypr/.config/hypr"
package.path = base .. "/?.lua;" .. base .. "/?/init.lua;" .. package.path

local monitors, configs, outputs, devices
-- A fresh Hyprland: the modules loaded again, the given outputs, no rules yet, no saved display mode.
local function start(names)
    monitors, configs, devices, outputs = {}, {}, {}, {}
    for _, name in ipairs(names) do
        table.insert(outputs, { name = name, enabled = true })
    end
    hl = {
        config = function(values) table.insert(configs, values) end,
        monitor = function(spec) table.insert(monitors, spec) end,
        device = function(spec) table.insert(devices, spec) end,
        bind = function() end,
        on = function() end,
        get_monitors = function() return outputs end,
        dsp = { exec_cmd = function() end },
        plugin = {},
    }
    package.loaded["config.displays"] = nil
    package.loaded["config.tablet"] = nil
    os.remove(state .. "/desktop-session/display.lua")
    return require("config.tablet"), require("config.displays")
end

local M, displays = start({ "eDP-1", "DP-1" })

local checks = 0
local function check(condition, message)
    checks = checks + 1
    if not condition then
        error("displays.lua: " .. message, 2)
    end
end

local function last_rule(output)
    for index = #monitors, 1, -1 do
        if monitors[index].output == output then
            return monitors[index]
        end
    end
end

local function last_panel()
    return last_rule("eDP-1")
end

local function last_vrr()
    for index = #configs, 1, -1 do
        if configs[index].misc then
            return configs[index].misc.vrr
        end
    end
end

local function read(path)
    local file = io.open(path)
    if not file then
        return nil
    end
    local text = file:read("*a")
    file:close()
    return text
end

M.monitor({ output = "eDP-1", mode = "preferred", position = "0x0", scale = 1.6 }, { "touch", "pen" })
check(popens == 1, "the power source is read once at load")

-- Rotations read no files.
for transform = 0, 3 do
    desktop_rotate(transform)
end
check(popens == 1, "rotations run no popen")
check(last_panel().transform == 3, "the last rotation is applied")
check(devices[#devices].name == "pen" and devices[#devices].transform == 3 and devices[#devices].output == "eDP-1",
    "the panel's touch devices rotate with it")

-- A choice per power source; the shell says which source applies.
desktop_refresh("battery", "vrr")
desktop_refresh("ac", "2880x1800@120.00")
desktop_refresh_power("battery")
check(last_vrr() == 1 and last_panel().mode == "preferred", "battery: VRR at the preferred mode")
desktop_refresh_power("ac")
check(last_vrr() == 0 and last_panel().mode == "2880x1800@120.00", "mains: the fixed mode, VRR off")
check(last_panel().transform == 3, "a refresh change keeps the rotation")
check(popens == 1, "a told power source runs no popen")

-- Anything else is refused and the saved choices stay.
local saved = read(state .. "/desktop-session/refresh.lua")
desktop_refresh("ac", 'x" } os.execute("true") --')
desktop_refresh("solar", "vrr")
desktop_refresh("ac", "fast")
check(read(state .. "/desktop-session/refresh.lua") == saved, "invalid choices leave the saved ones")

-- "" goes back to the preferred mode for that source.
desktop_refresh("ac", "")
desktop_refresh_power("ac")
check(last_panel().mode == "preferred" and last_vrr() == 0, "an empty choice is the preferred mode")

-- The single choice saved before there was one per source counts for both.
local file = assert(io.open(state .. "/desktop-session/refresh.lua", "w"))
file:write('return { refresh = "vrr" }\n')
file:close()
desktop_refresh_power("battery")
check(last_vrr() == 1, "the old single choice applies on battery")
desktop_refresh_power("ac")
check(last_vrr() == 1, "and on mains")

-- Display modes: an unknown one changes nothing; mirror points the other monitor at the panel.
local count = #monitors
desktop_display_mode("bogus")
check(#monitors == count, "an unknown display mode is ignored")
desktop_display_mode("mirror")
local mirrored = false
for index = count + 1, #monitors do
    mirrored = mirrored or (monitors[index].output == "DP-1" and monitors[index].mirror == "eDP-1")
end
check(mirrored, "mirror shows the panel on the other monitor")
check(read(state .. "/desktop-session/display.lua") == 'return { mode = "mirror" }\n', "the mode is saved")

-- Back to extend: the other monitor gets its own rule again, as declared.
displays.monitor({ output = "DP-1", mode = "preferred", position = "auto", scale = 1.25 })
desktop_display_mode("extend")
check(last_rule("DP-1").scale == 1.25 and last_rule("DP-1").mirror == "", "extend gives a declared monitor its rule back")

-- A laptop with no profile: the panel is found by its name, at the defaults, and rotates.
M, displays = start({ "eDP-2", "HDMI-A-1" })
displays.setup()
check(last_rule("eDP-2") and last_rule("eDP-2").scale == 1 and last_rule("eDP-2").transform == 0,
    "an undeclared internal display is found by its name")
check(last_rule("HDMI-A-1") == nil, "a monitor seen in extend mode is left to its own rules")
desktop_rotate(1)
check(last_rule("eDP-2").transform == 1, "an undeclared panel rotates too")
desktop_display_mode("internal")
check(last_rule("HDMI-A-1").disabled == true, "internal turns the other monitor off")

-- A desktop: no internal display, so no mode, refresh or rotation touches its monitors.
M, displays = start({ "DP-1", "DP-2" })
displays.setup()
for _, mode in ipairs({ "internal", "external", "mirror", "extend" }) do
    desktop_display_mode(mode)
end
desktop_refresh("ac", "vrr")
desktop_refresh_power("battery")
desktop_rotate(2)
check(#monitors == 0, "a desktop's monitors are left alone")

print("displays.lua: " .. checks .. " checks passed")
