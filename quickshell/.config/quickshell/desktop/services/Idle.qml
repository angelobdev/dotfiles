pragma Singleton
import QtQuick
QtObject {
    // Inhibitors live on the mapped bars, so closing a panel does not release them.
    property bool keepAwake: false
}
