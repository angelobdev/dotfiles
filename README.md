# Hyprland + Quickshell

Desktop custom per Fedora 44: Hyprland Lua, interfaccia QML in Quickshell e pacchetti GNU Stow. Versioni locali: Hyprland 0.56.2, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6, hyprpaper 0.8.4.

## Pacchetti

| Stow | Contenuto |
| --- | --- |
| `hypr` | `~/.config/hypr/hyprland.lua` e moduli Lua |
| `quickshell` | Barra, launcher, controlli, notifiche, power e agente Polkit |
| `shell` | `~/.local/bin/desktop-{shell,session,power,theme,wallpaper}` e helper wallpaper Python |
| `hypridle` | Timer e coordinamento lock/sospensione |
| `hyprlock` | Blocco Wayland con autenticazione PAM |
| `hyprpaper` | Sfondo Fedora 44 notturno, su ogni monitor |
| `gtk` | Palette, font, icone e preferenza scura GTK 3/4 |
| `qt` | Palette Fusion e icone per Qt 5/6 tramite qt5ct/qt6ct |

## Installazione e aggiornamento

I COPR della macchina sono `nett00n/hyprland` ed `errornointernet/quickshell`.

```sh
sudo dnf install hyprland quickshell stow kitty brightnessctl wireplumber \
  NetworkManager bluez upower power-profiles-daemon \
  hypridle hyprlock hyprpaper qt5ct qt6ct papirus-icon-theme ripgrep \
  f44-backgrounds-base xorg-x11-server-Xwayland ImageMagick python3
cd ~/.dotfiles
./scripts/stow.py dry-run
./scripts/stow.py apply
./scripts/check.sh
hyprctl reload
~/.local/bin/desktop-session start
~/.local/bin/desktop-shell restart
```

La repo è la fonte dei file; Stow crea symlink senza folding. `dry-run` non scrive e restituisce errore in presenza di conflitti. `apply` salva i file in conflitto in `~/.local/state/dotfiles/backups/<data>/`, simula l'operazione e applica i link. Rifiuta directory genitrici che siano symlink. Ripetere `apply` dopo aver aggiunto file. Non usare sudo con Stow.

I pacchetti usano i percorsi XDG standard sotto `$HOME`. I due `color_scheme_path` Qt contengono `/home/angelo`: aggiornarli quando si installa su un altro utente. Lo sfondo Fedora 44 è incluso in JPEG in `hyprpaper/.local/share/wallpapers`, convertito dal JPEG XL installato (questa build hyprpaper non lo decodifica). Proviene da `f44-backgrounds-base`; licenza originale CC BY-SA 4.0 e attribuzione nei file del pacchetto Fedora.

## Interfaccia

- Barra flottante alta 38 px logici, controlli alti 30 px e icone di stato da 16 px centrate; logo Fedora da 23 px, workspace occupati (più quello attivo), pill attiva azzurra, titolo, tray e orologio cliccabile. Volume e batteria mostrano la percentuale.
- Icone vettoriali per rete, volume, batteria, notifiche e sessione; tooltip con stato. Le icone app originali restano colorate.
- Launcher con ricerca, titoli a sinistra, icone, frecce e Invio; le app da terminale si aprono in Kitty.
- Superfici traslucide, bordi leggeri e blur Hyprland; sfondo fornito da hyprpaper.
- Pannelli separati: Rete e Wi-Fi con ricerca/selezione reti; Audio con volume, mute, ingresso/uscita predefiniti e livello microfono; Batteria con potenza in W, energia in Wh, autonomia/carica rimanente e profili energetici. Le reti Wi-Fi Personal hanno un prompt password; Enterprise richiede un profilo preconfigurato.
- Centro di controllo come accesso rapido ai pannelli e gestione Bluetooth per dispositivi già associati. I profili energetici dipendono dall’hardware.
- Notifiche, popup, azioni, centro notifiche e non disturbare; storico in memoria, azzerato al riavvio della shell.
- Agente Polkit QML con l'identità predefinita proposta da Polkit.
- Power navigabile da tastiera: blocco immediato; sospensione, logout, riavvio e spegnimento con conferma. Gli errori del comando vengono mostrati nel pannello.
- Calendario mensile con settimana da lunedì, selezione giorno, oggi e navigazione fra mesi; non include ancora eventi/calendari esterni.
- Hints con ricerca: legge `hyprctl -j binds` a ogni apertura e mostra scorciatoia + descrizione reali, inclusi submap e bind aggiunti in `local.lua`.
- Selettore sfondi QML con navigazione cartelle e anteprima; nessun dialog esterno.

NetworkManager, BlueZ, PipeWire/WirePlumber, UPower, Polkit e power-profiles-daemon forniscono i servizi di sistema. I config avviano Quickshell, hypridle e hyprpaper. Nessun Waybar, nm-applet, Blueman, Sway o server notifiche separato.

## Blocco, inattività e sospensione

`Super + L` e il pannello power eseguono `desktop-power lock`, che avvia hyprlock con autenticazione obbligatoria (`--grace 0`) e serializza le richieste. PAM usa `/etc/pam.d/hyprlock` fornito dal pacchetto Fedora.

| Inattività | Azione |
| --- | --- |
| 5 minuti | Blocco della sessione |
| 10 minuti | Spegnimento display (DPMS) |
| 30 minuti | Sospensione |

Personalizzare `hypridle/.config/hypr/hypridle.conf`. Il daemon rispetta gli inibitori delle applicazioni. `inhibit_sleep = 3` fa attendere a logind il segnale Wayland di sessione bloccata prima del riposo, anche con il wrapper custom. `before_sleep_cmd` copre le richieste esterne e la chiusura del coperchio quando logind la associa alla sospensione. Al risveglio riaccende i display. `desktop-power suspend` rifiuta di procedere se hypridle non è attivo.

Il config di hyprlock è stato provato in una sessione Hyprland annidata: inizializzazione PAM, rendering e conferma `onLockLocked` riusciti. Lo sblocco con la propria password, la chiusura del coperchio e il risveglio restano da verificare sulla macchina; il test annidato non prova questi percorsi hardware.

## Tema delle applicazioni

Palette blu notte, accent `#89b4fa`, Adwaita Sans e icone Papirus-Dark. GTK 3 usa Adwaita-dark e colori CSS; GTK 4/libadwaita riceve la preferenza scura anche via GSettings/portale e i colori nominati. Qt Widgets usa Fusion e palette custom in entrambe le generazioni. Il plugin qt6ct installato accetta anche la chiave `qt5ct`, quindi `QT_QPA_PLATFORMTHEME=qt5ct` copre Qt 5/6. Qt Quick Controls usa Basic; applicazioni con stile proprio possono ignorare queste preferenze.

`desktop-theme` applica GSettings e importa le variabili Qt in D-Bus/systemd; alla prima esecuzione salva i valori precedenti in `~/.local/state/dotfiles/interface-before-theme.ini`. Riavviare le applicazioni già aperte per adottare il tema; il prossimo login applica anche l'ambiente completo. Le app Flatpak dipendono dai runtime/temi esposti alla sandbox e potrebbero non seguire tutti gli override CSS.

Il vetro è applicato alla shell. Le finestre delle applicazioni mantengono superfici scure leggibili.

## Scorciatoie

| Tasti | Azione |
| --- | --- |
| `Super + B` | Browser (`zen-browser`) |
| `Super + Invio` | Kitty |
| `Super + Q` | Chiudi finestra |
| `Super + Spazio` | Applicazioni |
| `Super + Shift + C` | Centro di controllo / Bluetooth |
| `Super + Shift + E` | Rete e Wi-Fi |
| `Super + Shift + V` | Volume e dispositivi audio |
| `Super + Shift + B` | Batteria ed energia |
| `Super + Shift + N` | Notifiche |
| `Super + Shift + D` | Calendario |
| `Super + Shift + H` | Hints / bind attivi |
| `Super + Shift + Q` | Menu sessione |
| `Super + Shift + W` | Scegli sfondo |
| `Super + L` / `XF86Sleep` | Blocca / sospendi con lock |
| `Super + Shift + R` | Riavvia Quickshell |
| `Super + V` / `Super + F` | Floating / fullscreen |
| `Super + P` / `Super + J` | Pseudo tiling / orientamento split |
| `Super + frecce` / `Super + Shift + frecce` | Focus / sposta finestra |
| `Super + 1…9,0` / `Super + Shift + 1…9,0` | Workspace / sposta al workspace |
| `Super + S` / `Super + Shift + S` | Mostra / popola scratchpad |
| `Super + trascina sinistro/destro` | Sposta / ridimensiona finestra |
| Tasti multimediali | Volume, microfono, luminosità |
| `Esc` / clic esterno | Chiudi pannello |

Nel menu sessione: **↑/↓ e Tab/Shift+Tab** spostano il focus; **Invio o Spazio** attivano il pulsante. Alla richiesta di conferma il focus passa ad **Annulla**: usare **←/→ o Tab** per scegliere Conferma. **Esc** annulla la conferma, poi chiude il pannello. All’apertura il primo pulsante riceve il focus.

Nel calendario: frecce per spostare il giorno, PgUp/PgDn per il mese e Home per oggi. Nel selettore sfondo: frecce per la lista, Invio per aprire cartella/selezionare immagine, Backspace per risalire; Tab raggiunge percorso, applicazione e ripristino.

## XWayland

`hypr/.config/hypr/config/xwayland.lua` abilita esplicitamente il server XWayland installato da Fedora. `force_zero_scaling = false` conserva la scala del compositor su schermi HiDPI. Qt usa `wayland;xcb` e GTK `wayland,x11,*`, con `DISPLAY` importato nell’ambiente D-Bus/systemd al login. Le app native usano Wayland; le app X11 possono usare il bridge senza un desktop X separato.

La macchina è stata verificata con XWayland attivo e `xprop -root`. Per cambiare la politica di scala delle app X11, usare `hypr/.config/hypr/config/local.lua`; forzare la scala a zero può rendere molto piccole le app che non gestiscono HiDPI da sole.

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

Audio usa i nodi PipeWire e cambia i dispositivi predefiniti tramite le API Quickshell; WirePlumber decide come instradare gli stream già aperti. UPower fornisce potenza della batteria in W, energia in Wh e tempi stimati: il valore non è il consumo totale alla presa e può variare nel tempo. Se una stima manca, il pannello lo indica senza inventare un’autonomia. Il calendario è locale e non accede ad account esterni.

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

Verifiche eseguite: parser Lua e script, caricamento/layout QML, scansione Wi-Fi nativa, lettura dispositivi audio e dati UPower, calendario bisestile/cambio anno, navigazione completa del power menu con comando fittizio e selezione sfondo persistente. Le prove sullo sfondo coprono nomi con spazi/virgole e conservazione della scelta precedente in caso di file non valido o errore IPC.

## Rimozione

Prima fermare la shell (`desktop-shell stop`) e i daemon (`pkill -x hypridle; pkill -x hyprpaper`), poi `./scripts/stow.py remove`. La rimozione stacca i link, preserva la repo e non ripristina automaticamente i backup. Copiare dal backup i file desiderati e ricaricare Hyprland. Le preferenze GSettings restano: per ripristinarle usare i valori nel file `interface-before-theme.ini` con `gsettings set org.gnome.desktop.interface CHIAVE VALORE`. Effettuare un nuovo login per cambiare l'ambiente Qt.

## Prossimi moduli

Pairing Bluetooth con PIN/conferma, OSD, MPRIS, eventi nel calendario, clipboard e impostazioni persistenti della shell. Per screen sharing manca ancora `xdg-desktop-portal-hyprland` (il portale GTK è presente); installarlo e integrarlo in una fase dedicata.

Riferimenti: [Hyprland Lua](https://wiki.hypr.land/Configuring/Start/), [Quickshell](https://quickshell.org/docs/v0.3.0/types/), [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/), [hyprlock](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/), [hyprpaper](https://wiki.hypr.land/Hypr-Ecosystem/hyprpaper/).
