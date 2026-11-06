-- Overrides for this machine. Example:
-- hl.monitor({ output = "eDP-1", mode = "preferred", position = "auto", scale = 2 })

-- TABLET MODE --

-- The OmniBook Ultra Flip reports its 2-in-1 posture (SW_TABLET_MODE) on this switch.
require("config.tablet").switch("Intel HID switches")
-- With an external monitor on, closing the lid turns the internal display off instead of suspending.
require("config.tablet").lid("Lid Switch")

-- BINDS --

local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local function bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
end

-- Verified Omnibook firmware actions: F1 (two screens) emits Super+P, the display picker; the three-diamond
-- programmable key (F11) emits XF86Launch2. Fn/Fn Lock chooses action mode.
bind("SUPER + P", hl.dsp.exec_cmd(shell .. " toggle displays"), "Displays")
bind("XF86Launch2", hl.dsp.exec_cmd(shell .. " toggle controls"), "Control Center")
