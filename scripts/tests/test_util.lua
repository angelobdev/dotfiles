-- config/util.lua: desktop_run_bind runs what a described bind does (the Shortcuts of the launcher), for binds made
-- with util.bind and with hl.bind alike (the user's hypr.lua); mouse binds and undescribed ones are not kept.
local here = arg[0]:match("(.*/)") or "./"
local base = here .. "../../hypr/.config/hypr"
package.path = base .. "/?.lua;" .. package.path

local ran = {}
local bound = 0
hl = {
    bind = function()
        bound = bound + 1
        return {}
    end,
    dispatch = function(action)
        ran[#ran + 1] = action
    end,
}
local util = require("config.util")

local called = 0
util.bind("SUPER + O", function()
    called = called + 1
end, "Pop window out")
util.bind("SUPER + Q", "close-dispatcher", "Close window")
util.bind("Print", "first", "Screenshot")
util.bind("SUPER + SHIFT + S", "second", "Screenshot")
hl.bind("SUPER + N", "notes", { description = "Notes" })
util.bind("SUPER + mouse:272", "drag", "Drag window", { mouse = true })
hl.bind("SUPER + X", "plain")

assert(bound == 7, "every bind still reaches Hyprland")
desktop_run_bind("Pop window out")
assert(called == 1, "a function bind is called")
desktop_run_bind("Close window")
desktop_run_bind("Screenshot")
desktop_run_bind("Notes")
assert(ran[1] == "close-dispatcher" and ran[2] == "first" and ran[3] == "notes", "a dispatcher is dispatched, the first of a description")
desktop_run_bind("Drag window")
desktop_run_bind("Nothing like this")
assert(#ran == 3, "mouse binds and unknown descriptions do nothing")
print("util.lua: 5 checks passed")
