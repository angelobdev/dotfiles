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

-- The user's own settings, outside the repository, in ~/.config/desktop (see the configuration guide):
-- settings.lua, which Settings generates (keyboard layout, shortcuts, assistant language), then hypr.lua,
-- written by hand, so it wins. Through require, so Hyprland watches them and reloads on save as it does for
-- these modules.
local user = (os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")) .. "/desktop/?.lua"
for _, name in ipairs({ "settings", "hypr" }) do
    if package.searchpath(name, user) then
        -- The user's folder first, then these modules, which settings.lua uses (config.displays).
        local path = package.path
        package.path = user .. ";" .. path
        require(name)
        package.path = path
    end
end

-- The internal display found by its name when no profile declared it, and the lid of a laptop.
require("config.displays").setup()
