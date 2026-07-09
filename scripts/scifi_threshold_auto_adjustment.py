#!/usr/bin/env python3

# author: i.keshelashvili@gsi.de
# This script automates the process of running the thresholdfinder.py script for multiple SFPs in separate screen sessions.

import subprocess
import os
from pathlib import Path

#                                [sfp] [start value] [cpunts / sec]
#  ~/SiFi > ./thresholdfinder.py 0 5       0x9800       100 

SCRIPT_NAME = "~/SiFi/thresholdfinder.py" # from m.heil@gsi.de

START_THRESHOLD = 0x9800
DESIRED_COUNTS_PER_SECOND = 100

SFP_LIST = [(0,0),
            (0,1),
            (0,2),
            (0,3),
            (0,4),
            (0,5),

            (1,0),
            (1,1),
            
            (2,0),
            (2,1),
            (2,2),
            (2,3),
            (2,4),
            (2,5),

            (3,0),
            (3,1)]

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Create screen session for each SFP
for sfp0, sfp1 in SFP_LIST:
    screen_name = f"thre_finder_{sfp0}_{sfp1}"
    log_file = logs_dir / f"{screen_name}.log"
    
    command = f"{SCRIPT_NAME} {sfp0} {sfp1} {hex(START_THRESHOLD)} {DESIRED_COUNTS_PER_SECOND}; exit"
    
    screen_cmd = f"screen -dmS {screen_name} -L -Logfile {log_file} bash -c '{command}'"
    
    subprocess.run(screen_cmd, shell=True)

