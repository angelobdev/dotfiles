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
                edge_margin = 10,
            }
        }
    })
    touch.gesture({
        pattern = {
            kind = "swipe",
            fingers = 3,
            direction = "horizontal"
        },
        action = "workspace",
    })
    touch.bind({
        pattern = {
            kind = "edge",
            origin = "down",
            direction = "up"
        },
        action = hl.dsp.exec_cmd(shell .. " toggle launcher"),
    })
    touch.bind({
        pattern = {
            kind = "edge",
            origin = "up",
            direction = "down"
        },
        action = hl.dsp.exec_cmd(shell .. " toggle controls"),
    })
    -- The floating assist button, anywhere on the screen.
    touch.bind({
        pattern = {
            kind = "longpress",
            fingers = 3
        },
        action = hl.dsp.exec_cmd(shell .. " assist toggle"),
    })
    if plugins.overview then
        touch.bind({
            pattern = {
                kind = "swipe",
                fingers = 3,
                direction = "up"
            },
            action = function() plugins.overview.open() end,
        })
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
