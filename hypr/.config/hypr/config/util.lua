-- What several modules need: the quoted path of a desktop wrapper, the bind every shortcut goes through (its
-- description is the Hints key, and the key test_binds.py checks in the catalogs), and the state folder.
local M = {}

-- A wrapper in ~/.local/bin, quoted for a command line.
function M.bin(name)
    return '"' .. os.getenv("HOME") .. "/.local/bin/" .. name .. '"'
end

M.shell = M.bin("desktop-shell")

function M.bind(keys, dispatcher, description, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
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
