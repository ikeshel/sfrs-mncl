#!/bin/csh

# List of screen sessions to close
set sessions = (mbs web)

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
