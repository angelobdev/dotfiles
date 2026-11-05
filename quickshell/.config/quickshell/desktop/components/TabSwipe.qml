import QtQuick

// A one-finger horizontal swipe over its parent, by touch only (a mouse still selects and drags as before):
// swiped(1) for the next tab (a swipe to the left), swiped(-1) for the previous one. It counts past a quarter
// of the parent's width, or for a quick flick of at least 30 px. Vertical lists still scroll and sliders keep
// the finger they hold; a button the swipe starts on does not fire.
DragHandler {
    id: root
    // Pixels per second that make a short swipe count.
    property real flick: 600
    property real speed: 0
    property real lastX: 0
    property double lastTime: 0
    signal swiped(int step)
    target: null
    acceptedDevices: PointerDevice.TouchScreen
    yAxis.enabled: false
    onTranslationChanged: {
        if (!active)
            return;
        const now = Date.now();
        if (now > lastTime)
            speed = (translation.x - lastX) * 1000 / (now - lastTime);
        lastX = translation.x;
        lastTime = now;
    }
    onActiveChanged: {
        if (active) {
            speed = 0;
            lastX = 0;
            lastTime = Date.now();
            return;
        }
        const distance = lastX;
        const far = Math.abs(distance) > (parent?.width ?? 0) / 4;
        const quick = Math.abs(distance) >= 30 && Math.abs(speed) > flick && Math.sign(speed) === Math.sign(distance);
        if (far || quick)
            swiped(distance < 0 ? 1 : -1);
    }
}
