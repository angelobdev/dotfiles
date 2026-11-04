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

if plugins.overview then
    -- Called with `hyprctl eval` by the corner of a bar: the overview of that monitor.
    function desktop_overview(monitor)
        hl.dispatch(hl.dsp.focus({ monitor = monitor }))
        plugins.overview.toggle()
    end
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
    -- The glass brightness follows the theme: the dynamic theme can be light.
    -- The theme picks the look (glassStyle): "desktop" is restrained, "liquid" refracts like macOS glass.
    local style = theme.glassStyle == "liquid" and "liquid" or "desktop"
    -- On 0.57.1 the glass caches never notice a window changing behind them: an open panel, the assistant
    -- console or a translucent terminal showed a frozen copy of what was behind (verification log,
    -- 2026-11-03). Layers re-render every frame (force_live_resample) and windows re-sample every frame
    -- (no background_cache), at some GPU cost while glass is on screen.
    glass.config({
        default_theme = theme.mode == "light" and "light" or "dark",
        default_preset = style,
        layers = { enabled = true, force_live_resample = true },
        windows = { background_cache = false },
    })
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
    -- A thick pane: a narrow lens rim that bends and mirrors what is around it over a flat, lightly
    -- frosted center, a thin lit bevel and a touch of dispersion on the rim only.
    local liquid = {
        inherits = "subtle",
        blur_strength = 0.45,
        blur_iterations = 3,
        noise_strength = 0.0,
        refraction_strength = 1.8,
        chromatic_aberration = 0.5,
        lens_distortion = 0.0,
        edge_thickness_px = 40,
        edge_height = 60,
        fresnel_strength = 0.45,
        fresnel_reflection = 0.6,
        specular_strength = 0.6,
        bevel_strength = 0.5,
        bevel_size = 1.5,
        bevel_shadow = 0.25,
        saturation = 1.05,
        vibrancy = 0.3,
        tint_color = theme.glassTint,
        -- Light blur shows the lens; a darker or brighter backdrop keeps the text on top readable.
        dark = { brightness = 0.72, adaptive_dim = 0.55 },
        light = { brightness = 1.15, adaptive_boost = 0.5 },
    }
    -- The values changed in the Theming panel for this theme (theme.py keeps the same defaults).
    for option, value in pairs(theme.glassTuning) do
        if type(option) == "string" and type(value) == "number" then
            liquid[option] = value
        end
    end
    glass.preset("liquid", liquid)
    -- Shell surfaces draw their own 1 px stroke at the window radius. The bevel of contour glass rounds its
    -- corners by about 0.6 x the lens rim width instead (the contour is smoothed), which drew a second,
    -- differently rounded border inside them; there the bevel is off. Windows keep it: their glass follows
    -- decoration.rounding exactly.
    glass.preset("liquid-surface", { inherits = "liquid", bevel_strength = 0.0 })
    -- Every shell surface with a background, the same list as the desktop-glass blur rule (rules.lua). The bar
    -- has none: it is left out rather than glassing its glyphs. 0.2 excludes the almost transparent
    -- fullscreen overlay dismissal area.
    for _, namespace in ipairs({ "desktop-dock", "desktop-overlay", "desktop-notifications", "desktop-osd",
        "desktop-share-picker", "desktop-tray-menu", "desktop-osk", "desktop-authentication",
        "desktop-bluetooth-auth" }) do
        -- Liquid glass follows each shape a surface draws (every card and toast gets its own rim);
        -- the desktop look keeps the alpha mask.
        glass.layer(namespace, {
            preset = style == "liquid" and "liquid-surface" or "desktop",
            mask_threshold = 0.2,
            mask_mode = style == "liquid" and "contour" or "auto",
        })
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
