local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'

hl.config({
    input = {
        kb_layout = "it",
        follow_mouse = 1,
        sensitivity = 0,
        touchpad = {
            natural_scroll = true,
            tap_to_click = false,
            disable_while_typing = true,
            clickfinger_behavior = true,
            scroll_factor = 1
        },
    },
    misc = {
        middle_click_paste = false
    }
})

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace",
})

hl.gesture({
    fingers = 3,
    direction = "up",
    action = function()
        hl.exec_cmd(shell .. " toggle launcher")
    end
})

hl.gesture({
    fingers = 3,
    direction = "down",
    action = function()
        hl.exec_cmd(shell .. " toggle controls")
    end
})

-- Three fingers pinched zoom the screen around the pointer, a step at a time (the same steps and OSD as
-- Super + Alt + plus / minus). Hyprland names the directions the other way round from how they feel:
-- pinchin is the fingers moving apart.
hl.gesture({
    fingers = 3,
    direction = "pinchin",
    action = function()
        hl.exec_cmd(shell .. " zoom in")
    end
})

hl.gesture({
    fingers = 3,
    direction = "pinchout",
    action = function()
        hl.exec_cmd(shell .. " zoom out")
    end
})
