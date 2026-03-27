#!/bin/tcsh

# i.keshelashvili@gsi.de

set conf_file = "list_of_nodes.conf"

if (! -f $conf_file) then
    echo "\033[5;31mError: $conf_file file not found\033[0m"
    exit 1
endif

source bin/read_config.csh

foreach node ($list_paras)
    # Check if ssh connection can be established to the node
    ssh -o BatchMode=yes -o ConnectTimeout=3 pi@$node "echo ok" >& /dev/null

    if ($status == 0) then
        echo "Node $node is alive (SSH reachable)"
        exit 0
    endif
    echo "Node $node is not reachable via SSH"
end


