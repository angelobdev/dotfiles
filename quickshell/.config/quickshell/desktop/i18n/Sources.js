.pragma library

// Labels supplied by Hyprland/Quickshell APIs are mapped to stable catalog keys.
// Unrecognized custom labels are preserved by the caller.
var bindKeys = {
    "Terminale": "apps.terminal",
    "Browser": "apps.browser",
    "1Password": "apps.passwordManager",
    "Chiudi finestra": "bindings.closeWindow",
    "Finestra flottante": "bindings.toggleFloating",
    "Pseudo tiling": "bindings.togglePseudotiling",
    "Cambia orientamento split": "bindings.toggleSplit",
    "Schermo intero": "bindings.fullscreen",
    "Screenshot · Area con editor": "capture.regionWithEditor",
    "Screenshot · Monitor con editor": "capture.displayWithEditor",
    "Riavvia Quickshell": "bindings.restartShell",
    "Applicazioni": "launcher.title",
    "Centro di controllo": "controlCenter.title",
    "Notifiche": "notifications.title",
    "Rete e Wi-Fi": "network.title",
    "Volume e dispositivi audio": "audio.panelTooltip",
    "Batteria ed energia": "battery.title",
    "Calendario": "calendar.title",
    "Hints · Scorciatoie tastiera": "hints.title",
    "Scegli sfondo": "wallpaper.title",
    "Menu sessione": "session.menuTitle",
    "Clipboard · Storico": "clipboard.historyTitle",
    "Registrazione schermo": "recording.title",
    "Trascina finestra": "bindings.dragWindow",
    "Ridimensiona finestra": "bindings.resizeWindow",
    "Volume +": "bindings.volumeUp",
    "Volume -": "bindings.volumeDown",
    "Muto": "bindings.mute",
    "Microfono": "audio.microphone",
    "Luminosità +": "bindings.brightnessUp",
    "Luminosità -": "bindings.brightnessDown",
    "Blocca schermo": "session.lock",
    "Sospendi": "session.suspend"
};

var networkKeys = {
    "Connected": "network.status.connected",
    "Connecting": "network.status.connecting",
    "Connection intercepted by a captive portal": "network.connectivity.captivePortal",
    "Disconnected": "network.status.disconnected",
    "Disconnecting": "network.status.disconnecting",
    "Full internet connectivity": "network.connectivity.full",
    "Not connected to a network": "network.connectivity.none",
    "Partial internet connectivity": "network.connectivity.partial",
    "Secrets were required but not provided": "network.errors.noSecrets",
    "Unknown": "network.status.unknown",
    "Wi-Fi connection took too long to authenticate": "network.errors.authenticationTimeout",
    "Wi-Fi network could not be found": "network.errors.networkNotFound",
    "Wi-Fi supplicant disconnected": "network.errors.supplicantDisconnected",
    "Wi-Fi supplicant failed": "network.errors.supplicantFailed"
};
