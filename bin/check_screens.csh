#!/bin/csh

# i.keshelashvili@gsi.de

source /home/irakli/mncl/bin/list_of_nodes.csh

foreach session ($sessions)
    # Check if screen session already exists
    if (`screen -ls | grep -c "\.$session"` == 0) then
        echo "Creating screen session: $session"
        screen -dmS $session
    else
        echo "Screen session '$session' already exists"
    endif
end

echo ""
echo "Done. Active sessions:"
screen -ls

