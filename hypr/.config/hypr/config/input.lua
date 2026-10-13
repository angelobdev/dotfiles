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
