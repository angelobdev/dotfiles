hl.config({
    general = {
        gaps_in = 4,
        gaps_out = 4,
        border_size = 0,
        layout = "dwindle",
        resize_on_border = true,
    },
    decoration = {
        rounding = 16,
        active_opacity = 1.0,
        inactive_opacity = 0.92,
        fullscreen_opacity = 1.0,
        shadow = {
            enabled = true,
            range = 12,
            render_power = 3,
            color = 0x660d0e10
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

hl.curve("desktop", {
    type = "bezier",
    points = { { 0.2, 0.8 }, { 0.2, 1.0 } }
})

hl.animation({
    leaf = "windows",
    enabled = true,
    speed = 4,
    bezier = "desktop",
    style = "slide"
})

hl.animation({
    leaf = "workspaces",
    enabled = true,
    speed = 4,
    bezier = "desktop",
    style = "slide"
})

hl.animation({
    leaf = "fade",
    enabled = true,
    speed = 3,
    bezier = "desktop"
})
