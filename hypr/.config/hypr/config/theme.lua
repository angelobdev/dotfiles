-- Colours of the current desktop theme, rendered by desktop-theme into
-- ~/.local/state/desktop-theme/hyprland.lua. The defaults are Graphite, so --verify-config
-- and a first login without that file look the same; a value of the wrong type is ignored.
local defaults = {
    shadow = 0x660d0e10,
    glassTint = 0x191a1d22,
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
