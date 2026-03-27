#!/bin/tcsh

# i.keshelashvili@gsi.de

set conf_file = "list_of_nodes.conf"

if (! -f $conf_file) then
    echo "\033[5;31mError: $conf_file file not found\033[0m"
    exit 1
endif

source bin/read_config.csh

foreach session ($list_paras)
    # Check if screen session already exists
    # Ping raspi4 once with short timeout
    ping -c 1 -W 2 $session >& /dev/null

    if ($status == 0) then
        echo "$session is alive"
    else
        echo "$session is not reachable"
    endif
end

