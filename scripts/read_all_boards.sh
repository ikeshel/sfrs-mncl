#!/bin/bash

declare -a list_sft_board=(
    "0,0" "0,1" "0,2" "0,3" "0,4" "0,5"
    "1,0" "1,1"
    "2,0" "2,1" "2,2" "2,3" "2,4" "2,5"
    "3,0" "3,1"
)

MY_COMMAND=""
for board_pair in "${list_sft_board[@]}"; do
    IFS=',' read -r sfp board <<< "$board_pair"
    MY_COMMAND+="/mbs/driv/mbspexV3_5.10-64_DEB/bin/gosipcmd -rxd $sfp $board 0x20005c;" # FPGA temperature
    MY_COMMAND+="/mbs/driv/mbspexV3_5.10-64_DEB/bin/gosipcmd -rxd $sfp $board 0x200064;" # SiPM temperature
done

# echo "Executing command: $MY_COMMAND"
ssh -o ConnectTimeout=1 ikeshel@X86L-253 "$MY_COMMAND"
