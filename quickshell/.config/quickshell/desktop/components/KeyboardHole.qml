import QtQuick
import Quickshell
import "../services"

// The input region of a full-screen layer without the on-screen keyboard rectangle: a touch on a key then
// always reaches the keyboard, whichever surface the compositor puts on top. Use it as the mask while
// Keyboard.areaVisible on the same screen (Overlay, the password prompts).
Region {
    required property Item content
    item: content
    Region {
        intersection: Intersection.Subtract
        x: Keyboard.area.x
        y: Keyboard.area.y
        width: Keyboard.area.width
        height: Keyboard.area.height
    }
}
