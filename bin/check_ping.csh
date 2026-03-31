#!/bin/tcsh

# i.keshelashvili@gsi.de

set conf_file = "config/list_of_nodes.conf"

if (! -f $conf_file) then
    echo "\033[5;31mError: $conf_file file not found\033[0m"
    exit 1
endif

source bin/read_config.csh

foreach node ($list_paras)

    ping -c 1 -W 2 $node >& /dev/null

    if ($status == 0) then
        echo "Node $node is alive"
    else
        echo "Node $node is not reachable"
    endif
end

