local theme = require("config.theme")

hl.config({
    general = {
        gaps_in = 4,
        gaps_out = 4,
        border_size = theme.borderSize,
        col = {
            active_border = theme.activeBorder,
            inactive_border = theme.inactiveBorder,
        },
        layout = "dwindle",
        resize_on_border = true,
        allow_tearing = true,
    },
    decoration = {
        rounding = theme.rounding,
        active_opacity = 1.0,
        inactive_opacity = 0.92,
        fullscreen_opacity = 1.0,
        shadow = {
            enabled = true,
            range = 12,
            render_power = 3,
            color = theme.shadow
        },
        blur = {
            enabled = true,
            size = 8,
            passes = 3
        },
    },
    dwindle = {
        preserve_split = true
    },
    animations = {
        enabled = true
    },
    misc = {
        disable_hyprland_logo = true,
        force_default_wallpaper = 0
    },
})

-- Restrained motion: quick ease-out entrances, quicker accelerating exits, no overshoot.
-- "out" and "accel" match Theme.easeOut/easeIn in Quickshell, so the shell and the compositor move alike.
hl.curve("out", {
    type = "bezier",
    points = { { 0.16, 1.0 }, { 0.3, 1.0 } }
})

hl.curve("accel", {
    type = "bezier",
    points = { { 0.3, 0.0 }, { 0.8, 0.15 } }
})

hl.curve("inout", {
    type = "bezier",
    points = { { 0.65, 0.0 }, { 0.35, 1.0 } }
})

-- Critically damped (damping = 2 * sqrt(stiffness)): tiling reflow glides without bouncing.
hl.curve("move", {
    type = "spring",
    mass = 1,
    stiffness = 240,
    damping = 31
})

hl.animation({
    leaf = "windowsIn",
    enabled = true,
    speed = 2.2,
    bezier = "out",
    style = "popin 87%"
})

hl.animation({
    leaf = "windowsOut",
    enabled = true,
    speed = 1.5,
    bezier = "accel",
    style = "popin 92%"
})

hl.animation({
    leaf = "windowsMove",
    enabled = true,
    speed = 3,
    spring = "move"
})

hl.animation({
    leaf = "fadeIn",
    enabled = true,
    speed = 2.2,
    bezier = "out"
})

hl.animation({
    leaf = "fadeOut",
    enabled = true,
    speed = 1.5,
    bezier = "accel"
})

hl.animation({
    leaf = "fadeSwitch",
    enabled = true,
    speed = 2.5,
    bezier = "out"
})

hl.animation({
    leaf = "fadeShadow",
    enabled = true,
    speed = 2.5,
    bezier = "out"
})

hl.animation({
    leaf = "fadeDim",
    enabled = true,
    speed = 2.5,
    bezier = "inout"
})

hl.animation({
    leaf = "fadeLayersIn",
    enabled = true,
    speed = 1.8,
    bezier = "out"
})

hl.animation({
    leaf = "fadeLayersOut",
    enabled = true,
    speed = 1.4,
    bezier = "accel"
})

hl.animation({
    leaf = "fadePopups",
    enabled = true,
    speed = 1.5,
    bezier = "out"
})

hl.animation({
    leaf = "layersIn",
    enabled = true,
    speed = 1.8,
    bezier = "out",
    style = "fade"
})

hl.animation({
    leaf = "layersOut",
    enabled = true,
    speed = 1.4,
    bezier = "accel",
    style = "fade"
})

hl.animation({
    leaf = "border",
    enabled = true,
    speed = 2.5,
    bezier = "out"
})

hl.animation({
    leaf = "workspaces",
    enabled = true,
    speed = 3,
    bezier = "out",
    style = "slidefade 18%"
})

hl.animation({
    leaf = "specialWorkspace",
    enabled = true,
    speed = 3,
    bezier = "out",
    style = "slidefadevert 20%"
})

-- The assistant console (console.lua) drops down from the bar and goes back up.
hl.animation({
    leaf = "specialWorkspaceIn",
    enabled = true,
    speed = 3,
    bezier = "out",
    style = "slidefadevert -20%"
})

hl.animation({
    leaf = "specialWorkspaceOut",
    enabled = true,
    speed = 2.5,
    bezier = "out",
    style = "slidefadevert -20%"
})
