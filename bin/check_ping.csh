#!/bin/tcsh

# i.keshelashvili@gsi.de

set conf_file = "$HOME/sfrs-mncl/config/list_of_nodes.conf"

if (! -f $conf_file) then
    echo "\033[5;31mError: $conf_file file not found\033[0m"
    exit 1
endif

source $HOME/sfrs-mncl/bin/read_config.csh

foreach node ($list_paras)

    echo "ping -c 1 -W 2 $node >& /dev/null"
    ping -c 1 -W 2 $node >& /dev/null

    if ($status == 0) then
        echo "$node alive ping"
    else
        echo "$node dead ping"
    endif
end

