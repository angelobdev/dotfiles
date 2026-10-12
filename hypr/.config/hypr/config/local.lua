-- Overrides for this machine. Example:
-- hl.monitor({ output = "eDP-1", mode = "preferred", position = "auto", scale = 2 })

-- BINDS --

local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local function bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
end

bind("SUPER + B", hl.dsp.exec_cmd("zen-browser"), "Browser")
bind("SUPER + SHIFT + Space", hl.dsp.exec_cmd("1password --quick-access"), "1Password")
