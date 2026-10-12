# Hyprland + Quickshell

Dotfiles per Fedora 44. Hyprland gestisce le finestre; tutta l'interfaccia desktop è QML custom in Quickshell. Base verificata con **Hyprland 0.56.2**, **Quickshell 0.3.2** e **GNU Stow 2.4.1**.

## Pacchetti Stow

| Pacchetto | Destinazione | Contenuto |
| --- | --- | --- |
| `hypr` | `~/.config/hypr` | Configurazione Lua modulare |
| `quickshell` | `~/.config/quickshell/desktop` | Shell QML e servizi condivisi |
| `shell` | `~/.local/bin/desktop-shell` | Avvio, riavvio e controllo IPC |

La repo è la fonte dei config: modifica i file qui, Stow crea solo symlink. Gli script Stow presuppongono i percorsi XDG standard sotto `$HOME`; per un `XDG_CONFIG_HOME` differente occorre adattare il layout dei pacchetti. Non eseguire Stow con sudo.

## Installazione

I repository COPR `nett00n/hyprland` e `errornointernet/quickshell` sono già abilitati su questa macchina.

```sh
sudo dnf install hyprland quickshell stow kitty brightnessctl wireplumber \
  NetworkManager bluez upower power-profiles-daemon
cd ~/.dotfiles
./scripts/stow.py dry-run
./scripts/stow.py apply
./scripts/check.sh
~/.local/bin/desktop-shell start
hyprctl reload
```

`dry-run` non modifica file e segnala i conflitti (GNU Stow restituisce errore se ce ne sono). `apply` sposta soltanto i file in conflitto in `~/.local/state/dotfiles/backups/<data>/`, esegue una simulazione, quindi crea i link con `--no-folding`. Non usa `--adopt`. Se trova symlink nelle directory genitrici, si ferma per evitare scritture in destinazioni inattese.

Per ristoware dopo aver aggiunto file basta ripetere `apply`. Per rimuovere i link:

```sh
cd ~/.dotfiles
./scripts/stow.py remove
```

La rimozione non cancella la repo e non ripristina automaticamente i backup. Per tornare al config originale, fermare prima Quickshell con `~/.local/bin/desktop-shell stop`, rimuovere i link, copiare il file `hyprland.lua` dal backup in `~/.config/hypr/`, poi eseguire `hyprctl reload`.

## Interfaccia disponibile

- Sfondo QML, barra per ogni monitor, workspace 1–10, titolo della finestra, orologio e batteria.
- Launcher di applicazioni con ricerca, frecce e Invio; le applicazioni da terminale si aprono in Kitty.
- Controlli PipeWire per volume, mute e microfono.
- Rete via API Quickshell/NetworkManager: Ethernet, Wi-Fi, reti salvate, nuove reti aperte o WPA/WPA2/WPA3 Personal, inserimento password ed errori di connessione. Enterprise richiede un profilo preconfigurato.
- Bluetooth: alimentazione adattatore e connessione/disconnessione di dispositivi già associati. Il pairing con PIN/conferma è un modulo successivo.
- Profili energetici tramite power-profiles-daemon, se supportati dall'hardware.
- Server notifiche, popup, centro notifiche, azioni, cancellazione e modalità non disturbare. Lo storico rimane in memoria per la durata del processo.
- System tray per le applicazioni e relativi menu.
- Agente Polkit QML con prompt di autenticazione; usa l'identità predefinita proposta da Polkit. PIN Bluetooth e Polkit sono protocolli distinti.
- Menu di logout, riavvio e spegnimento con conferma.

I servizi **NetworkManager**, **BlueZ**, **PipeWire/WirePlumber**, **UPower**, **Polkit** e **power-profiles-daemon** restano componenti di sistema. Nessun Waybar, nm-applet, Blueman, Sway o demone di notifiche separato viene avviato da questi config.

## Scorciatoie

| Tasti | Azione |
| --- | --- |
| `Super + Invio` / `Super + Q` | Kitty |
| `Super + Spazio` / `Super + R` | Launcher |
| `Super + A` | Centro di controllo |
| `Super + N` | Centro notifiche |
| `Super + M` | Menu sessione |
| `Super + Shift + R` | Riavvia Quickshell |
| `Super + C` | Chiudi finestra |
| `Super + V` / `Super + F` | Floating / fullscreen |
| `Super + frecce` | Sposta focus |
| `Super + Shift + frecce` | Sposta finestra |
| `Super + 1…9,0` | Workspace 1…10 |
| `Super + Shift + 1…9,0` | Sposta al workspace |
| `Super + S` / `Super + Shift + S` | Mostra / popola scratchpad |
| `Super + trascina sinistro/destro` | Sposta / ridimensiona finestra |
| Tasti multimediali | Volume, microfono e luminosità |
| `Esc` / clic sullo sfondo del pannello | Chiudi pannello |

## Personalizzazione e diagnostica

- `hypr/.config/hypr/config/local.lua`: override della macchina (monitor, scala, input). Tastiera iniziale italiana; scala automatica.
- `quickshell/.config/quickshell/desktop/Theme.qml`: palette, font e raggi. Non richiede Nerd Fonts.
- `modules/`: interfaccia; `services/`: audio e notifiche; `components/`: controlli riutilizzabili.
- Quickshell ricarica QML quando salvi; Hyprland ricarica i config Lua.

```sh
~/.local/bin/desktop-shell status
qs ipc -c desktop show
qs log -c desktop
hyprctl configerrors
./scripts/check.sh
```

L'autostart usa l'evento `hyprland.start`, quindi non si ripete a ogni reload. `desktop-shell start` usa `--no-duplicate`. Dopo il primo Stow, avvia manualmente la shell come sopra; dai login successivi parte da sola. Il riavvio di Quickshell azzera lo storico notifiche.

## Passi successivi verso un DE completo

La base non include ancora lockscreen PAM/Wayland, idle/lock automatico, pairing Bluetooth con agente, selettori dispositivi audio, OSD, controlli MPRIS, calendario, clipboard e impostazioni persistenti. Il lockscreen va implementato usando il protocollo di session lock, insieme all'autenticazione PAM e alle verifiche di ripristino; un overlay grafico non costituisce un blocco della sessione.

Per condivisione schermo e selezione file nelle app sandbox servono anche i portali di sistema. Su questa macchina manca `xdg-desktop-portal-hyprland`; `xdg-desktop-portal-gtk` è presente. Installazione prevista:

```sh
sudo dnf install xdg-desktop-portal-hyprland
```

I portali non sostituiscono la shell: espongono funzionalità del sistema alle applicazioni. La loro integrazione e quella del lockscreen sono da completare nella prossima fase.

Riferimenti: [config Lua Hyprland](https://wiki.hypr.land/Configuring/Start/), [API Quickshell](https://quickshell.org/docs/v0.3.0/types/), [rete](https://quickshell.org/docs/v0.3.0/types/Quickshell.Networking/), [Polkit](https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.Polkit/).
