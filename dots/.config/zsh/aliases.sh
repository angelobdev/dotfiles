# Aliases
alias code='code --enable-features=UseOzonePlatform --ozone-platform=wayland'
alias pmclean='pacman -Qdtq | sudo pacman -Rns -' # Remove unsed packages
alias pmlist="pacman -Qe | awk '!/linux|apple|t2|tiny-dfr|lib/' | cut -d ' ' -f1"