# Configurazione

[← README](../README.md)

## Configurazione del Control Center

Modificare `quickshell/.config/quickshell/desktop/Config.qml`. La configurazione è dichiarativa, senza editor nell’interfaccia:

```qml
readonly property var controlCenterModules: ["network", "bluetooth", "brightness", "audio", "media", "doNotDisturb", "idle"]
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

Il bus `6` è un esempio: usare quello effettivo mostrato da `ddcutil detect`. Per DDC/CI installare facoltativamente `sudo dnf install ddcutil`, abilitare DDC/CI nel monitor e verificare i permessi `/dev/i2c-*` previsti dal pacchetto. La shell non esegue sudo. Dopo la prima installazione, applicare i permessi ai dispositivi già collegati: `sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=i2c-dev && sudo udevadm trigger --subsystem-match=drm`. Un monitor senza backend o senza accesso hardware mostra uno slider disabilitato con il motivo. L’accordion elenca solo gli altri monitor connessi; hotplug e valori vengono aggiornati mentre il Control Center è aperto. Lo slider e la percentuale seguono subito il valore scelto; durante il trascinamento le scritture vengono inviate con un intervallo di circa 70 ms, accorpate e serializzate. Il dato hardware viene riconciliato al termine senza ripristinare letture precedenti. Il valore minimo è 1% per evitare lo spegnimento accidentale del backlight. Non viene usata un’opacità software per simulare la luminosità.

Audio e Bluetooth usano le API native Quickshell. Bluetooth usa anche un helper Python/Gio registrato come agente BlueZ `KeyboardDisplay`: PIN, conferme e autorizzazioni richiedono una risposta esplicita, con timeout di 120 secondi. La ricerca si ferma chiudendo il pannello; l’associazione non rende automaticamente attendibile il dispositivo. Dopo l’associazione selezionare il dispositivo per connetterlo. Le sezioni Hints sono ricavate dai tasti/descrizioni dei bind reali: i bind personalizzati non riconosciuti restano in Altro e sono ricercabili.

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

## Sfondi persistenti

```sh
~/.local/bin/desktop-wallpaper                     # apre il selettore QML
~/.local/bin/desktop-wallpaper /percorso/immagine.png
~/.local/bin/desktop-wallpaper --reset             # ripristina Fedora
```

Il selettore parte dalla home e permette di risalire, digitare una cartella e aprire la raccolta degli sfondi. Supporta PNG, JPEG, WebP, JXL, AVIF, BMP e TIFF. ImageMagick converte il file selezionato in un JPEG gestito, applica l’orientamento EXIF e preserva l’originale. L’anteprima dipende dai decoder Qt; un JXL privo di anteprima può comunque essere convertito e applicato.

La selezione vive in `~/.local/state/desktop-session/wallpaper/`: `selection.json` conserva il percorso originale e `current.jpg` punta alla copia convertita. Hyprpaper usa quel link nel config Stow e ritrova la scelta al login; la repo non viene riscritta a ogni cambio sfondo. `desktop-session start` inizializza il link allo sfondo Fedora soltanto quando manca. Una conversione o applicazione fallita conserva la selezione precedente. La copia locale resta utilizzabile anche se si sposta l’originale.

I dati di stato non sono inclusi in Git e seguono il layout XDG standard di questa repo. Lo script serializza richieste concorrenti, passa i percorsi come argomenti e normalizza il nome inviato a IPC, gestendo anche spazi, virgole e caratteri speciali.

## Tema delle applicazioni

Tema dark-glassy: superfici grafite traslucide in Quickshell, blur di Hyprland e testo sempre opaco. Le superfici shell usano gli stessi RGB della palette nativa (`#191a1d`, `#202226`, `#292b30`), con alpha separato. Gli elementi selezionati usano testo scuro opaco per conservare il contrasto. Kitty usa uno sfondo al 94%, font Adwaita Mono e colori ANSI coordinati; il testo rimane opaco. I bordi Hyprland restano disabilitati e le finestre inattive conservano l’opacità 0,92.

Palette grigio grafite, primary neutro `#d4d6dc`, testo chiaro, Adwaita Sans e icone Papirus-Dark. GTK, Qt e hyprlock condividono la palette; GSettings usa l’accent slate. GTK 3 usa Adwaita-dark e colori CSS; GTK 4/libadwaita riceve la preferenza scura anche via GSettings/portale e i colori nominati. Qt Widgets usa Fusion e palette custom in entrambe le generazioni. Il plugin qt6ct installato accetta anche la chiave `qt5ct`, quindi `QT_QPA_PLATFORMTHEME=qt5ct` copre Qt 5/6. Qt Quick Controls usa Basic; applicazioni con stile proprio possono ignorare queste preferenze.

`desktop-theme` applica GSettings e importa le variabili Qt in D-Bus/systemd; alla prima esecuzione salva i valori precedenti in `~/.local/state/dotfiles/interface-before-theme.ini`. Riavviare le applicazioni già aperte per adottare il tema; il prossimo login applica anche l'ambiente completo. Le app Flatpak dipendono dai runtime/temi esposti alla sandbox e potrebbero non seguire tutti gli override CSS.

La shell usa superfici traslucide scure con blur e bordi sottili neutri. Hyprland non disegna bordi delle finestre: opacità attiva/fullscreen 1, inattiva 0.92 e blur abilitato. Questi valori sono in `hypr/.config/hypr/config/appearance.lua`. Le finestre attive conservano piena leggibilità.

## Multimedia e calendari

Il modulo `media` del Control Center usa MPRIS nativo Quickshell: titolo/artista, precedente, riproduci/pausa, successivo e posizione quando esposta dal lettore. Con più lettori si può scegliere quello desiderato. I pulsanti seguono le capacità pubblicate dall’app; non serve `playerctl`.

`calendarSources: []` in `Config.qml` include tutti i calendari EDS abilitati. Per limitarli, inserire gli UID delle sorgenti, ad esempio `calendarSources: ["system-calendar"]`. I nomi possono cambiare, gli UID identificano la sorgente. Configurare gli account negli strumenti GNOME già in uso; il pannello usa le stesse credenziali e gli stessi eventi, senza memorizzare password nella repo. Le ricorrenze sono espanse da EDS. Il calendario aggiorna gli eventi all’apertura, al cambio mese, ogni minuto mentre aperto e con **Aggiorna**. In caso di errore mostra il motivo e conserva in memoria gli eventi già letti per la sorgente non disponibile.

Per elencare gli UID locali:

```sh
python3 - <<'PY'
import gi
gi.require_version('EDataServer', '1.2')
from gi.repository import EDataServer
registry = EDataServer.SourceRegistry.new_sync(None)
for source in registry.list_enabled('Calendar'):
    print(source.get_uid(), source.get_display_name())
PY
```

## Display Philips FTV: esito della verifica

Il 12 ottobre 2026 il display collegato via HDMI viene esposto da Hyprland come `DP-1`, bus I²C 14. Dopo l’installazione di `ddcutil` e l’applicazione delle regole udev, EDID e connettore sono leggibili, ma `getvcp 10` e `capabilities` non rispondono correttamente; anche la lettura con controlli iniziali disabilitati e tempi più lunghi fallisce. Non è stato scritto alcun valore hardware. Hotplug fisico verificato: monitor e controlli spariscono allo scollegamento e ricompaiono alla riconnessione.

Il controllo integrato di GNOME può usare una luminosità software tramite Mutter, soprattutto in HDR: vedi la [spiegazione dello sviluppatore GNOME](https://blog.sebastianwick.net/posts/gnome-49-backlight-changes/). È una possibile spiegazione del diverso comportamento; non dimostra che il Philips esponga DDC/CI. Questo desktop controlla backlight/DDC hardware, senza introdurre automaticamente un dimmer software. La prova positiva di lettura, scrittura e ripristino DDC richiede un display che risponda al protocollo.
