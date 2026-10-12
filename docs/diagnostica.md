# Diagnostica e verifiche

[← README](../README.md)

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

## Verifiche di questa fase

- Popup: eventi di clic simulati sul componente reale, azione predefinita invocata una volta, clic destro senza eliminazione; markup filtrato e azioni del centro conservate.
- Bluetooth: BlueZ simulato su bus D-Bus privato, registrazione/rilascio dell’agente, PIN e passkey, conferma, rifiuto di autorizzazioni, risposte obsolete ignorate, visualizzazione codice e annullamento. Nessun dispositivo reale associato o rimosso durante i test.
- MPRIS: due lettori su bus privato, metadati, selezione, cambio stato, comandi trasporto, seek con conversione secondi/microsecondi e fallback alla rimozione del lettore.
- Calendari: lettura delle quattro sorgenti EDS già configurate senza errori; contenuti degli eventi non riportati nei log di diagnostica.
- Layout QML: Control Center, agenda, richiesta Bluetooth e popup renderizzati con dati fittizi.
- Hotplug: scollegamento e riconnessione fisici del display HDMI verificati. DDC/CI sul Philips FTV non disponibile nelle prove effettuate; [dettagli](configurazione.md#display-philips-ftv-esito-della-verifica).

La prova finale di pairing con un dispositivo fisico resta manuale, tramite **Bluetooth → Cerca dispositivi**. La lettura/scrittura DDC reale resta da validare su un monitor compatibile.

## Riferimenti

[Hyprland Lua](https://wiki.hypr.land/Configuring/Start/), [Quickshell](https://quickshell.org/docs/v0.3.0/types/), [PopupAnchor](https://quickshell.org/docs/v0.3.0/types/Quickshell/PopupAnchor/), [IdleInhibitor](https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/IdleInhibitor/), [Hyprshot](https://github.com/Gustash/Hyprshot), [DDC/CI luminosità](https://www.ddcutil.com/command_getvcp/), [hypridle](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/), [hyprlock](https://wiki.hypr.land/Hypr-Ecosystem/hyprlock/), [hyprpaper](https://wiki.hypr.land/Hypr-Ecosystem/hyprpaper/), [portale Hyprland](https://wiki.hypr.land/Hypr-Ecosystem/xdg-desktop-portal-hyprland/), [Electron Wayland](https://www.electronjs.org/blog/tech-talk-wayland), [cliphist](https://github.com/sentriz/cliphist), [wf-recorder](https://github.com/ammen99/wf-recorder), [Kitty](https://sw.kovidgoyal.net/kitty/conf/).
