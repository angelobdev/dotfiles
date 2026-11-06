-- config/console.lua with a stub of Hyprland's hl table: desktop_console_hide, which the shell runs through
-- `hyprctl eval` when the catcher layer is pressed and --verify-config never reaches. Hyprland 0.57 hides a
-- special workspace with set_special_workspace(nil) and refuses an empty table (#14).
local here = arg[0]:match("(.*/)") or "./"
local base = here .. "../../hypr/.config/hypr"
package.path = base .. "/?.lua;" .. base .. "/?/init.lua;" .. package.path

local calls = {}
local function monitor(name, special)
    return {
        name = name,
        active_special_workspace = special and { name = special } or nil,
        set_special_workspace = function(self, value)
            if value ~= nil and type(value) ~= "string" then
                error("HLMonitor.set_special_workspace: expected a workspace object or selector")
            end
            table.insert(calls, { name = self.name, value = value })
            self.active_special_workspace = nil
        end,
    }
end
local monitors = { monitor("eDP-1", "special:ai"), monitor("DP-1", "special:other"), monitor("HDMI-A-1", nil) }
hl = {
    layout = { register = function() end },
    workspace_rule = function() end,
    config = function() end,
    on = function() end,
    dispatch = function() end,
    get_monitors = function() return monitors end,
    get_windows = function() return {} end,
    get_active_monitor = function() return monitors[1] end,
    get_active_window = function() return nil end,
    dsp = { window = { move = function() end, float = function() end }, workspace = { toggle_special = function() end } },
}
require("config.console")

local checks = 0
local function check(condition, message)
    checks = checks + 1
    if not condition then
        error("console.lua: " .. message, 2)
    end
end

desktop_console_hide("DP-1")
check(#calls == 0, "a monitor showing another special workspace is left alone")
desktop_console_hide("eDP-1")
check(#calls == 1 and calls[1].name == "eDP-1" and calls[1].value == nil, "the console's monitor is cleared with nil")
monitors[1].active_special_workspace = { name = "special:ai" }
calls = {}
desktop_console_hide()
check(#calls == 1 and calls[1].name == "eDP-1", "without a name, every monitor showing the console")

print("console.lua: " .. checks .. " checks passed")
