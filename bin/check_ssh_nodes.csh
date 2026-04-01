#!/bin/tcsh

# i.keshelashvili@gsi.de

set conf_file = "$HOME/mncl/config/list_of_nodes.conf"

if (! -f $conf_file) then
    echo "\033[5;31mError: $conf_file file not found\033[0m"
    exit 1
endif

source $HOME/mncl/bin/read_config.csh

foreach node ($list_paras)
    # Check if ssh connection can be established to the node
    ssh -o BatchMode=yes -o ConnectTimeout=1 ikeshel@$node "echo ok" >& /dev/null

    if ($status == 0) then
        echo "$node alive SSH"
	continue
    endif
    echo "$node dead SSH"
end


