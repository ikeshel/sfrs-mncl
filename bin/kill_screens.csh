#!/bin/csh

# i.keshelashvili@gsi.de

# This script reads the list of screen sessions from the list_of_screens.conf file and kills them if they exist. 
# It also prints the list of active screens after killing.   

set conf_file = "$HOME/mncl/config/list_of_screens.conf"

# Check if the list_of_screens.conf file exists
if (! -f $conf_file) then
    echo "\033[5;31mError: $conf_file file not found\033[0m"
    exit 1
endif

# Source the read_config.csh script to read the list of screens
source $HOME/mncl/bin/read_config.csh

# Loop through the list of screens and kill them if they exist
foreach session ($list_paras)
    # Check if screen session exists
    if (`screen -ls | grep -c "\.$session"` > 0) then
        echo "Closing screen session: $session"
        screen -S $session -X quit
    else
        echo "Screen session '$session' does not exist"
    endif
end
