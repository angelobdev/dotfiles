-- Hyprland >= 0.55. Modules are resolved relative to this config, not $PWD.
local base = (os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")) .. "/hypr"
package.path = base .. "/?.lua;" .. base .. "/?/init.lua;" .. package.path

require("config.monitors")
require("config.appearance")
require("config.input")
require("config.binds")
require("config.rules")
require("config.xwayland")
require("config.session")

-- Machine-specific overrides belong here and remain versioned.
require("config.local")
