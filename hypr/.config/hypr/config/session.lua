hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")
-- Do not override XDG_CURRENT_DESKTOP: the session launcher owns that variable.
hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE")
    hl.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell" start')
end)
