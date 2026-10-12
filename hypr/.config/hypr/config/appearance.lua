hl.config({
    general = {
        gaps_in = 5, gaps_out = 12, border_size = 2, layout = "dwindle",
        resize_on_border = true,
        col = { active_border = "rgba(89b4faff)", inactive_border = "rgba(313244ff)" },
    },
    decoration = {
        rounding = 12,
        shadow = { enabled = true, range = 12, render_power = 3, color = 0x6611111b },
        blur = { enabled = true, size = 6, passes = 2 },
    },
    dwindle = { preserve_split = true },
    animations = { enabled = true },
    misc = { disable_hyprland_logo = true, force_default_wallpaper = 0 },
})
hl.curve("desktop", { type = "bezier", points = { {0.2, 0.8}, {0.2, 1.0} } })
hl.animation({ leaf = "windows", enabled = true, speed = 4, bezier = "desktop", style = "slide" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 4, bezier = "desktop", style = "slide" })
hl.animation({ leaf = "fade", enabled = true, speed = 3, bezier = "desktop" })
