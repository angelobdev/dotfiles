$font = {{ fonts.sans }}

general {
    hide_cursor = true
}
auth {
    pam:enabled = true
    pam:module = hyprlock
    fingerprint:enabled = true
    fingerprint:ready_message = {{ strings.lockFingerprintReady }}
    fingerprint:present_message = {{ strings.lockFingerprintPresent }}
    fingerprint:retry_delay = 250
}
background {
    monitor =
    path = screenshot
    blur_passes = 3
    blur_size = 8
    brightness = 0.55
    color = rgba({{ palette.bg | rgba }})
}
label {
    monitor =
    text = $TIME
    color = rgba({{ palette.fg | rgba }})
    font_size = 84
    font_family = $font
    position = 0, -90
    halign = center
    valign = top
}
label {
    monitor =
    text = cmd[update:60000] date +"%A, %d %B"
    color = rgba({{ palette.fg | rgba:dd }})
    font_size = 19
    font_family = $font
    position = 0, -215
    halign = center
    valign = top
}
label {
    monitor =
    text = $USER
    color = rgba({{ palette.fg | rgba }})
    font_size = 22
    font_family = $font
    position = 0, 258
    halign = center
    valign = bottom
}
input-field {
    monitor =
    size = 300, 52
    outline_thickness = 1
    rounding = {{ derived.lockRounding }}
    outer_color = rgba({{ shell.stroke | rgba }})
    inner_color = rgba({{ shell.tile | rgba }})
    font_color = rgba({{ palette.fg | rgba }})
    check_color = rgba({{ palette.accent | rgba }})
    fail_color = rgba({{ palette.danger | rgba }})
    font_family = $font
    placeholder_text = {{ strings.lockPassword }}
    fail_text = $PAMFAIL
    capslock_color = rgba({{ palette.warning | rgba }})
    fade_on_empty = false
    dots_spacing = 0.3
    position = 0, 180
    halign = center
    valign = bottom
}
label {
    monitor =
    text = $FPRINTPROMPT
    color = rgba({{ palette.muted | rgba }})
    font_size = 12
    font_family = $font
    position = 0, 138
    halign = center
    valign = bottom
}
label {
    monitor =
    text = $FPRINTFAIL
    color = rgba({{ palette.danger | rgba }})
    font_size = 12
    font_family = $font
    position = 0, 108
    halign = center
    valign = bottom
}
label {
    monitor =
    text = $LAYOUT
    color = rgba({{ palette.muted | rgba:cc }})
    font_size = 11
    font_family = $font
    position = 0, 65
    halign = center
    valign = bottom
}
