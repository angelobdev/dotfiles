# Hyprland + Quickshell

Desktop custom per Fedora 44, con Hyprland Lua, interfaccia Quickshell e pacchetti GNU Stow. La repo gestisce barra, launcher, Control Center, notifiche, calendario, clipboard, cattura e registrazione, blocco e sfondi.

I servizi NetworkManager, BlueZ, PipeWire/WirePlumber, UPower e Polkit forniscono i backend. Tutti i pannelli sono Quickshell, senza applet esterne.

## Da dove partire

- [Installazione, pacchetti e aggiornamenti](docs/installazione.md)
- [Plugin Hyprland: overview, gesture touch, glass e screenshot](docs/plugins.md)
- [Interfaccia e scorciatoie](docs/interfaccia.md)
- [Configurazione, tema, luminosità e sfondi](docs/configurazione.md)
- [Blocco, impronte, XWayland e condivisione schermo](docs/integrazioni.md)
- [Diagnostica e stato delle verifiche](docs/diagnostica.md)
- [Roadmap](ROADMAP.md)

## Aggiornare la configurazione

Dopo aver installato le dipendenze indicate nella guida:

```sh
cd ~/.dotfiles
./scripts/stow.py dry-run
./scripts/stow.py apply
./scripts/check.sh
hyprctl reload
desktop-session start
desktop-shell restart
```

Non usare sudo con Stow. `apply` salva eventuali file in conflitto prima di collegarli alla repo. Dopo l’aggiunta di nuovi file ripetere `apply`.

L’angolo top-left alterna Hyprspace e desktop; la barra rilascia spazio e input durante l’overview. HyprCapture segue il puntatore tra monitor: `Super + Shift + S` o `Stamp` aprono la cattura area con editor; `Super + Shift + Alt + S` o `Alt + Stamp` quella del monitor con editor. Hints mostra i bind della sessione attiva, raggruppando screenshot e registrazione in “Cattura schermo”.

Le impostazioni principali sono in [`Config.qml`](quickshell/.config/quickshell/desktop/Config.qml), la palette in [`Theme.qml`](quickshell/.config/quickshell/desktop/Theme.qml) e gli override della macchina in [`local.lua`](hypr/.config/hypr/config/local.lua).

Quickshell è organizzato per funzione (`bar`, `controlcenter`, `panels`, `notifications`, `session`, `osd`), con componenti e servizi condivisi. Il [layout delle cartelle](docs/configurazione.md#struttura-quickshell) descrive dove intervenire. I launcher locali di ChatGPT e File/Nautilus preferiscono Wayland; vedere [XWayland e nitidezza](docs/integrazioni.md#xwayland).
