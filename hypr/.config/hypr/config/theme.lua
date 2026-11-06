-- Colours of the current desktop theme, rendered by desktop-theme into
-- ~/.local/state/desktop-theme/hyprland.lua. The defaults are Graphite, so --verify-config
-- and a first login without that file look the same; a value of the wrong type is ignored.
local defaults = {
    shadow = 0x660d0e10,
    glassTint = 0x191a1d22,
    glassStyle = "desktop",
    -- Theming panel changes to the liquid glass of this theme (plugins.lua).
    glassTuning = {},
    activeBorder = "rgba(d4d6dcff)",
    inactiveBorder = "rgba(44474eff)",
    rounding = 16,
    borderSize = 0,
    gapsIn = 4,
    gapsOut = 4,
    mode = "dark",
    -- The cursor (session.lua); theme.py also sets it live with hyprctl setcursor.
    cursorTheme = "Adwaita",
    cursorSize = 24,
    -- Reduce effects in the Theming panel: no animations, blur, shadows or glass (appearance.lua, plugins.lua).
    reduceEffects = false,
}

local state = os.getenv("XDG_STATE_HOME") or (os.getenv("HOME") .. "/.local/state")
local ok, loaded = pcall(dofile, state .. "/desktop-theme/hyprland.lua")
if not ok or type(loaded) ~= "table" then
    loaded = {}
end

local theme = {}
for key, value in pairs(defaults) do
    theme[key] = type(loaded[key]) == type(value) and loaded[key] or value
end
return theme
