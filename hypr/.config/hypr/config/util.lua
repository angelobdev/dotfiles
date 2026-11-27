-- What several modules need: the quoted path of a desktop wrapper, the bind every shortcut goes through (its
-- description is the Hints key, and the key test_binds.py checks in the catalogs), and the state folder.
local M = {}

-- A wrapper in ~/.local/bin, quoted for a command line.
function M.bin(name)
    return '"' .. os.getenv("HOME") .. "/.local/bin/" .. name .. '"'
end

M.shell = M.bin("desktop-shell")

-- What each described bind does, by its description: the commands of the launcher run a shortcut through
-- desktop_run_bind (services/Commands.qml). Kept by hl.bind itself, so the binds of ~/.config/desktop/hypr.lua
-- count too; the first bind of a description is kept (Print and Super + Shift + S do the same).
local actions = {}
-- Outside Hyprland (the installer's tests read state_home) there is no hl.
if hl and hl.bind then
    local hyprland_bind = hl.bind
    hl.bind = function(keys, dispatcher, flags)
        local description = type(flags) == "table" and flags.description or nil
        if description and actions[description] == nil and not flags.mouse then
            actions[description] = dispatcher
        end
        return hyprland_bind(keys, dispatcher, flags)
    end
end
function M.bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    return hl.bind(keys, dispatcher, flags)
end
function desktop_run_bind(description)
    local action = actions[description]
    if type(action) == "function" then
        action()
    elseif action ~= nil then
        hl.dispatch(action)
    end
end

-- $XDG_STATE_HOME, an empty value counted as unset, as the installer and the shell do.
function M.state_home()
    local state = os.getenv("XDG_STATE_HOME")
    if not state or state == "" then
        state = (os.getenv("HOME") or "") .. "/.local/state"
    end
    return state
end

return M
