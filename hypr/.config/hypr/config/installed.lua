-- What the installer installed: its units (profiles, and parts as profile.part), one per line in
-- $XDG_STATE_HOME/dotfiles/units, which install-desktop.py writes with its record. What needs a unit is set up only
-- with it (the shell does the same, services/Installed.qml). Without that file (an install from before it, or none
-- by the installer), every unit counts as installed.
local state = require("config.util").state_home()

local units = nil
local file = io.open(state .. "/dotfiles/units", "r")
if file then
    units = {}
    for line in file:lines() do
        units[line] = true
    end
    file:close()
end

return function(unit)
    return units == nil or units[unit] == true
end
