local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'

-- *** Utilities *** --

local function bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
end

local function screenshot(mode)
    return function()
        local capture = (hl.plugin or {}).hyprcapture
        if not capture then
            hl.exec_cmd('python3 "' .. os.getenv("HOME") .. '/.local/libexec/desktop/i18n.py" --notify "capture.title" "capture.errors.pluginMissing"')
            return
        end
        capture.open_editor(mode)
    end
end

-- *** BINDS *** --

-- Applications
bind("SUPER + Return", hl.dsp.exec_cmd("kitty"), "Terminal")
bind("XF86Calculator", hl.dsp.exec_cmd("gnome-calculator"), "Calculator")
bind("SUPER + A", hl.dsp.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-ai"'), "AI assistant")

-- System (Hyprland)
bind("SUPER + Q", hl.dsp.window.close(), "Close window")
bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }), "Toggle floating window")
bind("SUPER + CTRL + P", hl.dsp.window.pseudo(), "Toggle pseudotiling")
bind("SUPER + J", hl.dsp.layout("togglesplit"), "Toggle split orientation")
bind("SUPER + SHIFT + F", hl.dsp.window.fullscreen(), "Fullscreen")

bind("SUPER + SHIFT + S", screenshot("region"), "Screenshot · Area with editor")
bind("SUPER + SHIFT + ALT + S", screenshot("fullscreen"), "Screenshot · Display with editor")

bind("Print", screenshot("region"), "Screenshot · Area with editor")
bind("ALT + Print", screenshot("fullscreen"), "Screenshot · Display with editor")

-- System (Quickshell)
bind("SUPER + SHIFT + R", hl.dsp.exec_cmd(shell .. " restart"), "Restart Quickshell")
bind("SUPER + Space", hl.dsp.exec_cmd(shell .. " toggle launcher"), "Applications")
bind("SUPER + SHIFT + C", hl.dsp.exec_cmd(shell .. " toggle controls"), "Control Center")
bind("SUPER + SHIFT + N", hl.dsp.exec_cmd(shell .. " toggle notifications"), "Notifications")
bind("SUPER + SHIFT + E", hl.dsp.exec_cmd(shell .. " toggle network"), "Network & Wi-Fi")
bind("SUPER + SHIFT + V", hl.dsp.exec_cmd(shell .. " toggle audio"), "Sound & audio devices")
bind("SUPER + SHIFT + B", hl.dsp.exec_cmd(shell .. " toggle battery"), "Battery & power")
bind("SUPER + SHIFT + D", hl.dsp.exec_cmd(shell .. " toggle calendar"), "Calendar")
bind("SUPER + SHIFT + H", hl.dsp.exec_cmd(shell .. " toggle hints"), "Hints · Keyboard shortcuts")
bind("SUPER + SHIFT + W", hl.dsp.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-wallpaper"'), "Choose wallpaper")
bind("SUPER + CTRL + W", hl.dsp.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-wallpaper" --next'), "Next wallpaper")
bind("SUPER + CTRL + T", hl.dsp.exec_cmd(shell .. " toggle theming"), "Theming")
bind("SUPER + SHIFT + Q", hl.dsp.exec_cmd(shell .. " toggle power"), "Session menu")
bind("SUPER + D", hl.dsp.exec_cmd(shell .. " dock toggle"), "Dock")
for i = 1, 9 do
    bind("SUPER + ALT + " .. i, hl.dsp.exec_cmd(shell .. " dock launch " .. i), "Dock item " .. i)
end

-- System (Extensions)
bind("SUPER + CTRL + C", hl.dsp.exec_cmd(shell .. " toggle clipboard"), "Clipboard · History")
bind("SUPER + CTRL + R", hl.dsp.exec_cmd(shell .. " toggle recording"), "Screen recording")

-- Directional Binds
for _, direction in ipairs({ "left", "right", "up", "down" }) do
    bind("SUPER + " .. direction, hl.dsp.focus({ direction = direction }), "Focus " .. direction)
    bind("SUPER + SHIFT + " .. direction, hl.dsp.window.move({ direction = direction }), "Move " .. direction)
end

-- Workspaces
for i = 1, 10 do
    local key = i % 10
    bind("SUPER + " .. key, hl.dsp.focus({ workspace = i }), "Workspace " .. i)
    bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }), "Move to workspace " .. i)
end

-- Window Management (Cursor)
bind("SUPER + mouse:272", hl.dsp.window.drag(), "Drag window", { mouse = true })
bind("SUPER + mouse:273", hl.dsp.window.resize(), "Resize window", { mouse = true })

-- Keyboard Controls
-- Use the same selected MPRIS player as the Quickshell Control Center.
bind("XF86AudioPlay", hl.dsp.exec_cmd(shell .. " media play-pause"), "Play / pause", { locked = true })
bind("XF86AudioPause", hl.dsp.exec_cmd(shell .. " media pause"), "Pause", { locked = true })
bind("XF86AudioNext", hl.dsp.exec_cmd(shell .. " media next"), "Next", { locked = true })
bind("XF86AudioPrev", hl.dsp.exec_cmd(shell .. " media previous"), "Previous", { locked = true })
bind("XF86AudioStop", hl.dsp.exec_cmd(shell .. " media stop"), "Stop", { locked = true })
bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), "Volume up",
    { locked = true, repeating = true })
bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), "Volume down",
    { locked = true, repeating = true })
bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), "Mute", { locked = true })
bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), "Microphone", { locked = true })
bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), "Brightness up",
    { locked = true, repeating = true })
bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), "Brightness down",
    { locked = true, repeating = true })

-- Power Management
local power = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-power"'
bind("SUPER + L", hl.dsp.exec_cmd(power .. " lock"), "Lock screen")
bind("XF86Sleep", hl.dsp.exec_cmd(power .. " suspend"), "Suspend")
