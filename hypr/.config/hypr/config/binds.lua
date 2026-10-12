local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'
local function bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
end

-- Applications
bind("SUPER + Return", hl.dsp.exec_cmd("kitty"), "Terminale")

-- System (Hyprland)
bind("SUPER + Q", hl.dsp.window.close(), "Chiudi finestra")
bind("SUPER + V", hl.dsp.window.float({ action = "toggle" }), "Finestra flottante")
bind("SUPER + P", hl.dsp.window.pseudo(), "Pseudo tiling")
bind("SUPER + J", hl.dsp.layout("togglesplit"), "Cambia orientamento split")
bind("SUPER + SHIFT + F", hl.dsp.window.fullscreen(), "Schermo intero")
bind("SUPER + SHIFT + S", hl.dsp.exec_cmd("hyprshot -m region"), "Screenshot · Area")
bind("SHIFT + Print", hl.dsp.exec_cmd("hyprshot -m region"), "Screenshot · Area")
bind("Print", hl.dsp.exec_cmd("hyprshot -m output"), "Screenshot · Monitor")
bind("SUPER + Print", hl.dsp.exec_cmd("hyprshot -m window"), "Screenshot · Finestra")
bind("ALT + Print", hl.dsp.exec_cmd("hyprshot -m window -m active"), "Screenshot · Finestra attiva")

-- System (Quickshell)
bind("SUPER + SHIFT + R", hl.dsp.exec_cmd(shell .. " restart"), "Riavvia Quickshell")
bind("SUPER + Space", hl.dsp.exec_cmd(shell .. " toggle launcher"), "Applicazioni")
bind("SUPER + SHIFT + C", hl.dsp.exec_cmd(shell .. " toggle controls"), "Centro di controllo")
bind("SUPER + SHIFT + N", hl.dsp.exec_cmd(shell .. " toggle notifications"), "Notifiche")
bind("SUPER + SHIFT + E", hl.dsp.exec_cmd(shell .. " toggle network"), "Rete e Wi-Fi")
bind("SUPER + SHIFT + V", hl.dsp.exec_cmd(shell .. " toggle audio"), "Volume e dispositivi audio")
bind("SUPER + SHIFT + B", hl.dsp.exec_cmd(shell .. " toggle battery"), "Batteria ed energia")
bind("SUPER + SHIFT + D", hl.dsp.exec_cmd(shell .. " toggle calendar"), "Calendario")
bind("SUPER + SHIFT + H", hl.dsp.exec_cmd(shell .. " toggle hints"), "Hints · Scorciatoie tastiera")
bind("SUPER + SHIFT + W", hl.dsp.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-wallpaper"'), "Scegli sfondo")
bind("SUPER + SHIFT + Q", hl.dsp.exec_cmd(shell .. " toggle power"), "Menu sessione")

-- System (Extensions)
bind("SUPER + CTRL + C", hl.dsp.exec_cmd(shell .. " toggle clipboard"), "Clipboard · Storico")
bind("SUPER + CTRL + R", hl.dsp.exec_cmd(shell .. " toggle recording"), "Registrazione schermo")

-- Directional Binds
for _, direction in ipairs({ "left", "right", "up", "down" }) do
    bind("SUPER + " .. direction, hl.dsp.focus({ direction = direction }), "Focus " .. direction)
    bind("SUPER + SHIFT + " .. direction, hl.dsp.window.move({ direction = direction }), "Sposta " .. direction)
end

-- Workspaces
for i = 1, 10 do
    local key = i % 10
    bind("SUPER + " .. key, hl.dsp.focus({ workspace = i }), "Workspace " .. i)
    bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }), "Sposta al workspace " .. i)
end

-- Window Management (Cursor)
bind("SUPER + mouse:272", hl.dsp.window.drag(), "Trascina finestra", { mouse = true })
bind("SUPER + mouse:273", hl.dsp.window.resize(), "Ridimensiona finestra", { mouse = true })

-- Keyboard Controls
bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), "Volume +",
    { locked = true, repeating = true })
bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), "Volume -",
    { locked = true, repeating = true })
bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), "Muto", { locked = true })
bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), "Microfono", { locked = true })
bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), "Luminosità +",
    { locked = true, repeating = true })
bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), "Luminosità -",
    { locked = true, repeating = true })

-- Power Management
local power = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-power"'
bind("SUPER + L", hl.dsp.exec_cmd(power .. " lock"), "Blocca schermo")
bind("XF86Sleep", hl.dsp.exec_cmd(power .. " suspend"), "Sospendi")
