# Plugin Hyprland

[← README](../README.md)

Configurazione: [`plugins.lua`](../hypr/.config/hypr/config/plugins.lua). I bind screenshot sono in [`binds.lua`](../hypr/.config/hypr/config/binds.lua); le gesture del touchpad rimangono in `input.lua`.

## Installazione

Build verificata: **Hyprland e hyprland-devel 0.56.2-17.fc44.x86_64**, COPR nett00n. Dipendenze usate:

```sh
sudo dnf install hyprland-devel git gcc-c++ make cmake pkgconf-pkg-config \
  meson ninja-build glm-devel lua-devel pango-devel patch \
  qt6-qtsvg-devel qt6-qtwayland-devel layer-shell-qt-devel \
  opencv-devel pipewire-devel pulseaudio-libs-devel fftw-devel ffmpeg-devel \
  nlohmann-json-devel libjpeg-turbo-devel x265-devel libde265-devel
```

Dal terminale della sessione Hyprland, come utente normale:

```sh
cd ~/.dotfiles
./scripts/install-hypr-plugins.py
```

Lo script richiede sudo per la cache protetta di hyprpm; confermare l’aggiunta del repository locale quando hyprpm lo chiede. Le compilazioni avvengono come utente. Alla prima esecuzione possono richiedere diversi minuti. Sulla macchina di sviluppo sono già disponibili le build verificate in cache.

Il packaging in [`scripts/hyprpm`](../scripts/hyprpm) scarica i cinque progetti originali alle revisioni della tabella seguente. Lo script ne crea una copia Git locale sotto `~/.local/share/dotfiles/hyprpm/`, registrata da hyprpm come **dotfiles-desktop**. I cinque plugin si abilitano/disabilitano singolarmente con i loro nomi runtime. Nessun commit viene creato nella repository dei dotfiles.

| Plugin / sorgente                                              | Revisione fissata                          |
| -------------------------------------------------------------- | ------------------------------------------ |
| [Hyprspace](https://github.com/KZDKM/Hyprspace)                | `cf08bed82621c1fb943ef4934ff0ba36540fea77` |
| [Hyprgrass](https://github.com/horriblename/hyprgrass)         | `8e605468cbf429791d61ddbfaeb14ff5e08fec3e` |
| [Hyprglass](https://github.com/hyprnux/hyprglass)              | `84c1a5ab217101a317d4edaab7fba2efcc1bf346` |
| [hypr-hot-edge](https://github.com/claychinasky/hypr-hot-edge) | `32b2dffdf2900a5a4b8cd10133f6a58cfd7ec4d6` |
| [HyprCapture](https://github.com/gfhdhytghd/HyprCapture)       | `bf4d1f9021fc288200002f5a7d8291ed56f0df83` |

## Adattamenti per Fedora COPR

Questa build espone il commit Git `unknown`. Il normale download degli header da una revisione Git non è quindi utilizzabile. L’installer controlla che sessione, binario installato e pacchetto `hyprland-devel` corrispondano, poi prepara gli header hyprpm copiando quelli RPM reali. Conserva `version.h` e ABI originali. La cache resta di proprietà root in `/var/cache/hyprpm/$USER`; le sole operazioni privilegiate riguardano questa cache.

Hyprland Fedora usa Lua 5.4. hypr-hot-edge richiede 5.5 nel CMake, pur usando API disponibili in entrambe: il packaging corregge esclusivamente la ricerca della dipendenza, imponendo Lua 5.4. La build e il caricamento sono stati verificati con la libreria usata dal compositor.

Il manifest usa il nome runtime **HyprCapture** (maiuscole incluse), evitando il disallineamento del manifest upstream. Installa l’helper Qt `~/.local/bin/hyprcapture-ui` e le licenze. Non avvia l’installazione opzionale del runtime TensorFlow/AEC per il microfono: le catture non lo richiedono. La registrazione Quickshell continua a usare wf-recorder.

## Comportamento

- **Hyprspace:** overview dal top-left o da tre dita verso l’alto sul touchscreen. Lo stesso angolo la chiude al passaggio successivo; nessuna scorciatoia keyboard per aprirla, `Esc` per chiuderla. `affectStrut = false` evita lo spostamento del layout e `hideTopLayers`/`hideOverlayLayers` escludono le superfici shell dalle miniature.
- **hypr-hot-edge:** attiva un workspace speciale interno vuoto; il callback Lua lo chiude e alterna apertura/chiusura di Hyprspace sul monitor interessato. Il trigger si riarma quando il puntatore lascia l’angolo. Non è uno scratchpad utilizzabile dalle applicazioni.
- **Hyprgrass:** tre dita orizzontali per i workspace; dal basso verso l’alto per le app; dall’alto verso il basso per i controlli. Le gesture sono registrate nuovamente a ogni reload.
- **Hyprglass:** preset `desktop` basato su `subtle`, blur moderato, tinta grafite e rifrazione leggera. Distorsione centrale e aberrazione cromatica a zero. Le app completamente opache restano opache; le superfici traslucide ricevono l’effetto. I namespace dei pannelli Quickshell sono espliciti; la soglia alpha esclude l’area trasparente esterna ai pannelli. La top bar senza sfondo non viene filtrata sui soli testi.
- **HyprCapture:** `Super + Shift + S` / `Stamp` selezionano un’area; `Super + Shift + Alt + S` / `Alt + Stamp` catturano il monitor corrente. Tutti e quattro i bind usano `open_editor()`. Salvataggio PNG nella directory Immagini XDG, sottocartella `Screenshots`, copia e notifica di sistema. `overlay_scope = "focus"` consente di spostare la selezione tra monitor. La configurazione attuale non assegna scorciatoie separate alla cattura diretta o alla finestra attiva.

`BarVisibility.qml` usa il piccolo helper `bar_visibility.py` per osservare l’alpha delle superfici `desktop-bar` via socket IPC locale Hyprland (100 ms, processo unico, output solo quando cambia lo stato). Quando Hyprspace le rende invisibili, Quickshell porta a zero la zona esclusiva e la regione di input sul monitor interessato. La superficie rimane mappata, mantenendo anche l’IdleInhibitor: Hyprspace può ripristinarne l’alpha alla chiusura. La barra torna a riservare 38 px. In caso di disconnessione il servizio ripristina il comportamento normale.

La [guida interfaccia](interfaccia.md) contiene la tabella dei bind e delle gesture.

## Verifiche e aggiornamenti

```sh
hyprpm list
hyprctl plugin list
hyprctl configerrors
desktop-plugins reload
```

`desktop-plugins reload` è eseguito automaticamente all’avvio di Hyprland. Prima del caricamento confronta RPM, ABI e binario in esecuzione con lo stato salvato dall’installer. Dopo un aggiornamento COPR sospende l’autoload e mostra una notifica: il solo hash `unknown` non basta a riconoscere una build compatibile.

I pin e la build RPM accettata sono intenzionalmente espliciti in `scripts/hyprpm/build.py`. Per un aggiornamento del compositor occorre verificare nuove revisioni compatibili, ricompilare e provarle in una sessione isolata prima di aggiornare quel controllo. `hyprpm update` sul packaging locale mantiene i pin; non seleziona automaticamente nuove revisioni upstream.

Per cambiare il packaging sulla stessa build: `hyprpm remove dotfiles-desktop`, poi ripetere l’installer. Per cambiare ABI/header, verificare prima eventuali altri repository registrati: l’installer rifiuta una cache di ABI diverso e non la sovrascrive. Il ripristino della cache richiede la ricompilazione di tutti i plugin che la usano.

Per disabilitare temporaneamente un plugin, per esempio:

```sh
hyprpm disable hyprglass
desktop-plugins reload
hyprctl reload
```

L’installer riabilita tutti e cinque. I blocchi Lua sono protetti e permettono l’avvio anche senza plugin. Il blur nativo di Hyprland rimane come fallback quando Hyprglass è disabilitato.

Installazione nella sessione principale completata: i cinque plugin risultano abilitati in hyprpm e caricati in Hyprland; `desktop-plugins reload` e `hyprctl configerrors` passano senza errori.

Verificato in sessione isolata: caricamento dei cinque `.so`, parsing dei file Lua reali, hot-edge → overview con chiusura del workspace interno, riarmo e screenshot del monitor di prova. Verifiche aggiuntive su due output virtuali 2880×1800 a scala 1,667 e 1920×1080 a scala 1: stesso hot corner per aprire/chiudere, zona riservata 38 → 0 → 38 sul solo monitor interessato, overlay HyprCapture su entrambi, PNG alle risoluzioni native e toolbar dell’editor visibile sul display frazionario. Le gesture fisiche e la selezione sui display reali rimangono da confermare nell’uso quotidiano.
