# ROADMAP

Stato aggiornato al 13 ottobre 2026, verificato sui file della repository.
Le voci completate indicano funzionalità presenti nel codice; le verifiche hardware ancora necessarie sono elencate separatamente.

## Direzione attuale

- Seguire questa roadmap per i prossimi sviluppi.
- Conservare la palette grafite; la nuova richiesta del 13 ottobre introduce il blur glass tramite Hyprglass, senza richiedere il precedente restyling chiaro di macOS.
- Mantenere l’interfaccia desktop custom in Quickshell, con Hyprland Lua e pacchetti GNU Stow.

## Completato

### Base del desktop

- [x] Repository dotfiles organizzata in pacchetti Stow, con simulazione, backup dei conflitti e script di verifica.
- [x] Configurazione Hyprland modulare in Lua: monitor, input, aspetto, regole, scorciatoie, sessione e override locali.
- [x] Avvio e gestione della sessione tramite gli script `desktop-shell` e `desktop-session`.
- [x] Supporto XWayland di base e fallback dei backend GTK/Qt.
- [x] Integrazione di hypridle, hyprlock e hyprpaper; blocco, DPMS e sospensione automatica configurati.
- [x] Hyprlock: layout moderno grafite, password PAM e autenticazione impronta nativa in parallelo; lettore Synaptics acquisito e verifica dell’indice destro avviata nel test headless.

- [x] Quickshell riorganizzato per funzione (`bar`, `controlcenter`, `panels`, `notifications`, `session`, `osd`), con componenti e servizi condivisi e import aggiornati.
- [x] Verifica testi sfocati di ChatGPT e Nautilus: entrambe le istanze segnalate erano XWayland; avvio nativo Wayland verificato con istanze isolate, launcher locali corretti e ambiente di sessione aggiornato. Riavvio delle app dell’utente necessario per applicare il backend.

### Barra e navigazione

- [x] Top bar da 38 px con sfondo trasparente/traslucido, logo Fedora e menu applicazioni.
- [x] Workspace occupati e attivo rappresentati da pill, con evidenza dello stato attivo e urgente.
- [x] Almeno due pill per monitor, segnaposto vuoti con ID globalmente unici e navigazione con rotella/touchpad sull’intera altezza dell’area workspace.
- [x] Titolo della finestra, spacer, tray, batteria con percentuale e icona, Hints, notifiche, Control Center, giorno/ora e power.
- [x] Menu tray QML con sfondo/bordo coordinati, angoli arrotondati, hover, sottomenu, ancoraggio sotto l’icona sul relativo monitor e navigazione da tastiera; Esc e clic esterno chiudono il menu.
- [x] Icone di stato centrate e tooltip nativi posizionati sotto i pulsanti.
- [x] Launcher con ricerca, icone applicazioni, titoli allineati a sinistra e navigazione da tastiera.
- [x] Pannello Hints con ricerca, categorie e scorciatoie/descrizioni lette dai bind reali di Hyprland.
- [x] Menu sessione con navigazione da tastiera, lock, sospensione, logout, riavvio e spegnimento; conferma per le azioni previste.
- [x] Calendario mensile con selezione del giorno, navigazione da tastiera, indicatori e agenda degli eventi dai calendari GNOME/Account online tramite Evolution Data Server; supporto ricorrenze, giornate intere, più giorni e fusi orari, lettura senza modifica degli account.
- [x] OSD per volume, mute speaker/microfono e luminosità, con livello/dispositivo, timeout configurabile e posizionamento sul monitor interessato; rilevamento dei cambiamenti anche a pannello chiuso.
- [x] Selettore sfondi QML su `Super + Shift + W`, anteprima e persistenza della scelta tra sessioni.
- [x] Bind HyprCapture con editor per area (`Super + Shift + S` / `Stamp`) e monitor (`Super + Shift + Alt + S` / `Alt + Stamp`); rimossi i bind scratchpad e il conflitto di scorciatoie.

### Plugin del compositor

- [x] Configurazione Lua dedicata con controlli sulla disponibilità delle API, compatibile anche con avvio senza plugin.
- [x] Cinque plugin compilati e caricati nella sessione isolata: Hyprspace, Hyprgrass, Hyprglass, hypr-hot-edge e HyprCapture.
- [x] Packaging locale hyprpm con revisioni upstream fissate, header RPM COPR corrispondenti e patch di compilazione Lua 5.4 per hypr-hot-edge; nomi manifest allineati a quelli runtime.
- [x] Hot corner top-left collegato a Hyprspace, con riarmo all’uscita e nessun bind keyboard per l’apertura; apertura e chiusura del workspace interno verificate in sessione isolata.
- [x] Gesture touchscreen Hyprgrass per workspace, overview, launcher e controlli; gesture touchpad conservate.
- [x] Preset Hyprglass neutro con rifrazione leggera, senza aberrazione cromatica né distorsione centrale, applicato alle superfici traslucide e ai pannelli Quickshell.
- [x] Bind screenshot migrati a HyprCapture; cattura PNG del monitor di prova verificata. Autoload con controllo versione RPM/ABI per evitare build obsolete dopo aggiornamenti COPR.
- [x] Hyprspace: eliminata la riserva aggiuntiva da 200 px, barre/overlay esclusi dalle miniature; la barra invisibile rilascia spazio e input senza perdere la superficie da ripristinare. Verifica 38 → 0 → 38 sul monitor interessato in sessione isolata.
- [x] Hot corner top-left con toggle apertura/chiusura dopo il riarmo all’uscita dall’angolo.
- [x] Editor nativo HyprCapture su tutte e quattro le scorciatoie screenshot; Hints usa la categoria “Cattura schermo”, mostra “Stamp” e aggiorna i bind anche al reload di Hyprland con pannello aperto.
- [x] Overlay HyprCapture mobile tra monitor; verificati output virtuali a scala 1,667 e 1 con PNG nativi 2880×1800/1920×1080 e toolbar editor sul display frazionario.
- [x] Installazione nella cache protetta di hyprpm e caricamento nella sessione principale: tutti e cinque abilitati e caricati; autoload verificato con `desktop-plugins reload`, configurazione senza errori.
- [ ] Prova fisica delle gesture touchscreen, dell’hot corner su entrambi i monitor e dell’aspetto glass durante l’uso quotidiano.

### Pannelli e Control Center

- [x] Control Center modulare, con ordine, visibilità e dimensioni configurabili in `Config.qml`.
- [x] Sottopannelli Rete e Bluetooth in alto a destra, con ritorno al Control Center e intestazioni condivise.
- [x] Wi-Fi: attivazione, scansione, ricerca/selezione reti, connessione e prompt password per reti Personal; Enterprise tramite profili preconfigurati.
- [x] Bluetooth: adattatori, attivazione, ricerca, associazione tramite agente BlueZ `KeyboardDisplay` con PIN/passkey, conferma e autorizzazione esplicita, annullamento/timeout, connessione/disconnessione e batteria. Protocollo verificato su bus isolato; associazione con un dispositivo fisico da provare dall’interfaccia.
- [x] Luminosità: slider principale, accordion per altri monitor e associazione configurabile dei backend backlight/DDC.
- [x] Aggiornamento immediato dello slider luminosità e invio delle modifiche durante il trascinamento, con gestione delle letture precedenti e degli errori.
- [x] Controlli MPRIS nel Control Center: titolo/artista, precedente, riproduci/pausa, successivo, posizione e scelta del lettore; capacità e scomparsa dei lettori gestite con API native Quickshell.
- [x] Audio: slider e percentuale del volume, mute, selezione ingressi/uscite e livello microfono; accordion nel Control Center e pannello dedicato.
- [x] Non disturbare nel Control Center, con switch allineato a destra.
- [x] Centro notifiche in alto a destra: storico in memoria, azioni e controlli Non disturbare/Elimina tutte con icone a destra del titolo.
- [x] Popup notifiche con icone, markup di testo limitato e sicuro, clic sinistro per l’azione predefinita e clic destro per nascondere conservando lo storico; pulsanti Activate/Elimina/Nascondi rimossi dai popup. Azioni secondarie e controlli del centro notifiche conservati. Non disturbare silenzia i popup.
- [x] Pannello batteria in alto a destra: percentuale, potenza, energia, tempi stimati e selezione dei profili energetici con icone.
- [x] Indicatore del profilo energetico nel blocco batteria della barra: foglia per Risparmio, fulmine per Prestazioni e nessuna icona aggiuntiva per Bilanciato; tooltip con profilo corrente e aggiornamento dal servizio di sistema.
- [x] Pulsanti con testo e padding conservato; variante compatta senza padding per chevron e controlli audio stretti. Eliminazione singola delle notifiche rossa, in linea con il titolo e con la stessa dimensione del testo.
- [x] Dimensioni comuni dei pannelli laterali e icone di ritorno/chiusura da 22 px.
- [x] Toggle “Resta attivo” collegato a un `IdleInhibitor` Wayland sulle barre: indipendente dall’apertura del Control Center, senza pacchetti aggiuntivi.
- [x] Clipboard manager Quickshell con ricerca, tastiera, testo/immagini, pausa ed eliminazione; storico cliphist e bridge XWayland verificati in entrambe le direzioni.

### Integrazioni e documentazione

- [x] Agente di autenticazione Polkit in Quickshell.
- [x] Tema dark-glassy coerente: palette grafite condivisa tra Quickshell, GTK 3/4 e Qt 5/6, superfici shell traslucide con testo opaco e accento neutro; le app conservano la geometria nativa e possono avere stili propri.
- [x] Tema Kitty coordinato, font Adwaita Mono, sfondo traslucido e palette ANSI.
- [x] Primary neutro e configurazione Hyprland senza bordi finestra, con opacità delle finestre inattive e blur.
- [x] Ambiente Electron Wayland e wrapper per scelta esplicita Wayland/X11; VS Code verificato su entrambi i backend con profili temporanei, Zen aperto rilevato nativo Wayland.
- [x] Portali XDG: routing Hyprland/GTK, importazione dell’ambiente prima dell’avvio e selettore di condivisione custom Quickshell.
- [x] Screen sharing via ScreenCast/PipeWire e registrazione monitor/area via wf-recorder, pannello QML, scelta audio, indicatore nella barra e salvataggio video; test reale del portale e registrazione di una finestra dedicata, prova nella web app specifica elencata sotto.
- [x] README sintetico e guide separate in `docs/` per installazione, interfaccia/scorciatoie, configurazione, integrazioni e diagnostica; aggiornate per pairing, MPRIS, calendari e risultati DDC/CI.
- [x] Hotplug fisico HDMI verificato con Philips FTV: rimozione e ripristino del monitor, della barra e dell’elenco luminosità, senza riavvio della shell. Permessi I²C applicati tramite le regole udev del pacchetto ddcutil.

## Prossimi sviluppi

- [ ] Completare la prova positiva DDC/CI (lettura, variazione minima e ripristino) con un display che risponda al protocollo. Il Philips FTV collegato viene identificato sul bus 14 ma non risponde a VCP 10 né alle capabilities, anche dopo l’applicazione dei permessi e con tempi maggiorati. Il controllo integrato GNOME può usare luminosità software: non è una conferma del supporto DDC/CI del display.

## Possibili estensioni individuate

- [ ] Multilanguage support
- [ ] Multi-distro installation support (add debian, arch)
