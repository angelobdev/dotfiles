# Hyprland dotfiles

## Screenshots

![Screenshot 1](https://i.imgur.com/rhGCxl7.png)

## Install

1. Install dependencies (defined in `config/packages.conf`)

2. Clone this repository
   ```sh
   $ git clone https://github.com/angelobdev/dotfiles.git
   ```
3. Move to the cloned repo

   ```sh
   $ cd dotfiles/
   ```

4. Copy config files
   ```sh
   $ chmod +x Backup.sh
   $ ./Backup.sh --load
   ```
5. Enjoy!

## Manual TODOs

- Enable NTP (timedatectl set-ntp true)
