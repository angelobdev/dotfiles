-- HP OmniBook Ultra Flip 14 (2-in-1, 2880x1800 OLED): the panel at 5/3, its ELAN touchscreen and stylus,
-- the tablet posture switch and the firmware's action keys.

local tablet = require("config.tablet")

-- The internal display rotates in tablet mode, with its own touchscreen and stylus.
tablet.monitor({
    output = "eDP-1",
    mode = "preferred",
    position = "auto",
    scale = "1.667"
}, { "elan2513:00-04f3:4302", "elan2513:00-04f3:4302-stylus" })

-- The 2-in-1 posture (SW_TABLET_MODE) comes on this switch.
tablet.switch("Intel HID switches")

local util = require("config.util")
local shell = util.shell
local bind = util.bind

-- Verified firmware actions: F1 (two screens) emits Super+P, the display picker; the three-diamond
-- programmable key (F11) emits XF86Launch2. Fn/Fn Lock chooses action mode.
bind("SUPER + P", hl.dsp.exec_cmd(shell .. " toggle displays"), "Displays")
bind("XF86Launch2", hl.dsp.exec_cmd(shell .. " toggle controls"), "Control Center")
