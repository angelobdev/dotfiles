-- Render X11 surfaces at 1:1; HiDPI-aware clients (including desktop-steam) scale their UI.
hl.config({
    xwayland = {
        enabled = true,
        force_zero_scaling = true
    }
})
