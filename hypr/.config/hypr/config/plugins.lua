-- Loaded plugins expose these APIs after hyprpm reload; guards also allow recovery
-- and --verify-config without loading native code.
local plugins = hl.plugin or {}
local theme = require("config.theme")
local shell = '"' .. os.getenv("HOME") .. '/.local/bin/desktop-shell"'

if plugins.overview then
    hl.config({
        plugin = {
            overview = {
                disableGestures = true, -- Keep the existing touchpad gestures.
                panelHeight = 200,
                -- Do not reserve the overview strip or render shell bars in previews.
                affectStrut = false,
                hideTopLayers = true,
                hideOverlayLayers = true,
                hideRealLayers = true,
                showNewWorkspace = true,
                showSpecialWorkspace = false,
                exitOnSwitch = true,
            }
        }
    })
end

if plugins.hyprhotedge and plugins.overview then
    local trigger = "desktop-overview-trigger"
    hl.config({
        plugin = {
            hyprhotedge = {
                edge1 = {
                    enabled = 1,
                    side = "topleft",
                    trigger_width = 8,
                    dwell_time = 220,
                    special_workspace = trigger,
                    target_monitor = "*",
                    hide_on_leave = 0,
                }
            }
        }
    })

    -- Upstream hot-edge only opens special workspaces. Use an empty internal
    -- workspace as a signal, close it before toggling the overview, then rearm
    -- after leaving the corner (the upstream exact-corner trigger repeats).
    local pending = false
    local function rearm()
        local cursor, monitor = hl.get_cursor_pos(), hl.get_monitor_at_cursor()
        if cursor and monitor and cursor.x >= monitor.x and cursor.y >= monitor.y
            and cursor.x < monitor.x + 12 and cursor.y < monitor.y + 12 then
            hl.timer(rearm, { timeout = 100, type = "oneshot" })
        else
            plugins.hyprhotedge.enable()
            pending = false
        end
    end
    hl.on("workspace.special_active", function(workspace, monitor)
        if pending or not workspace or workspace.name ~= "special:" .. trigger then return end
        pending = true
        plugins.hyprhotedge.disable()
        local monitorName = monitor.name
        hl.timer(function()
            local current = hl.get_monitor(monitorName)
            if current then
                local special = current.active_special_workspace
                if special and special.name == "special:" .. trigger then
                    current:set_special_workspace({})
                    hl.dispatch(hl.dsp.focus({ monitor = monitorName }))
                    plugins.overview.toggle()
                end
            end
            rearm()
        end, { timeout = 1, type = "oneshot" })
    end)
    plugins.hyprhotedge.enable()
end

if plugins.hyprgrass then
    local touch = plugins.hyprgrass
    hl.config({
        plugin = {
            hyprgrass = {
                sensitivity = 4.0,
                long_press_delay = 400,
                resize_on_border_long_press = true,
            }
        }
    })
    -- No edge swipes: they are not always recognised. Three fingers do what they do on the touchpad
    -- (input.lua); four act on windows and the overview. Everything else is in the assist button.
    local function swipe(fingers, direction, action)
        touch.bind({
            pattern = {
                kind = "swipe",
                fingers = fingers,
                direction = direction
            },
            action = action,
        })
    end
    -- Workspaces switch as soon as the swipe is recognised (about 40 px), not along with the fingers: the
    -- live workspace gesture commits only past workspace_swipe_cancel_ratio of the screen width, half of it,
    -- while the app under the fingers scrolls. As on the touchpad, fingers left bring the next workspace.
    swipe(3, "left", hl.dsp.focus({ workspace = "r+1" }))
    swipe(3, "right", hl.dsp.focus({ workspace = "r-1" }))
    swipe(3, "up", hl.dsp.exec_cmd(shell .. " toggle launcher"))
    swipe(3, "down", hl.dsp.exec_cmd(shell .. " toggle controls"))
    touch.bind({
        pattern = {
            kind = "longpress",
            fingers = 3
        },
        action = hl.dsp.exec_cmd(shell .. " assist toggle"),
    })
    -- Two fingers held, then moved, drag the window under them like Super and the mouse (a two-finger
    -- scroll moves at once, so it never becomes a long press).
    touch.bind({
        pattern = {
            kind = "longpress",
            fingers = 2
        },
        action = hl.dsp.window.drag(),
        mouse = true,
    })
    -- The window follows to the workspace beside it, empty ones included.
    swipe(4, "left", hl.dsp.window.move({ workspace = "r-1" }))
    swipe(4, "right", hl.dsp.window.move({ workspace = "r+1" }))
    swipe(4, "down", hl.dsp.exec_cmd(shell .. " toggle notifications"))
    if plugins.overview then
        swipe(4, "up", function() plugins.overview.toggle() end)
    end
end

if plugins.hyprglass then
    local glass = plugins.hyprglass
    glass.config({ default_theme = "dark", default_preset = "desktop", layers = { enabled = true } })
    glass.preset("desktop", {
        inherits = "subtle",
        blur_strength = 1.5,
        blur_iterations = 3,
        refraction_strength = 0.15,
        chromatic_aberration = 0.0,
        lens_distortion = 0.0,
        fresnel_strength = 0.12,
        specular_strength = 0.15,
        tint_color = theme.glassTint,
    })
    -- The bar has no background: exclude it rather than glassing its glyphs.
    -- 0.2 excludes the almost transparent fullscreen overlay dismissal area.
    for _, namespace in ipairs({ "desktop-dock", "desktop-overlay", "desktop-notifications", "desktop-osd",
        "desktop-share-picker", "desktop-tray-menu" }) do
        glass.layer(namespace, { preset = "desktop", mask_threshold = 0.2 })
    end
end

if plugins.hyprcapture then
    hl.config({
        plugin = {
            hyprcapture = {
                default_mode = "region",
                fullscreen_scope = "current",
                overlay_scope = "focus",
                allow_quick = true,
                save = true,
                clipboard = true,
                notification_backend = "system",
                save_dir = "$XDG_PICTURES_DIR/Screenshots",
            }
        }
    })
end
