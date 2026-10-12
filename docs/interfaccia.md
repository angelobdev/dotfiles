# Interfaccia e scorciatoie

[← README](../README.md)

## Interfaccia

- Barra alta 38 px logici: Fedora/app menu → workspace occupati/attivo e almeno due pill per monitor → titolo → spazio → tray → batteria (percentuale + icona) → Hints → notifiche → Control Center → giorno/ora → sessione. Controlli da 30 px, icone di stato da 16 px centrate e logo da 18 px. Rete e volume vivono nel Control Center.
- Icone vettoriali e tooltip nativi posizionati sotto i pulsanti, fuori dalla superficie della barra. Le icone app originali restano colorate.
- Launcher con ricerca, titoli a sinistra, icone, frecce e Invio; le app da terminale si aprono in Kitty.
- Superfici traslucide, bordi leggeri e blur Hyprland; sfondo fornito da hyprpaper.
- Pannelli Rete, Bluetooth, Notifiche e Batteria allineati in alto a destra, con larghezza comune configurata in `Config.qml` e intestazioni con icone da 22 px. Le azioni Non disturbare/Elimina tutte sono a destra del titolo Notifiche. I profili energetici si selezionano nel pannello batteria; il blocco batteria nella barra mostra una foglia in Risparmio energetico e un fulmine in Prestazioni, senza icona aggiuntiva in Bilanciato. L’indicatore segue il profilo di sistema anche quando viene cambiato esternamente; il tooltip riporta sempre il profilo corrente.
- Pannelli separati: Rete e Wi-Fi con ricerca/selezione reti; Audio con volume, mute, ingresso/uscita predefiniti e livello microfono; Batteria con potenza in W, energia in Wh, autonomia/carica rimanente e profili energetici. Le reti Wi-Fi Personal hanno un prompt password; Enterprise richiede un profilo preconfigurato.
- Control Center compatto, in alto a destra: schede Rete/Bluetooth, luminosità del monitor primario con accordion per gli altri display, volume dello speaker selezionato con accordion per ingressi/uscite e livello microfono, controlli multimediali MPRIS, toggle Non disturbare e Resta attivo. Moduli e ordine si configurano in `Config.qml`. Bluetooth ha un sottopannello con adattatori, ricerca, associazione con PIN/conferma tramite agente BlueZ dedicato, connessione/disconnessione e batteria quando esposta da BlueZ. I profili energetici dipendono dall’hardware.
- Popup notifiche con icone e testo formattato (`b`, `i`, `u`, `s`, `strong`, `em`, `br`); clic sinistro invoca l’azione predefinita quando presente, clic destro nasconde il popup conservando la notifica. Le altre azioni restano pulsanti; eliminazione e azione predefinita come pulsante restano nel centro notifiche. Lo storico è in memoria e si azzera al riavvio della shell. Immagini e attributi HTML nel testo vengono rimossi.
- Agente Polkit QML con l'identità predefinita proposta da Polkit.
- Power navigabile da tastiera: blocco immediato; sospensione, logout, riavvio e spegnimento con conferma. Gli errori del comando vengono mostrati nel pannello.
- Calendario mensile con selezione giorno, indicatori e agenda dei calendari abilitati in GNOME/Account online. Include ricorrenze, giornate intere, più giorni e fusi orari tramite Evolution Data Server. Il pannello legge i calendari esistenti e non crea/modifica eventi o account.
- Hints con ricerca e categorie (Applicazioni, Shell e pannelli, Finestre, Workspace, Mouse, Audio e luminosità, Sessione, Altro): legge `hyprctl -j binds` a ogni apertura e mostra scorciatoia + descrizione reali, inclusi submap e bind aggiunti in `local.lua`.
- Selettore sfondi QML con navigazione cartelle e anteprima; nessun dialog esterno.
- Clipboard Quickshell con ricerca e pausa; selettore screen sharing custom e pannello registrazione con indicatore nella barra.
- OSD Quickshell per volume, mute dello speaker, microfono e luminosità: icona, livello e dispositivo, in basso al centro, senza intercettare mouse o tastiera.

NetworkManager, BlueZ, PipeWire/WirePlumber, UPower, Polkit e power-profiles-daemon forniscono i servizi di sistema. I config avviano Quickshell, hypridle e hyprpaper. Nessun Waybar, nm-applet, Blueman, Sway o server notifiche separato.

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

## Dati dei pannelli

Audio usa i nodi PipeWire e cambia i dispositivi predefiniti tramite le API Quickshell; WirePlumber decide come instradare gli stream già aperti. UPower fornisce potenza della batteria in W, energia in Wh e tempi stimati: il valore non è il consumo totale alla presa e può variare nel tempo. Se una stima manca, il pannello lo indica senza inventare un’autonomia. Il calendario legge le sorgenti abilitate di Evolution Data Server, incluse quelle degli Account online; la sincronizzazione e le credenziali rimangono gestite da GNOME. Le letture possono richiedere rete. Gli eventi sono tenuti in memoria dalla shell; EDS conserva la propria cache. Non disturbare silenzia i popup e conserva le notifiche nel centro; lo stato si azzera al riavvio della shell.
