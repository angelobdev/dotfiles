-- Overrides for this machine. Example:
-- hl.monitor({ output = "eDP-1", mode = "preferred", position = "auto", scale = 2 })

-- ENVIRONMENT --

-- The AI assistant (Super+A) dictates and replies in Italian; the UI locale stays en_US.
hl.env("DESKTOP_AI_LANGUAGE", "italian")

-- BINDS --

local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local function bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
end

bind("SUPER + B", hl.dsp.exec_cmd("zen-browser"), "Browser")
bind("SUPER + SHIFT + Space", hl.dsp.exec_cmd("1password --quick-access"), "1Password")

-- Verified Omnibook firmware actions: F1 emits Super+P; the three-diamond
-- programmable key (F11) emits XF86Launch2. Fn/Fn Lock chooses action mode.
bind("SUPER + P", hl.dsp.exec_cmd(shell .. " toggle controls"), "Control Center")
bind("XF86Launch2", hl.dsp.exec_cmd(shell .. " toggle controls"), "Control Center")
