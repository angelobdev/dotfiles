# Hyprland dotfiles

## Install

1. Install dependencies (defined in `config/packages.conf`)

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
5. Enjoy!```

## Manual TODOs

- Enable NTP (timedatectl set-ntp true)
- Enable utomatic tiny-dfr restart after suspend
