-- Cursor. XCURSOR_SIZE stays unset: X11 clients draw in physical pixels under force_zero_scaling and read a
-- scaled size from the X resources set by desktop-xwayland; Wayland clients default to 24 logical pixels.
hl.env("HYPRCURSOR_SIZE", "24")

-- qt6ct also registers the qt5ct key, so one value serves both Qt generations.
hl.env("QT_QPA_PLATFORMTHEME", "qt5ct")
hl.env("QT_QUICK_CONTROLS_STYLE", "Basic")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")

hl.env("XDG_SESSION_TYPE", "wayland")
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")

-- GTK
hl.env("GDK_BACKEND", "wayland,x11,*")

-- SDL
hl.env("SDL_VIDEODRIVER", "wayland")

-- Clutter
hl.env("CLUTTER_BACKEND", "wayland")

-- X11 has one scale for every window: follow the focused monitor when outputs change.
for _, event in ipairs({ "monitor.added", "monitor.removed" }) do
    hl.on(event, function()
        hl.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-xwayland" apply')
    end)
end

-- Hyprland Start callback
hl.on("hyprland.start", function()
    hl.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-plugins" reload')
    hl.exec_cmd(
        "dbus-update-activation-environment --systemd WAYLAND_DISPLAY DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE HYPRLAND_INSTANCE_SIGNATURE QT_QPA_PLATFORMTHEME QT_QUICK_CONTROLS_STYLE QT_QPA_PLATFORM GDK_BACKEND")
    hl.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-session" start')
    hl.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell" start')
end)
