# dotfiles

## Needed Packages

**Pacman:**
```conf
# Hyprland Ecosystem
hyprland
hypridle
hyprlock
hyprpaper

# Hyprland Must-Have
dunst
pipewire
pipewire-pulse
wireplumber
xdg-desktop-portal-hyprland
polkit-kde-agent
qt5-wayland
qt6-wayland

# Desktop Manager
sddm

# Terminal
alacritty

# File Manager
thunar
thunar-archive-plugin
thunar-media-tags-plugin
thunar-volman
tumbler
file-roller
gvfs

# Status Bar
waybar

# App Menu
wofi

# Bluetooth
bluez
bluez-utils

# GTK/QT
nwg-look
qt5ct
qt6ct

# Utilities
brightnessctl
inotify-tools
pavucontrol
network-manager-applet
cliphist
udiskie
xsettingsd

# Fonts
otf-font-awesome
ttf-fira-code
ttf-firacode-nerd
ttf-jetbrains-mono
ttf-jetbrains-mono-nerd
ttf-roboto
noto-fonts-emoji

# Flatpak
flatpak
gnome-software

# Optional
btop
usbutils
easyeffects
neofetch
neovim
discord

```

**AUR:**
```conf
# Needed
blueman
libinput-gestures
hyprshot
wlogout

# Optional
1password
google-chrome
spotify
visual-studio-code-bin

```

## Install

1. Install dependencies

2. Clone this repository
    ```sh
    git clone https://github.com/angelobdev/dotfiles.git
    ```
3. Move to the cloned repo
   ```sh
   cd dotfiles/
   ``` 

4. Copy config files
    ```sh
    cp -R .config/* ~/.config/
    ```
5. Enjoy!

## Recommended aliases
```zshrc
# Aliases
alias code='code--enable-features=UseOzonePlatform --ozone-platform=wayland'
alias pmclean='pacman -Qdtq | sudo pacman -Rns -' # Remove unsed packages
alias pmlist="pacman -Qe | awk '!/linux|apple|t2|tiny-dfr|lib/' | cut -d ' ' -f1"
```

## Notes
- Enable NTP (timedatectl set-ntp true)
- Automatic tiny-dfr restart after suspend
