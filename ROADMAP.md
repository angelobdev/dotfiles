# ROADMAP

Stato aggiornato al 12 ottobre 2026, verificato sui file della repository.
Le voci completate indicano funzionalità presenti nel codice; le verifiche hardware ancora necessarie sono elencate separatamente.

## Direzione attuale

- Seguire questa roadmap per i prossimi sviluppi.
- La precedente richiesta di schiarire il tema e imitare il look glassy di macOS è superata e non costituisce più un obiettivo.
- Mantenere l’interfaccia desktop custom in Quickshell, con Hyprland Lua e pacchetti GNU Stow.

## Completato

### Base del desktop

- [x] Repository dotfiles organizzata in pacchetti Stow, con simulazione, backup dei conflitti e script di verifica.
- [x] Configurazione Hyprland modulare in Lua: monitor, input, aspetto, regole, scorciatoie, sessione e override locali.
- [x] Avvio e gestione della sessione tramite gli script `desktop-shell` e `desktop-session`.
- [x] Supporto XWayland di base e fallback dei backend GTK/Qt.
- [x] Integrazione di hypridle, hyprlock e hyprpaper; blocco, DPMS e sospensione automatica configurati.

### Barra e navigazione

- [x] Top bar da 38 px con sfondo trasparente/traslucido, logo Fedora e menu applicazioni.
- [x] Workspace occupati e attivo rappresentati da pill, con evidenza dello stato attivo e urgente.
- [x] Titolo della finestra, spacer, tray, batteria con percentuale e icona, Hints, notifiche, Control Center, giorno/ora e power.
- [x] Icone di stato centrate e tooltip nativi posizionati sotto i pulsanti.
- [x] Launcher con ricerca, icone applicazioni, titoli allineati a sinistra e navigazione da tastiera.
- [x] Pannello Hints con ricerca, categorie e scorciatoie/descrizioni lette dai bind reali di Hyprland.
- [x] Menu sessione con navigazione da tastiera, lock, sospensione, logout, riavvio e spegnimento; conferma per le azioni previste.
- [x] Calendario mensile con selezione del giorno e navigazione da tastiera.
- [x] Selettore sfondi QML su `Super + Shift + W`, anteprima e persistenza della scelta tra sessioni.
- [x] Bind Hyprshot per area (`Super + Shift + S` / `Shift + Stamp`), monitor (`Stamp`), finestra (`Super + Stamp`) e finestra attiva (`Alt + Stamp`); rimossi i bind scratchpad e il conflitto di scorciatoie.

### Pannelli e Control Center

- [x] Control Center modulare, con ordine, visibilità e dimensioni configurabili in `Config.qml`.
- [x] Sottopannelli Rete e Bluetooth in alto a destra, con ritorno al Control Center e intestazioni condivise.
- [x] Wi-Fi: attivazione, scansione, ricerca/selezione reti, connessione e prompt password per reti Personal; Enterprise tramite profili preconfigurati.
- [x] Bluetooth: adattatori, attivazione, connessione/disconnessione dei dispositivi già associati e batteria quando disponibile.
- [x] Luminosità: slider principale, accordion per altri monitor e associazione configurabile dei backend backlight/DDC.
- [x] Aggiornamento immediato dello slider luminosità e invio delle modifiche durante il trascinamento, con gestione delle letture precedenti e degli errori.
- [x] Audio: slider e percentuale del volume, mute, selezione ingressi/uscite e livello microfono; accordion nel Control Center e pannello dedicato.
- [x] Non disturbare nel Control Center, con switch allineato a destra.
- [x] Centro notifiche in alto a destra: storico in memoria, azioni e controlli Non disturbare/Elimina tutte con icone a destra del titolo.
- [x] Popup notifiche e modalità Non disturbare che silenzia i popup conservando le notifiche nello storico.
- [x] Pannello batteria in alto a destra: percentuale, potenza, energia, tempi stimati e selezione dei profili energetici con icone.
- [x] Indicatore del profilo energetico nel blocco batteria della barra: foglia per Risparmio, fulmine per Prestazioni e nessuna icona aggiuntiva per Bilanciato; tooltip con profilo corrente e aggiornamento dal servizio di sistema.
- [x] Dimensioni comuni dei pannelli laterali e icone di ritorno/chiusura da 22 px.
- [x] Toggle “Resta attivo” collegato a un `IdleInhibitor` Wayland sulle barre: indipendente dall’apertura del Control Center, senza pacchetti aggiuntivi.

### Integrazioni e documentazione

- [x] Agente di autenticazione Polkit in Quickshell.
- [x] Prima integrazione del tema per GTK 3/4, Qt 5/6 e hyprlock, con font e icone condivisi; uniformità completa ancora da raggiungere.
- [x] Primary neutro e configurazione Hyprland senza bordi finestra, con opacità delle finestre inattive e blur.
- [x] README con installazione, pacchetti, funzionalità, scorciatoie, configurazione e diagnostica; aggiornato per fullscreen, screenshot, “Resta attivo” e stato dell’indicatore energetico nella barra.

## Prossimi sviluppi

- [ ] OSD per volume e luminosità.
- [ ] Tema pienamente coerente tra shell e applicazioni, senza perseguire il precedente obiettivo glassy/macOS.
- [ ] Allineamento del tema di Kitty.
- [ ] Configurazione e verifica delle applicazioni Electron con XWayland/Wayland; il supporto XWayland generale è già presente.
- [ ] Integrazione e configurazione dei portali XDG per la sessione Hyprland.
- [ ] Supporto screen sharing e registrazione dello schermo, con verifica delle applicazioni utilizzate.
- [ ] Mostrare almeno due workspace nella top bar; attualmente vengono mostrati solo quelli occupati e quello attivo.
- [ ] Clipboard manager con sincronizzazione X11/Wayland.

## Estensioni già individuate

- [ ] Pairing Bluetooth con PIN/conferma tramite agente dedicato.
- [ ] Controlli multimediali MPRIS.
- [ ] Eventi e calendari esterni nel calendario.
- [ ] Persistenza delle impostazioni della shell: Non disturbare e “Resta attivo” attualmente si azzerano al riavvio.

## Verifiche manuali ancora aperte

- [ ] Provare selezione interattiva e cattura reale con i nuovi bind Hyprshot; verificati parsing dei bind, assenza di conflitti e flussi di salvataggio/copia con backend simulati.

- [ ] Verificare sblocco hyprlock con password, chiusura del coperchio e risveglio sulla macchina reale; il test annidato documentato non copre questi percorsi hardware.
- [ ] Verificare luminosità su monitor esterni DDC/CI e hotplug con l’hardware disponibile; backend e configurazione sono presenti.
