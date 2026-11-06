local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'

-- The keyboard layout the system has (localectl set-x11-keymap writes it for X11 and Wayland sessions alike), else
-- the console's keymap, else us. ~/.config/desktop/hypr.lua can set another one.
local function system_layout()
    local file = io.open("/etc/X11/xorg.conf.d/00-keyboard.conf")
    if file then
        local text = file:read("*a") or ""
        file:close()
        local layout = text:match('Option%s+"XkbLayout"%s+"([^"]+)"')
        if layout then
            return layout, text:match('Option%s+"XkbVariant"%s+"([^"]*)"') or ""
        end
    end
    file = io.open("/etc/vconsole.conf")
    if file then
        local text = file:read("*a") or ""
        file:close()
        -- Console keymaps add a suffix to the XKB name: de-latin1, fr-latin9.
        local keymap = text:match('KEYMAP="?([%w_]+)')
        if keymap then
            return keymap, ""
        end
    end
    return "us", ""
end

local layout, variant = system_layout()

hl.config({
    input = {
        kb_layout = layout,
        kb_variant = variant,
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
