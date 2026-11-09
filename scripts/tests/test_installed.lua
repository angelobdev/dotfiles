-- config/installed.lua: the installer's units from $XDG_STATE_HOME/dotfiles/units, or every unit without that file.
local here = arg[0]:match("(.*/)") or "./"
local base = here .. "../../hypr/.config/hypr"
package.path = base .. "/?.lua;" .. package.path

local function fresh(state)
    package.loaded["config.installed"] = nil
    local getenv = os.getenv
    os.getenv = function(name)
        if name == "XDG_STATE_HOME" then
            return state
        end
        return getenv(name)
    end
    local installed = require("config.installed")
    os.getenv = getenv
    return installed
end

local folder = os.tmpname()
os.remove(folder)
assert(os.execute("mkdir -p '" .. folder .. "/dotfiles'"))

-- No file: an install from before it, so everything.
local installed = fresh(folder)
assert(installed("plugins.hyprcapture") and installed("anything"), "without the file every unit counts")

local file = assert(io.open(folder .. "/dotfiles/units", "w"))
file:write("core\nplugins\nplugins.hyprspace\n")
file:close()
installed = fresh(folder)
assert(installed("core") and installed("plugins.hyprspace"), "a listed unit is installed")
assert(not installed("plugins.hyprcapture"), "an unlisted unit is not")
assert(not installed("plugins.hyprs"), "only whole names count")

os.execute("rm -rf '" .. folder .. "'")
print("installed.lua: 5 checks passed")
