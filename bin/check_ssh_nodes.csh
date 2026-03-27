#!/bin/tcsh

set node = "raspi4"

ssh -o BatchMode=yes -o ConnectTimeout=3 pi@$node "echo ok" >& /dev/null

if ($status == 0) then
    echo "$node is alive (SSH reachable)"
    exit 0
endif
echo "$node is not reachable via SSH"
