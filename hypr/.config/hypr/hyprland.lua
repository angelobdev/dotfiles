-- Hyprland >= 0.55. Modules resolve from $XDG_CONFIG_HOME/hypr (fallback ~/.config/hypr), not $PWD.
local base = (os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")) .. "/hypr"
package.path = base .. "/?.lua;" .. base .. "/?/init.lua;" .. package.path

require("config.monitors")
-- What this model needs beyond the generic modules (config/machines/), by its DMI product name.
require("config.machines")
require("config.appearance")
require("config.input")
require("config.plugins")
require("config.binds")
require("config.rules")
require("config.console")
require("config.xwayland")
require("config.session")

-- The user's own settings, outside the repository: ~/.config/desktop/hypr.lua (see the configuration guide).
-- Through require, so Hyprland watches it and reloads on save as it does for these modules.
local user = (os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")) .. "/desktop/?.lua"
if package.searchpath("hypr", user) then
    local path = package.path
    package.path = user
    require("hypr")
    package.path = path
end

-- The internal display found by its name when no profile declared it, and the lid of a laptop.
require("config.displays").setup()
