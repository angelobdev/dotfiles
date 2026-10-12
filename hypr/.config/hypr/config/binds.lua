local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local function bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
end
bind("SUPER + Return", hl.dsp.exec_cmd("kitty"), "Terminale")
bind("SUPER + Q", hl.dsp.exec_cmd("kitty"), "Terminale")
bind("SUPER + C", hl.dsp.window.close(), "Chiudi finestra")
bind("SUPER + Space", hl.dsp.exec_cmd(shell .. " toggle launcher"), "Applicazioni")
bind("SUPER + R", hl.dsp.exec_cmd(shell .. " toggle launcher"), "Applicazioni")
bind("SUPER + A", hl.dsp.exec_cmd(shell .. " toggle controls"), "Centro di controllo")
bind("SUPER + N", hl.dsp.exec_cmd(shell .. " toggle notifications"), "Notifiche")
bind("SUPER + M", hl.dsp.exec_cmd(shell .. " toggle power"), "Menu sessione")
bind("SUPER + SHIFT + R", hl.dsp.exec_cmd(shell .. " restart"), "Riavvia Quickshell")
bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }), "Finestra flottante")
bind("SUPER + F", hl.dsp.window.fullscreen(), "Schermo intero")
bind("SUPER + P", hl.dsp.window.pseudo(), "Pseudo tiling")
bind("SUPER + J", hl.dsp.layout("togglesplit"), "Cambia orientamento split")
for _, direction in ipairs({"left", "right", "up", "down"}) do
    bind("SUPER + " .. direction, hl.dsp.focus({ direction = direction }), "Focus " .. direction)
    bind("SUPER + SHIFT + " .. direction, hl.dsp.window.move({ direction = direction }), "Sposta " .. direction)
end
for i = 1, 10 do
    local key = i % 10
    bind("SUPER + " .. key, hl.dsp.focus({ workspace = i }), "Workspace " .. i)
    bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }), "Sposta al workspace " .. i)
end
bind("SUPER + S", hl.dsp.workspace.toggle_special("scratchpad"), "Scratchpad")
bind("SUPER + SHIFT + S", hl.dsp.window.move({ workspace = "special:scratchpad" }), "Sposta nello scratchpad")
bind("SUPER + mouse:272", hl.dsp.window.drag(), "Trascina finestra", { mouse = true })
bind("SUPER + mouse:273", hl.dsp.window.resize(), "Ridimensiona finestra", { mouse = true })
bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), "Volume +", { locked = true, repeating = true })
bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), "Volume -", { locked = true, repeating = true })
bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), "Muto", { locked = true })
bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), "Microfono", { locked = true })
bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), "Luminosità +", { locked = true, repeating = true })
bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), "Luminosità -", { locked = true, repeating = true })
