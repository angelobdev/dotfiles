-- Expose every mpv instance on D-Bus via the desktop MPRIS2 bridge (radio.py mpris)
-- so Quickshell MediaControl, top bar, lockscreen, and media keys detect terminal and panel playback.

local mp = require("mp")
local utils = require("mp.utils")

local home = os.getenv("HOME") or ""
local helper = home .. "/.local/libexec/desktop/radio.py"

local info = utils.file_info(helper)
if not info or not info.is_file then
    return
end

local pid = mp.get_property_native("pid") or utils.getpid()
local sock = mp.get_property("input-ipc-server")

if not sock or sock == "" then
    local runtime = os.getenv("XDG_RUNTIME_DIR")
    if not runtime or runtime == "" then
        runtime = "/tmp"
    end
    local dir = runtime .. "/desktop-shell"
    mp.command_native({
        name = "subprocess",
        args = { "mkdir", "-p", dir },
        playback_only = false,
        capture_stdout = true,
        capture_stderr = true,
    })
    sock = string.format("%s/mpv-%d.sock", dir, pid)
    mp.set_property("input-ipc-server", sock)
end

local bridge_token = mp.command_native_async({
    name = "subprocess",
    args = { "python3", helper, "mpris", sock, tostring(pid) },
    playback_only = false,
    capture_stdout = false,
    capture_stderr = false,
}, function() end)

mp.register_event("shutdown", function()
    if bridge_token then
        mp.abort_async_command(bridge_token)
    end
end)
