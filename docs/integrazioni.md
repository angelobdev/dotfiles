# Sessione e integrazioni

[← README](../README.md)

## Blocco, inattività e sospensione

`Super + L` e il pannello power eseguono `desktop-power lock`, che avvia hyprlock con autenticazione obbligatoria (`--grace 0`) e serializza le richieste. PAM usa `/etc/pam.d/hyprlock` fornito dal pacchetto Fedora.

| Inattività | Azione                     |
| ---------- | -------------------------- |
| 5 minuti   | Blocco della sessione      |
| 10 minuti  | Spegnimento display (DPMS) |
| 30 minuti  | Sospensione                |

Personalizzare `hypridle/.config/hypr/hypridle.conf`. Il daemon rispetta gli inibitori delle applicazioni. Non servono pacchetti aggiuntivi per il toggle: `IdleInhibitor` è incluso in Quickshell e usa il protocollo supportato da Hyprland; hypridle rispetta gli inibitori Wayland per impostazione predefinita (`ignore_wayland_inhibit = false`). **Resta attivo** nel Control Center sospende blocco, DPMS e sospensione automatici tramite un inibitore Wayland sulle barre; continua a funzionare a pannello chiuso. Le azioni manuali restano disponibili. Il toggle parte disattivato e si azzera al riavvio della shell; il modulo configurabile si chiama `idle`. `inhibit_sleep = 3` fa attendere a logind il segnale Wayland di sessione bloccata prima del riposo, anche con il wrapper custom. `before_sleep_cmd` copre le richieste esterne e la chiusura del coperchio quando logind la associa alla sospensione. Al risveglio riaccende i display. `desktop-power suspend` rifiuta di procedere se hypridle non è attivo.

Hyprlock usa l’autenticazione impronta **nativa e parallela** tramite fprintd, conservando PAM/password. Non si modificano i file PAM di sistema. Il layout dispone orologio/data in alto e utente, password, stato impronta e tastiera in basso, con la palette grafite della shell. Sulla macchina il lettore Synaptics e l’indice destro risultano già registrati; per un altro utente usare `fprintd-list "$USER"` e, se necessario, `fprintd-enroll`. In assenza del lettore rimane la password.

Il config di hyprlock è stato provato in una sessione Hyprland annidata: inizializzazione PAM, rendering e conferma `onLockLocked` riusciti; il nuovo test headless conferma anche acquisizione del lettore e avvio della verifica dell’indice destro. La riuscita dell’autenticazione biometrica richiede la prova fisica del dito. Lo sblocco con la propria password, la chiusura del coperchio e il risveglio restano da verificare sulla macchina; il test annidato non prova questi percorsi hardware.

## XWayland

`hypr/.config/hypr/config/xwayland.lua` abilita esplicitamente il server XWayland installato da Fedora. `force_zero_scaling = false` conserva la scala del compositor su schermi HiDPI. Qt usa `wayland;xcb` e GTK `wayland,x11,*`, con `DISPLAY` importato nell’ambiente D-Bus/systemd al login. Le app native usano Wayland; le app X11 possono usare il bridge senza un desktop X separato.

La macchina è stata verificata con XWayland attivo e `xprop -root`. Per cambiare la politica di scala delle app X11, usare `hypr/.config/hypr/config/local.lua`; forzare la scala a zero può rendere molto piccole le app che non gestiscono HiDPI da sole.

## Electron, portali e condivisione schermo

Le applicazioni moderne scelgono Wayland usando `XDG_SESSION_TYPE=wayland`. La sessione imposta anche `XDG_CURRENT_DESKTOP=Hyprland` e importa le variabili del display in D-Bus/systemd. Per app Electron che richiedono una scelta esplicita:

```sh
desktop-electron code                  # --ozone-platform=wayland
desktop-electron --x11 code            # fallback XWayland
```

Chiudere prima le istanze dell’app: un processo già aperto può ricevere la richiesta di nuova finestra conservando il suo backend. Il wrapper non modifica i launcher delle app e non inserisce variabili Electron obsolete. VS Code è stato provato con profili temporanei su entrambi i backend; VS Code e Zen già aperti risultavano nativi Wayland. Le app Electron con Chromium personalizzato o vecchio possono avere limiti propri.

`portals/.config/xdg-desktop-portal/hyprland-portals.conf` sceglie Hyprland per ScreenCast, Screenshot, GlobalShortcuts e InputCapture, con GTK per FileChooser e Settings e come fallback. PipeWire trasporta il video. `desktop-session start` importa anche `~/.local/bin` nel PATH dei servizi e avvia i portali **dopo** l’importazione dell’ambiente; non li riavvia automaticamente durante condivisioni attive.

Alla richiesta di condivisione appare il selettore **Quickshell** (`share.qml`), con monitor, finestre, ricerca e navigazione da tastiera. Selezionare una sorgente e Condividi; Esc/Annulla nega la richiesta. Gli ID finestra arrivano dal portale, non dagli indirizzi Hyprland. `hypr/.config/hypr/xdph.conf` imposta `desktop-portal-picker`, 60 fps massimi e consenso non memorizzabile per impostazione predefinita. Il fallback GTK è un backend di sistema, senza applet persistenti.

Dopo l’installazione o modifiche al backend, chiudere le condivisioni, eseguire `desktop-session start` e poi `systemctl --user restart xdg-desktop-portal-hyprland xdg-desktop-portal-gtk xdg-desktop-portal`. Riavviare browser/app già aperti se necessario. Per diagnostica:

```sh
systemctl --user status xdg-desktop-portal-hyprland xdg-desktop-portal
journalctl --user -b -u xdg-desktop-portal-hyprland -u xdg-desktop-portal
```

Il test isolato ha completato CreateSession/SelectSources/Start e ricevuto cinque frame PipeWire reali da una finestra di prova tramite il selettore QML. La prova end-to-end nella specifica web app di chiamate in Zen rimane manuale: avviare una condivisione, verificare monitor/finestra e interromperla dall’app.
