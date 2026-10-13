# Installazione e gestione

[← README](../README.md)

Versioni verificate: Hyprland 0.56.2, Quickshell 0.3.2, hypridle 0.1.8, hyprlock 0.9.6 e hyprpaper 0.8.4.

## Pacchetti

| Stow         | Contenuto                                                                                          |
| ------------ | -------------------------------------------------------------------------------------------------- |
| `hypr`       | `~/.config/hypr/hyprland.lua` e moduli Lua                                                         |
| `quickshell` | Barra, launcher, controlli, notifiche, power, agente Polkit e cataloghi `i18n/it_IT.json`, `i18n/en_US.json`                                       |
| `shell`      | `~/.local/bin/desktop-{shell,session,power,theme,wallpaper,electron,portal-picker}` e helper Python per sfondi, luminosità, clipboard, registrazione, Bluetooth, calendari EDS e traduzioni condivise (`i18n.py`) |
| `hypridle`   | Timer e coordinamento lock/sospensione                                                             |
| `hyprlock`   | Blocco Wayland con PAM e impronta fprintd                                                              |
| `hyprpaper`  | Sfondo Fedora 44 notturno, su ogni monitor                                                         |
| `gtk`        | Palette, font, icone e preferenza scura GTK 3/4                                                    |
| `qt`         | Palette Fusion e icone per Qt 5/6 tramite qt5ct/qt6ct                                              |
| `kitty`      | Terminale grafite con sfondo traslucido e palette ANSI condivisa                                  |
| `portals`    | Preferenze XDG: Hyprland per cattura/condivisione, GTK per file e impostazioni                      |

## Installazione e aggiornamento

I COPR della macchina sono `nett00n/hyprland` ed `errornointernet/quickshell`.

```sh
sudo dnf install hyprland quickshell stow kitty brightnessctl ddcutil wireplumber \
  NetworkManager bluez upower power-profiles-daemon \
  hypridle hyprlock hyprpaper qt5ct qt6ct papirus-icon-theme ripgrep \
  f44-backgrounds-base xorg-x11-server-Xwayland ImageMagick python3 libnotify jq grim slurp \
  xdg-desktop-portal xdg-desktop-portal-hyprland xdg-desktop-portal-gtk \
  wl-clipboard cliphist wf-recorder pulseaudio-utils fprintd fprintd-pam \
  python3-gobject evolution-data-server
cd ~/.dotfiles
./scripts/stow.py dry-run
./scripts/stow.py apply
./scripts/check.sh
hyprctl reload
~/.local/bin/desktop-session start
# Solo quando si installano/cambiano i portali, terminando prima le condivisioni:
systemctl --user restart xdg-desktop-portal-hyprland xdg-desktop-portal-gtk xdg-desktop-portal
~/.local/bin/desktop-shell restart
```

La repo è la fonte dei file; Stow crea symlink senza folding. `dry-run` non scrive e restituisce errore in presenza di conflitti. `apply` salva i file in conflitto in `~/.local/state/dotfiles/backups/<data>/`, simula l'operazione e applica i link. Rifiuta directory genitrici che siano symlink. Ripetere `apply` dopo aver aggiunto file. Non usare sudo con Stow.

Il supporto multilingua usa Qt e Python già installati, senza dipendenze aggiuntive. La lingua della shell deriva da `/etc/locale.conf`; dettagli e cataloghi in [Lingua dell’interfaccia](configurazione.md#lingua-dellinterfaccia).

I pacchetti usano i percorsi XDG standard sotto `$HOME`. I due `color_scheme_path` Qt contengono `/home/angelo`: aggiornarli quando si installa su un altro utente. Lo sfondo Fedora 44 è incluso in JPEG in `hyprpaper/.local/share/wallpapers`, convertito dal JPEG XL installato (questa build hyprpaper non lo decodifica). Proviene da `f44-backgrounds-base`; licenza originale CC BY-SA 4.0 e attribuzione nei file del pacchetto Fedora.

## Plugin del compositor

Hyprspace, Hyprgrass, Hyprglass, hypr-hot-edge e HyprCapture sono gestiti tramite hyprpm. Dipendenze di compilazione, installazione e aggiornamenti sono descritti in [Plugin Hyprland](plugins.md). Ripetere Stow dopo aver aggiunto i file, quindi eseguire `./scripts/install-hypr-plugins.py` dal terminale della sessione Hyprland.

## Rimozione

Prima fermare la shell (`desktop-shell stop`) e i daemon (`pkill -x hypridle; pkill -x hyprpaper`), poi `./scripts/stow.py remove`. La rimozione stacca i link, preserva la repo e non ripristina automaticamente i backup. Copiare dal backup i file desiderati e ricaricare Hyprland. Le preferenze GSettings restano: per ripristinarle usare i valori nel file `interface-before-theme.ini` con `gsettings set org.gnome.desktop.interface CHIAVE VALORE`. Effettuare un nuovo login per cambiare l'ambiente Qt.
