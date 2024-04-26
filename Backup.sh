#!/bin/bash

# Configuration file
config="config/directories.conf"
out_dir="dots"

# Saving arguments
option=$1

# Main Function
function backup() {

    while IFS= read line; do

        # Skipping comments and blank lines
        first_char=${line:0:1}
        if [[ "$first_char" == '#' || "$first_char" == '' ]]; then
            continue
        # Getting base directory
        elif [[ "$first_char" == 'D' ]]; then
            base_dir=$(echo "$line" | cut -d ' ' -f2)
            echo "Copying '$base_dir' directory..."
            continue
        fi

        # Checking if file or directory
        if [[ $base_dir ]]; then

            # Getting dir/file name
            dir_file=$(echo "$line" | tr -d ' ')

            # Saving/Loading    
            printf "$base_dir/$dir_file ... "

            # Path is a file
            if [ -f "$HOME/$base_dir/$dir_file" ]; then

                # Copying...
                cp $HOME/$base_dir/$dir_file $out_dir/$base_dir/
        
            # Path is a directory
            elif [ -d "$HOME/$base_dir/$dir_file" ]; then

                # Copying...
                mkdir -p $out_dir/$base_dir/$dir_file/
                cp -R $HOME/$base_dir/$dir_file/* $out_dir/$base_dir/$dir_file/

            fi
        fi

        echo "done!"

    done < "$config"
}

# Options functions
function help() {
    echo -e "Options:"
    echo -e "--help\t\tShows this help dialog"
    echo -e "--save\t\tSaves files defined in the '$config' file!"
    echo -e "--load\t\tLoads files in the '$out_dir' directory into home!"
}

function invalid_option() {
    if [[ "$1" == "" ]]; then
        echo -e "You need to specify an argument...\n"
    else
        echo -e "'$1' is not a valid argument...\n"
    fi
    help
}

# Main
if [[ "$option" == "--help" ]]; then
    help
elif [[ "$option" == "--save" ]]; then
    echo "Saving..."
    backup s
    echo "Done!"
elif [[ "$option" == "--load" ]]; then
    # cp -R dots/* $HOME
    echo "Loading is unsupported!"
    exit;
else
    invalid_option $option
fi