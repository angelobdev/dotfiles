-- Cursor, from the theme and the Theming panel (config/theme.lua). XCURSOR_SIZE stays unset: X11 clients draw
-- in physical pixels under force_zero_scaling and read a scaled size from the X resources set by
-- desktop-xwayland. Clients that ask Hyprland for a cursor shape (GTK 4, Qt 6) get its cursor whatever these say.
local cursor = require("config.theme")
hl.env("HYPRCURSOR_THEME", cursor.cursorTheme)
hl.env("HYPRCURSOR_SIZE", tostring(cursor.cursorSize))
hl.env("XCURSOR_THEME", cursor.cursorTheme)

-- qt6ct also registers the qt5ct key, so one value serves both Qt generations.
hl.env("QT_QPA_PLATFORMTHEME", "qt5ct")
hl.env("QT_QUICK_CONTROLS_STYLE", "Basic")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")

-- The desktop commands, for the shell and everything it starts: desktop entries name them without a path,
-- since an entry cannot spell the home of whoever installs it. The check keeps reloads from repeating it.
local bin = os.getenv("HOME") .. "/.local/bin"
local path = os.getenv("PATH") or "/usr/local/bin:/usr/bin"
if not (":" .. path .. ":"):find(":" .. bin .. ":", 1, true) then
    hl.env("PATH", bin .. ":" .. path)
end

hl.env("XDG_SESSION_TYPE", "wayland")
hl.env("XDG_CURRENT_DESKTOP", "Hyprland")

-- GTK
hl.env("GDK_BACKEND", "wayland,x11,*")

-- SDL: X11 for builds without the Wayland driver (older bundled SDL2 in games).
hl.env("SDL_VIDEODRIVER", "wayland,x11")

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
    -- desktop-session exports the session environment to systemd and D-Bus activation, once.
    hl.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-session" start')
    -- Starts the shell, and starts it again if it crashes (desktop-shell stop keeps it off).
    hl.exec_cmd('"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell" supervise')
end)
