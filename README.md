# Hyprland + Quickshell

Desktop custom per Fedora 44: Hyprland Lua, interfaccia QML in Quickshell e pacchetti GNU Stow. Versioni locali: Hyprland 0.56.2, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6, hyprpaper 0.8.4.

## Pacchetti

| Stow | Contenuto |
| --- | --- |
| `hypr` | `~/.config/hypr/hyprland.lua` e moduli Lua |
| `quickshell` | Barra, launcher, controlli, notifiche, power e agente Polkit |
| `shell` | `~/.local/bin/desktop-{shell,session,power,theme}` |
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
  f44-backgrounds-base
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

- Barra flottante con logo Fedora, workspace occupati (più quello attivo), pill attiva azzurra, titolo, tray e orologio.
- Icone vettoriali per rete, volume, batteria, notifiche e sessione; tooltip con stato. Le icone app originali restano colorate.
- Launcher con ricerca, titoli a sinistra, icone, frecce e Invio; le app da terminale si aprono in Kitty.
- Superfici traslucide, bordi leggeri e blur Hyprland; sfondo fornito da hyprpaper.
- Controlli PipeWire di volume, mute e microfono. Rete tramite API Quickshell/NetworkManager, password Wi-Fi Personal e reti salvate; Enterprise richiede un profilo preconfigurato.
- Bluetooth per dispositivi già associati; profili energetici se disponibili.
- Notifiche, popup, azioni, centro notifiche e non disturbare; storico in memoria, azzerato al riavvio della shell.
- Agente Polkit QML con l'identità predefinita proposta da Polkit.
- Power: blocco immediato; sospensione, logout, riavvio e spegnimento con conferma. Gli errori del comando vengono mostrati nel pannello.

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
| `Super + Invio` / `Super + Q` | Kitty |
| `Super + Spazio` / `Super + R` | Applicazioni |
| `Super + A` / `Super + N` / `Super + M` | Controlli / notifiche / sessione |
| `Super + L` | Blocca schermo |
| `XF86Sleep` | Sospendi con lock |
| `Super + Shift + R` | Riavvia Quickshell |
| `Super + C` | Chiudi finestra |
| `Super + V` / `Super + F` | Floating / fullscreen |
| `Super + frecce` / `Super + Shift + frecce` | Focus / sposta finestra |
| `Super + 1…9,0` / `Super + Shift + 1…9,0` | Workspace / sposta al workspace |
| `Super + S` / `Super + Shift + S` | Mostra / popola scratchpad |
| `Super + trascina sinistro/destro` | Sposta / ridimensiona finestra |
| Tasti multimediali | Volume, microfono, luminosità |
| `Esc` / clic esterno | Chiudi pannello |

## Personalizzazione e diagnostica

`hypr/.config/hypr/config/local.lua` contiene gli override della macchina. Palette QML in `Theme.qml`, icone in `assets/icons`, CSS GTK e colori Qt nei rispettivi pacchetti. Quickshell e Hyprland ricaricano i propri config; riavviare hypridle/hyprpaper dopo aver modificato i loro file. L'autostart avviene al login; `desktop-session start` e `desktop-shell start` evitano processi duplicati.

```sh
~/.local/bin/desktop-shell status
~/.local/bin/desktop-session status
qs log -c desktop
hyprctl configerrors
hyprctl hyprpaper listactive
cat ~/.local/state/desktop-session/hypridle.log
./scripts/check.sh
```

## Rimozione

Prima fermare la shell (`desktop-shell stop`) e i daemon (`pkill -x hypridle; pkill -x hyprpaper`), poi `./scripts/stow.py remove`. La rimozione stacca i link, preserva la repo e non ripristina automaticamente i backup. Copiare dal backup i file desiderati e ricaricare Hyprland. Le preferenze GSettings restano: per ripristinarle usare i valori nel file `interface-before-theme.ini` con `gsettings set org.gnome.desktop.interface CHIAVE VALORE`. Effettuare un nuovo login per cambiare l'ambiente Qt.

## Prossimi moduli

Pairing Bluetooth con PIN/conferma, selezione dispositivi audio, OSD, MPRIS, calendario, clipboard e impostazioni persistenti. Per screen sharing manca ancora `xdg-desktop-portal-hyprland` (il portale GTK è presente); installarlo e integrarlo in una fase dedicata.

Riferimenti: [Hyprland Lua](https://wiki.hypr.land/Configuring/Start/), [Quickshell](https://quickshell.org/docs/v0.3.0/types/), [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/), [hyprlock](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/), [hyprpaper](https://wiki.hypr.land/Hypr-Ecosystem/hyprpaper/).
