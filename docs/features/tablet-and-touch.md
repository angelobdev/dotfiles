# Tablet and touch

[← Docs](../README.md)

The desktop is built for a 2-in-1: fold the laptop and the shell follows, with larger targets, rotation, gestures and an on-screen keyboard. Target hardware is the HP OmniBook Ultra Flip.

## Gestures

| Touchscreen gesture (Hyprgrass) | Action |
| --- | --- |
| Three fingers left / right | Next / previous workspace, as on the touchpad; it switches as soon as the swipe is recognised |
| Three fingers up | Applications |
| Three fingers down | Control Center |
| Three-finger long press | Assist button: show / hide |
| Four fingers left / right | Move the active window to the previous / next workspace (it follows) |
| Four fingers up | Hyprspace overview |
| Four fingers down | Notifications |
| Two-finger long press, then drag | Move the window (as `Super` and the mouse) |
| Long press on window border | Resize |

Three fingers do what they do on the touchpad (`input.lua`); there are no edge swipes, which were not always recognised. Apps that ignore touch altogether, Kitty among them, still respond to one finger: a drag scrolls and a tap clicks. Gestures stay away from the window under them: three or more fingers never reach an app, even when no gesture follows, and two fingers held still wait for the long press, so an app gets them once they move or lift, or after about half a second. A single finger reaches an app within 40 ms. Everything else is in the assist button. In tablet mode, Hints lists these gestures first (title "Gestures and shortcuts"), and the launcher, Session menu and Theming panel drop their keyboard-only hints. Sensitivity and actions are in `hypr/.config/hypr/config/plugins.lua`.

**Window menu:** Fullscreen, Floating, Move to the previous / next workspace and Close window for the active window. In tablet mode (and on a bar too narrow for the title) the icon of the active app sits after the workspaces and opens it with a tap; the Window action of the assist button and `desktop-shell window-menu` open it too. With a mouse, a right click or a long press on the title does the same.

## Tablet mode and rotation

Folding the OmniBook screen back into tablet posture turns tablet mode on; unfolding it turns it off. In tablet mode the built-in display follows the accelerometer in quarter turns, with touch and stylus input rotated along with it; back in laptop mode it returns upright. Lying flat keeps the last orientation.

**Larger for fingers:** in tablet mode the shell hit targets grow by a quarter (`Config.touchScale`): the bar (38 → 48 px), its buttons and workspace pills, buttons, switches, sliders, chips, menu and launcher rows, input fields and dock icons. Text keeps its size, and laptop mode keeps every design size.

**Long press** does what a right click does: the dock menu, the pin menu in the launcher, tray menus, and hiding a notification popup. A tap on a stacked deck of popups opens it, and it closes after 6 s without a touch. Dock icons do not magnify in tablet mode, and a finger that slides off an icon neither taps nor drags it. **Swipe** a notification sideways past a third of its width: a popup goes away (it stays in the center), an entry in the center is deleted; a shorter swipe springs back.

**Rotation lock** in the Control Center (shown only on machines with an accelerometer) keeps the current orientation; `desktop-shell rotation-lock toggle|on|off` sets it with an OSD. It is remembered across restarts and logins. `desktop-shell tablet on|off|toggle` sets the posture by hand, for instance to try it without folding the screen.

## Assist button

A round floating button on the built-in display, for reaching the shell by touch. It appears with tablet mode and goes away in laptop mode; a three-finger long press (or `desktop-shell assist show|hide|toggle`) shows or hides it at any time, until the posture changes again.
- **Drag** it with a finger or the mouse: it snaps to the nearer side edge, and the place is remembered for each monitor and orientation. After 3 seconds untouched it fades and slides halfway into the edge.
- **Tap** opens a menu of large buttons beside it, in three pages chosen at its top, so that what laptop mode reaches with shortcuts is a tap away:
  - **Apps:** Keyboard, AI assistant (as `Super + A`), Apps, Dock, Overview, Notifications, Control Center, Previous / Next workspace (one step along the bar's workspaces, empty ones included).
  - **Window** (the active window): Close, Fullscreen, Floating, Split direction, Move left / right, To previous / next workspace.
  - **System:** Screenshot of an area or of the display (HyprCapture editor), Record screen, Clipboard, Theming, Wallpaper, Next wallpaper, Shortcuts and gestures, Lock, Session, Rotation lock (only where there is an accelerometer).
  A tap outside closes it; `desktop-shell assist menu [apps|window|system]` opens it from scripts.
- **Long press** runs a quick action, the on-screen keyboard by default.
- It never takes keyboard focus, so the window underneath keeps typing.

`Config.qml` sets `assistPages` (pages and their actions, in order; the names are in `services/Assist.qml`) and `assistLongPress`. Positions live in `~/.local/state/desktop-shell/assist.json`.

## Sign-in

[Tablet mode sign-in](../guide/installation.md#tablet-mode-sign-in-without-the-fingerprint-reader) explains how to skip the fingerprint reader while the laptop is folded.

## Configuration

- **Touch scale:** `Theme.hit(n)` is `n × Theme.touchScale`, which is `Config.touchScale` (1.25) in tablet mode and 1 otherwise; `Theme.barHeight` is `hit(38)`. Components size their hit targets through it.
- **Posture:** `hypr/.config/hypr/config/tablet.lua` binds `switch:on/off` of the tablet mode switch to `desktop-shell tablet on|off`. The switch is named in `local.lua` (`require("config.tablet").switch("Intel HID switches")`, as `hyprctl devices` lists it). `services/Tablet.qml` keeps the posture in `$XDG_RUNTIME_DIR/desktop-shell/tablet.json`, so a shell restart keeps it and a new session starts in laptop mode until the switch reports. The switch binds are left out of Hints.
- **Sensor:** `libexec/desktop/rotation.py watch` claims the iio-sensor-proxy accelerometer over D-Bus only while tablet mode is on and rotation is unlocked, and prints its orientation as a Hyprland transform (normal 0, left-up 1, bottom-up 2, right-up 3; flat keeps the last one). `rotation.py probe` tells the shell whether there is an accelerometer.
- **Rotation:** `rotation.py apply N` writes `~/.local/state/desktop-session/rotation.lua` and runs `hyprctl eval 'desktop_rotate(N)'`. `monitors.lua` declares the built-in display through `require("config.tablet").monitor({...})`, which applies the saved transform, so a config reload (a theme change, for one) keeps the rotation. The touchscreen and stylus named in that call (`elan2513:00-04f3:4302` and its `-stylus`) get the same transform through `hl.device` and are mapped to that output, so an external touch monitor or drawing tablet is left alone; without names, `input.touchdevice` and `input.tablet` follow it instead.
