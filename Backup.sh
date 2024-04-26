#!/bin/bash

# Configuration file
config="directories.conf"

# Saving arguments
option=$1

# Main Function
function backup(){
    mode=$1

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
            if [[ "$mode" == "s" ]]; then
                single_save "$base_dir" "$dir_file"
            elif [[ "$mode" == "l" ]]; then
                single_load "$base_dir" "$dir_file"
            else
                invalid_option
            fi

        fi

    done < "$config"

}

# Helper functions
function single_save() {
    base_dir=$1
    dir_file=$2

    printf "$base_dir/$dir_file ... "

    # Path is a file
    if [ -f "$HOME/$base_dir/$dir_file" ]; then

        # Copying...
        cp $HOME/$base_dir/$dir_file $base_dir/
        
    # Path is a directory
    elif [ -d "$HOME/$base_dir/$dir_file" ]; then
        
        # Copying...
        mkdir -p $base_dir/$dir_file
        cp -R $HOME/$base_dir/$dir_file/* $base_dir/$dir_file/
    fi

    echo "done!"
}

function single_load() {
    echo "Unsupported!"
}

# Options functions
function help() {
    echo -e "Options:"
    echo -e "--help\t\tShows this help dialog"
    echo -e "--save\t\tSave files defined in the '$config' file"
    echo -e "--load\t\tLoads files defined in the '$config' file"
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
    # backup l
    echo "Loading is unsupported!"
    exit;
else
    invalid_option $option
fi