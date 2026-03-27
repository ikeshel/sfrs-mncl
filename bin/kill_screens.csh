#!/bin/csh

# i.keshelashvili@gsi.de

set list_of_screens = "list_of_screens.csv"

if (! -f $list_of_screens) then
    echo "\033[5;31mError: list_of_screens.csv file not found\033[0m"
    exit 1
endif

set sessions = `awk -F',' '{print $1}' $list_of_screens`
echo "Sessions to kill: $sessions"

foreach session ($sessions)
    # Check if screen session exists
    if (`screen -ls | grep -c "\.$session"` > 0) then
        echo "Closing screen session: $session"
        screen -S $session -X quit
    else
        echo "Screen session '$session' does not exist"
    endif
end

echo ""
screen -ls
