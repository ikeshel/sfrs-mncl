#!/bin/csh

# i.keshelashvili@gsi.de

set conf_file = "config/list_of_screens.conf"

if (! -f $conf_file) then
    echo "\033[5;31mError: $conf_file file not found\033[0m"
    exit 1
endif

source bin/read_config.csh

foreach session ($list_paras)
    # Check if screen session already exists
    if (`screen -ls | grep -c "\.$session"` == 0) then
        echo "Creating screen session: $session"
        screen -dmS $session
    else
        echo "Screen session '$session' already exists"
    endif
end


