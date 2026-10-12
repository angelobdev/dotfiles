# Hyprland + Quickshell

Desktop custom per Fedora 44: Hyprland Lua, interfaccia QML in Quickshell e pacchetti GNU Stow. Versioni locali: Hyprland 0.56.2, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6, hyprpaper 0.8.4.

## Pacchetti

| Stow         | Contenuto                                                                                          |
| ------------ | -------------------------------------------------------------------------------------------------- |
| `hypr`       | `~/.config/hypr/hyprland.lua` e moduli Lua                                                         |
| `quickshell` | Barra, launcher, controlli, notifiche, power e agente Polkit                                       |
| `shell`      | `~/.local/bin/desktop-{shell,session,power,theme,wallpaper,electron,portal-picker}` e helper Python per sfondi, luminosità, clipboard e registrazione |
| `hypridle`   | Timer e coordinamento lock/sospensione                                                             |
| `hyprlock`   | Blocco Wayland con PAM e impronta fprintd                                                              |
| `hyprpaper`  | Sfondo Fedora 44 notturno, su ogni monitor                                                         |
| `gtk`        | Palette, font, icone e preferenza scura GTK 3/4                                                    |
| `qt`         | Palette Fusion e icone per Qt 5/6 tramite qt5ct/qt6ct                                              |
| `kitty`      | Terminale grafite con sfondo traslucido e palette ANSI condivisa                                  |
| `portals`    | Preferenze XDG: Hyprland per cattura/condivisione, GTK per file e impostazioni                      |

## Installazione e aggiornamento

I COPR della macchina sono `nett00n/hyprland` ed `errornointernet/quickshell`.

```sh
sudo dnf install hyprland quickshell stow kitty brightnessctl wireplumber \
  NetworkManager bluez upower power-profiles-daemon \
  hypridle hyprlock hyprpaper qt5ct qt6ct papirus-icon-theme ripgrep \
  f44-backgrounds-base xorg-x11-server-Xwayland ImageMagick python3 hyprshot \
  xdg-desktop-portal xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
  wl-clipboard cliphist wf-recorder pulseaudio-utils fprintd fprintd-pam
cd ~/.dotfiles
./scripts/stow.py dry-run
./scripts/stow.py apply
./scripts/check.sh
hyprctl reload
~/.local/bin/desktop-session start
# Solo quando si installano/cambiano i portali, terminando prima le condivisioni:
systemctl --user restart xdg-desktop-portal-hyprland xdg-desktop-portal-gtk xdg-desktop-portal
~/.local/bin/desktop-shell restart
```

La repo è la fonte dei file; Stow crea symlink senza folding. `dry-run` non scrive e restituisce errore in presenza di conflitti. `apply` salva i file in conflitto in `~/.local/state/dotfiles/backups/<data>/`, simula l'operazione e applica i link. Rifiuta directory genitrici che siano symlink. Ripetere `apply` dopo aver aggiunto file. Non usare sudo con Stow.

I pacchetti usano i percorsi XDG standard sotto `$HOME`. I due `color_scheme_path` Qt contengono `/home/angelo`: aggiornarli quando si installa su un altro utente. Lo sfondo Fedora 44 è incluso in JPEG in `hyprpaper/.local/share/wallpapers`, convertito dal JPEG XL installato (questa build hyprpaper non lo decodifica). Proviene da `f44-backgrounds-base`; licenza originale CC BY-SA 4.0 e attribuzione nei file del pacchetto Fedora.

## Interfaccia

- Barra alta 38 px logici: Fedora/app menu → workspace occupati/attivo e almeno due pill per monitor → titolo → spazio → tray → batteria (percentuale + icona) → Hints → notifiche → Control Center → giorno/ora → sessione. Controlli da 30 px, icone di stato da 16 px centrate e logo da 18 px. Rete e volume vivono nel Control Center.
- Icone vettoriali e tooltip nativi posizionati sotto i pulsanti, fuori dalla superficie della barra. Le icone app originali restano colorate.
- Launcher con ricerca, titoli a sinistra, icone, frecce e Invio; le app da terminale si aprono in Kitty.
- Superfici traslucide, bordi leggeri e blur Hyprland; sfondo fornito da hyprpaper.
- Pannelli Rete, Bluetooth, Notifiche e Batteria allineati in alto a destra, con larghezza comune configurata in `Config.qml` e intestazioni con icone da 22 px. Le azioni Non disturbare/Elimina tutte sono a destra del titolo Notifiche. I profili energetici si selezionano nel pannello batteria; il blocco batteria nella barra mostra una foglia in Risparmio energetico e un fulmine in Prestazioni, senza icona aggiuntiva in Bilanciato. L’indicatore segue il profilo di sistema anche quando viene cambiato esternamente; il tooltip riporta sempre il profilo corrente.
- Pannelli separati: Rete e Wi-Fi con ricerca/selezione reti; Audio con volume, mute, ingresso/uscita predefiniti e livello microfono; Batteria con potenza in W, energia in Wh, autonomia/carica rimanente e profili energetici. Le reti Wi-Fi Personal hanno un prompt password; Enterprise richiede un profilo preconfigurato.
- Control Center compatto, in alto a destra: schede Rete/Bluetooth, luminosità del monitor primario con accordion per gli altri display, volume dello speaker selezionato con accordion per ingressi/uscite e livello microfono, toggle Non disturbare e Resta attivo. Moduli e ordine si configurano in `Config.qml`. Bluetooth ha un sottopannello con adattatori, connessione/disconnessione dei dispositivi già associati e batteria quando esposta da BlueZ. I profili energetici dipendono dall’hardware.
- Notifiche, popup, azioni, centro notifiche e non disturbare; storico in memoria, azzerato al riavvio della shell.
- Agente Polkit QML con l'identità predefinita proposta da Polkit.
- Power navigabile da tastiera: blocco immediato; sospensione, logout, riavvio e spegnimento con conferma. Gli errori del comando vengono mostrati nel pannello.
- Calendario mensile con settimana da lunedì, selezione giorno, oggi e navigazione fra mesi; non include ancora eventi/calendari esterni.
- Hints con ricerca e categorie (Applicazioni, Shell e pannelli, Finestre, Workspace, Mouse, Audio e luminosità, Sessione, Altro): legge `hyprctl -j binds` a ogni apertura e mostra scorciatoia + descrizione reali, inclusi submap e bind aggiunti in `local.lua`.
- Selettore sfondi QML con navigazione cartelle e anteprima; nessun dialog esterno.
- Clipboard Quickshell con ricerca e pausa; selettore screen sharing custom e pannello registrazione con indicatore nella barra.
- OSD Quickshell per volume, mute dello speaker, microfono e luminosità: icona, livello e dispositivo, in basso al centro, senza intercettare mouse o tastiera.

NetworkManager, BlueZ, PipeWire/WirePlumber, UPower, Polkit e power-profiles-daemon forniscono i servizi di sistema. I config avviano Quickshell, hypridle e hyprpaper. Nessun Waybar, nm-applet, Blueman, Sway o server notifiche separato.

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

## OSD volume e luminosità

Gli OSD si aggiornano quando cambia il livello di sistema, anche usando i tasti multimediali o comandi esterni. Volume e mute seguono PipeWire; anche il microfono ha un indicatore dedicato. La luminosità del backlight viene letta da sysfs ogni 150 ms da un singolo helper persistente, senza avviare comandi a ogni lettura. Per monitor DDC/CI configurati e disponibili il controllo usa le letture periodiche esistenti (circa 3 secondi, con tempi dipendenti dal monitor).

L’indicatore appare sul monitor della luminosità modificata oppure, per l’audio, sul monitor con il focus. Scompare dopo 1,7 secondi dall’ultimo aggiornamento. Non compare alla prima lettura dei dispositivi; nel Control Center è nascosto, e per l’audio anche nel pannello Audio, dove il livello è già visibile. Non disturbare silenzia le notifiche e lascia disponibili gli OSD. Non servono nuovi pacchetti.

La configurazione è in `quickshell/.config/quickshell/desktop/Config.qml`:

```qml
readonly property bool osdEnabled: true
readonly property int osdTimeout: 1700
readonly property int osdWidth: 320
readonly property int osdBottomMargin: 96
```

Dimensioni e margine sono in pixel logici; il timeout è in millisecondi. Disabilitare `osdEnabled` nasconde gli OSD e ferma il watcher del backlight, conservando i controlli dei pannelli. Sono mostrati i cambiamenti effettivi: premere ancora un tasto quando il valore è già al limite non genera un nuovo OSD.

## Tema delle applicazioni

Tema dark-glassy: superfici grafite traslucide in Quickshell, blur di Hyprland e testo sempre opaco. Le superfici shell usano gli stessi RGB della palette nativa (`#191a1d`, `#202226`, `#292b30`), con alpha separato. Gli elementi selezionati usano testo scuro opaco per conservare il contrasto. Kitty usa uno sfondo al 94%, font Adwaita Mono e colori ANSI coordinati; il testo rimane opaco. I bordi Hyprland restano disabilitati e le finestre inattive conservano l’opacità 0,92.

Palette grigio grafite, primary neutro `#d4d6dc`, testo chiaro, Adwaita Sans e icone Papirus-Dark. GTK, Qt e hyprlock condividono la palette; GSettings usa l’accent slate. GTK 3 usa Adwaita-dark e colori CSS; GTK 4/libadwaita riceve la preferenza scura anche via GSettings/portale e i colori nominati. Qt Widgets usa Fusion e palette custom in entrambe le generazioni. Il plugin qt6ct installato accetta anche la chiave `qt5ct`, quindi `QT_QPA_PLATFORMTHEME=qt5ct` copre Qt 5/6. Qt Quick Controls usa Basic; applicazioni con stile proprio possono ignorare queste preferenze.

`desktop-theme` applica GSettings e importa le variabili Qt in D-Bus/systemd; alla prima esecuzione salva i valori precedenti in `~/.local/state/dotfiles/interface-before-theme.ini`. Riavviare le applicazioni già aperte per adottare il tema; il prossimo login applica anche l'ambiente completo. Le app Flatpak dipendono dai runtime/temi esposti alla sandbox e potrebbero non seguire tutti gli override CSS.

La shell usa superfici traslucide scure con blur e bordi sottili neutri. Hyprland non disegna bordi delle finestre: opacità attiva/fullscreen 1, inattiva 0.92 e blur abilitato. Questi valori sono in `hypr/.config/hypr/config/appearance.lua`. Le finestre attive conservano piena leggibilità.

## Scorciatoie

| Tasti                                       | Azione                                     |
| ------------------------------------------- | ------------------------------------------ |
| `Super + B`                                 | Browser (`zen-browser`)                    |
| `Super + Shift + Spazio`                    | Accesso rapido 1Password (override locale) |
| `Super + Invio`                             | Kitty                                      |
| `Super + Q`                                 | Chiudi finestra                            |
| `Super + Spazio`                            | Applicazioni                               |
| `Super + Shift + C`                         | Centro di controllo                        |
| `Super + Shift + E`                         | Rete e Wi-Fi                               |
| `Super + Shift + V`                         | Volume e dispositivi audio                 |
| `Super + Shift + B`                         | Batteria ed energia                        |
| `Super + Shift + N`                         | Notifiche                                  |
| `Super + Shift + D`                         | Calendario                                 |
| `Super + Shift + H`                         | Hints / bind attivi                        |
| `Super + Shift + Q`                         | Menu sessione                              |
| `Super + Shift + W`                         | Scegli sfondo                              |
| `Super + Ctrl + V`                          | Clipboard / storico                        |
| `Super + Ctrl + R`                          | Registrazione schermo                      |
| `Super + L` / `XF86Sleep`                   | Blocca / sospendi con lock                 |
| `Super + Shift + R`                         | Riavvia Quickshell                         |
| `Super + V` / `Super + Shift + F`           | Floating / fullscreen                      |
| `Super + P` / `Super + J`                   | Pseudo tiling / orientamento split         |
| `Super + frecce` / `Super + Shift + frecce` | Focus / sposta finestra                    |
| `Super + 1…9,0` / `Super + Shift + 1…9,0`   | Workspace / sposta al workspace            |
| `Super + Shift + S` / `Shift + Stamp`       | Screenshot di un’area                      |
| `Stamp`                                     | Screenshot di un monitor a scelta          |
| `Super + Stamp`                             | Screenshot di una finestra a scelta        |
| `Alt + Stamp`                               | Screenshot della finestra attiva           |
| `Super + trascina sinistro/destro`          | Sposta / ridimensiona finestra             |
| Tasti multimediali                          | Volume, microfono, luminosità              |
| `Esc` / clic esterno                        | Chiudi pannello                            |

Nel menu sessione: **↑/↓ e Tab/Shift+Tab** spostano il focus; **Invio o Spazio** attivano il pulsante. Alla richiesta di conferma il focus passa ad **Annulla**: usare **←/→ o Tab** per scegliere Conferma. **Esc** annulla la conferma, poi chiude il pannello. All’apertura il primo pulsante riceve il focus.

Nel calendario: frecce per spostare il giorno, PgUp/PgDn per il mese e Home per oggi. Nel selettore sfondo: frecce per la lista, Invio per aprire cartella/selezionare immagine, Backspace per risalire; Tab raggiunge percorso, applicazione e ripristino.

## Workspace per monitor

La barra mostra workspace occupati/attivi e almeno due pill per ogni monitor. Gli slot vuoti sono segnaposto: il workspace viene creato solo al clic o alla navigazione con rotella. Gli ID sono assegnati globalmente senza riutilizzare workspace di altri monitor; i workspace speciali restano esclusi. Il clic porta prima il focus sul monitor della barra. La rotella sopra le pill passa al precedente/successivo, fermandosi agli estremi.

In `Config.qml`: `minimumWorkspaces: 2` (minimo 2, massimo 10) e `workspaceScroll: true`.

## Clipboard

`Super + Ctrl + V` apre lo storico Quickshell: ricerca, frecce/Invio per copiare, eliminazione singola, svuotamento con conferma e pausa della raccolta. Dopo la copia il pannello si chiude; incollare nell’app con la sua normale scorciatoia. Testo e immagini vengono conservati da cliphist, con due watcher `wl-paste` gestiti dalla shell. Il bridge XWayland di Hyprland sincronizza la selezione X11/Wayland: non viene avviato un secondo sincronizzatore. Hyprland può limitare la lettura X11 quando nessuna finestra X11 ha il focus.

`clipboardEnabled: true` e `clipboardMaxItems: 200` sono in `Config.qml`. La pausa si azzera al riavvio. Lo storico è persistente in `$XDG_CACHE_HOME/cliphist/db` (normalmente `~/.cache/cliphist/db`), con directory privata: **è salvato su disco, non cifrato**. Le selezioni marcate `sensitive` da un’app vengono ignorate da cliphist; questo richiede che l’app le contrassegni. Disabilitare la raccolta o usare la pausa per contenuti che non si desidera conservare. La primaria X11/selezione con il mouse non viene sincronizzata dallo storico.

## Registrazione schermo

`Super + Ctrl + R` apre il pannello Quickshell. Scegliere monitor oppure area, quindi audio Nessuno/Speaker/Microfono e Avvia. Per l’area, trascinare all’interno di un solo monitor; `Esc` annulla. Durante la registrazione la barra mostra icona e durata: un clic ferma e salva; anche il pannello offre **Ferma e salva**. La registrazione prosegue a pannello chiuso. Il wrapper inoltra SIGINT al registratore per finalizzare il file anche quando viene terminato dalla shell.

I video vengono salvati nella directory Video XDG, sottocartella `Recordings`, con nomi unici e permessi privati. Il formato è Matroska (`.mkv`), video VP9 e audio Opus quando abilitato. In `Config.qml`: `recordingFramerate: 30` (1–60) e `recordingCodec: "libvpx-vp9"`. Audio Speaker cattura il monitor dell’uscita predefinita all’avvio; Microfono usa l’ingresso predefinito. Cambiare i dispositivi prima di avviare. Terminare la registrazione prima di uscire dalla sessione.

## Screenshot

Hyprshot gestisce la cattura; `Stamp` corrisponde al keysym `Print`. Area, finestra e monitor vengono selezionati con il mouse; `Alt + Stamp` cattura direttamente la finestra attiva. `Esc` annulla la selezione. I bind dello scratchpad sono stati rimossi, liberando `Super + S` e risolvendo il conflitto su `Super + Shift + S`.

Le immagini PNG vengono salvate e copiate negli appunti. Hyprshot usa `HYPRSHOT_DIR`, se impostata, altrimenti la cartella immagini XDG e infine la home. Per scegliere una directory, aggiungere per esempio `hl.env("HYPRSHOT_DIR", os.getenv("HOME") .. "/Pictures/Screenshots")` in `hypr/.config/hypr/config/local.lua` e ricaricare Hyprland; Hyprshot crea la cartella alla prima cattura. La notifica di salvataggio viene gestita da Quickshell e segue Non disturbare.

Il pacchetto Fedora `hyprshot` installa le dipendenze di cattura e selezione (`grim`, `slurp`), copia (`wl-clipboard`), lettura dati (`jq`) e notifiche (`libnotify`). Il freeze opzionale non è abilitato da questi bind.

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

## Sfondi persistenti

```sh
~/.local/bin/desktop-wallpaper                     # apre il selettore QML
~/.local/bin/desktop-wallpaper /percorso/immagine.png
~/.local/bin/desktop-wallpaper --reset             # ripristina Fedora
```

Il selettore parte dalla home e permette di risalire, digitare una cartella e aprire la raccolta degli sfondi. Supporta PNG, JPEG, WebP, JXL, AVIF, BMP e TIFF. ImageMagick converte il file selezionato in un JPEG gestito, applica l’orientamento EXIF e preserva l’originale. L’anteprima dipende dai decoder Qt; un JXL privo di anteprima può comunque essere convertito e applicato.

La selezione vive in `~/.local/state/desktop-session/wallpaper/`: `selection.json` conserva il percorso originale e `current.jpg` punta alla copia convertita. Hyprpaper usa quel link nel config Stow e ritrova la scelta al login; la repo non viene riscritta a ogni cambio sfondo. `desktop-session start` inizializza il link allo sfondo Fedora soltanto quando manca. Una conversione o applicazione fallita conserva la selezione precedente. La copia locale resta utilizzabile anche se si sposta l’originale.

I dati di stato non sono inclusi in Git e seguono il layout XDG standard di questa repo. Lo script serializza richieste concorrenti, passa i percorsi come argomenti e normalizza il nome inviato a IPC, gestendo anche spazi, virgole e caratteri speciali.

## Dati dei pannelli

Audio usa i nodi PipeWire e cambia i dispositivi predefiniti tramite le API Quickshell; WirePlumber decide come instradare gli stream già aperti. UPower fornisce potenza della batteria in W, energia in Wh e tempi stimati: il valore non è il consumo totale alla presa e può variare nel tempo. Se una stima manca, il pannello lo indica senza inventare un’autonomia. Il calendario è locale e non accede ad account esterni. Non disturbare silenzia i popup e conserva le notifiche nel centro; lo stato si azzera al riavvio della shell.

## Configurazione del Control Center

Modificare `quickshell/.config/quickshell/desktop/Config.qml`. La configurazione è dichiarativa, senza editor nell’interfaccia:

```qml
readonly property var controlCenterModules: ["network", "bluetooth", "brightness", "audio", "doNotDisturb", "idle"]
readonly property int controlCenterWidth: 400
readonly property bool expandMonitors: false
readonly property bool expandAudioDevices: false
readonly property string primaryMonitor: "eDP-1"
readonly property var brightnessDevices: ({})
```

Rimuovere un nome disabilita il modulo; riordinare la lista cambia la disposizione. Nomi sconosciuti e duplicati vengono ignorati. Ogni modulo è un file distinto in `modules/controlcenter/`. Rete e Bluetooth occupano mezza riga, gli altri moduli una riga intera; il pannello scorre quando gli accordion superano lo spazio disponibile. Se il monitor primario è scollegato si usa il primo display connesso.

La luminosità è hardware: il singolo backlight di un pannello eDP/LVDS/DSI viene rilevato automaticamente e controllato con `brightnessctl`. I tasti luminosità conservano il controllo del backlight integrato. Per più backlight o monitor esterni associare esplicitamente il nome restituito da `hyprctl monitors` al dispositivo:

```qml
readonly property var brightnessDevices: ({
    "eDP-1": { "type": "backlight", "device": "intel_backlight" },
    "DP-1": { "type": "ddc", "bus": 6 }
})
```

Il bus `6` è un esempio: usare quello effettivo mostrato da `ddcutil detect`. Per DDC/CI installare facoltativamente `sudo dnf install ddcutil`, abilitare DDC/CI nel monitor e verificare i permessi `/dev/i2c-*` previsti dal pacchetto. La shell non esegue sudo. Un monitor senza backend o senza accesso hardware mostra uno slider disabilitato con il motivo. L’accordion elenca solo gli altri monitor connessi; hotplug e valori vengono aggiornati mentre il Control Center è aperto. Lo slider e la percentuale seguono subito il valore scelto; durante il trascinamento le scritture vengono inviate con un intervallo di circa 70 ms, accorpate e serializzate. Il dato hardware viene riconciliato al termine senza ripristinare letture precedenti. Il valore minimo è 1% per evitare lo spegnimento accidentale del backlight. Non viene usata un’opacità software per simulare la luminosità.

Audio e Bluetooth usano le API native Quickshell. Bluetooth gestisce i dispositivi già associati; il pairing con PIN/conferma richiede ancora un agente dedicato. Le sezioni Hints sono ricavate dai tasti/descrizioni dei bind reali: i bind personalizzati non riconosciuti restano in Altro e sono ricercabili.

## Personalizzazione e diagnostica

`hypr/.config/hypr/config/local.lua` contiene gli override della macchina. Palette QML in `Theme.qml`, icone in `assets/icons`, CSS GTK e colori Qt nei rispettivi pacchetti. Quickshell e Hyprland ricaricano i propri config; riavviare hypridle/hyprpaper dopo aver modificato i loro file. L'autostart avviene al login; `desktop-session start` e `desktop-shell start` evitano processi duplicati. `desktop-shell restart` attende la chiusura dell’istanza precedente prima di avviare la nuova.

```sh
~/.local/bin/desktop-shell status
~/.local/bin/desktop-session status
qs log -c desktop
hyprctl configerrors
hyprctl getoption xwayland:enabled
xprop -root _NET_SUPPORTING_WM_CHECK
readlink -f ~/.local/state/desktop-session/wallpaper/current.jpg
cat ~/.local/state/desktop-session/hypridle.log
./scripts/check.sh
```

Verifiche eseguite: OSD con servizi simulati (volume, mute speaker/microfono, aggiornamenti rapidi, timeout, disabilitazione, riconnessione audio, soppressione nei pannelli e monitor multipli), watcher backlight su sysfs simulato (baseline, cambiamenti, hotplug e valori non validi) e regressione del trascinamento luminosità con coda di scrittura; parser Lua e script, caricamento/layout QML, Control Center e accordion, posizionamento tooltip, helper luminosità con backend fittizi (routing, limiti e scala DDC), aggiornamenti durante il trascinamento senza ritorno al vecchio valore e gestione di errori hardware, creazione/rilascio dell’inibitore Wayland anche a pannello chiuso, scansione Wi-Fi nativa, lettura dispositivi audio e dati UPower, calendario bisestile/cambio anno, navigazione completa del power menu con comando fittizio e selezione sfondo persistente. Le prove sullo sfondo coprono nomi con spazi/virgole e conservazione della scelta precedente in caso di file non valido o errore IPC. Per Hyprshot sono stati verificati l’assenza di bind duplicati e i flussi di salvataggio/copia nei quattro modi con backend simulati; la selezione interattiva e la cattura reale restano da provare manualmente.

Verifiche della fase successiva: modello workspace su più monitor (minimo, ID unici, attivo/urgente ed esclusione speciali); storico isolato con copia byte-per-byte di testo Unicode e PNG, eliminazione e svuotamento; bridge X11/Wayland con ripristino della selezione originale; registrazioni reali di una finestra di prova con/senza audio speaker, Matroska finalizzato e lettura con ffprobe; VS Code/Electron X11 e Wayland con profili temporanei; portale ScreenCast e ricezione di frame PipeWire; nuovo layout Hyprlock con acquisizione del dispositivo fprintd in compositor headless. QML e pannelli verificati su dati fittizi. Restano le prove fisiche di sblocco e quelle nella web app di chiamate scelta dall’utente.

## Rimozione

Prima fermare la shell (`desktop-shell stop`) e i daemon (`pkill -x hypridle; pkill -x hyprpaper`), poi `./scripts/stow.py remove`. La rimozione stacca i link, preserva la repo e non ripristina automaticamente i backup. Copiare dal backup i file desiderati e ricaricare Hyprland. Le preferenze GSettings restano: per ripristinarle usare i valori nel file `interface-before-theme.ini` con `gsettings set org.gnome.desktop.interface CHIAVE VALORE`. Effettuare un nuovo login per cambiare l'ambiente Qt.

## Prossimi moduli

Pairing Bluetooth con PIN/conferma, MPRIS, eventi nel calendario, impostazioni persistenti, traduzioni, altre distribuzioni e suddivisione del README. Lo stato completo è in `ROADMAP.md`.

Riferimenti: [Hyprland Lua](https://wiki.hypr.land/Configuring/Start/), [Quickshell](https://quickshell.org/docs/v0.3.0/types/), [PopupAnchor](https://quickshell.org/docs/v0.3.0/types/Quickshell/PopupAnchor/), [IdleInhibitor](https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/IdleInhibitor/), [Hyprshot](https://github.com/Gustash/Hyprshot), [DDC/CI luminosità](https://www.ddcutil.com/command_getvcp/), [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/), [hyprlock](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/), [hyprpaper](https://wiki.hypr.land/Hypr-Ecosystem/hyprpaper/), [portale Hyprland](https://wiki.hypr.land/Hypr-Ecosystem/xdg-desktop-portal-hyprland/), [Electron Wayland](https://www.electronjs.org/blog/tech-talk-wayland), [cliphist](https://github.com/sentriz/cliphist), [wf-recorder](https://github.com/ammen99/wf-recorder), [Kitty](https://sw.kovidgoyal.net/kitty/conf/).
