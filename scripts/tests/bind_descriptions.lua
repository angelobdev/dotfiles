-- Prints the description of every bind binds.lua and the machine profiles make, one per line, by loading them
-- with a stub of Hyprland's hl table in which every function accepts anything (test_binds.py reads them).
local function stub()
    return setmetatable({}, {
        __index = function(table, key)
            local value = stub()
            rawset(table, key, value)
            return value
        end,
        __call = function() return stub() end,
    })
end
hl = stub()
rawset(hl, "plugin", {})
rawset(hl, "get_monitors", function() return {} end)
rawset(hl, "bind", function(keys, dispatcher, flags)
    if type(flags) == "table" and type(flags.description) == "string" then
        print(flags.description)
    end
end)
local config = arg[1]
package.path = config .. "/?.lua;" .. package.path
require("config.binds")
-- Every profile, whatever this machine is.
local list = io.popen('ls "' .. config .. '/config/machines"')
for file in list:lines() do
    local name = file:match("^(.+)%.lua$")
    if name and name ~= "init" then
        require("config.machines." .. name)
    end
end
list:close()
