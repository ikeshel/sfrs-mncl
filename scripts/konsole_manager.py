#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
script to open konsole windows for each mbs_node and screen, and arrange them on the screen

NOTE: screens are here meant as a screen session name, not a physical monitor screen
'''

## standard library imports
import argparse
import sys
import subprocess
import time
import shlex
from loguru import logger

##
sys.path.append('package')
from config_reader import ConfigReader

## constants
USERNAME = "ikeshel"
NODES    = [] # ['x86l-132', 'x86l-170', 'x86l-253', 'x86l-157']
LOGINS   = [] # ['ikeshel@x86l-132', 'ikeshel@x86l-170', 'ikeshel@x86l-253', 'ikeshel@x86l-157']
SCREENS  = [] # ["mbs", "web", "com"]
SLEEP_TIME = 0.5

##
cfg = ConfigReader("config/list_of_nodes.conf")
for raw in cfg:
    try:
        node, desc = ConfigReader.parse_entry(raw)
        logger.success(f"{node!r:12} -> {desc}")
        NODES.append(node)
        LOGINS.append(f"{USERNAME}@{node}")
    except ValueError as exc:
        logger.error(f"⚠️  {exc}")    

##
cfg = ConfigReader("config/list_of_screens.conf")
for raw in cfg:
    try:
        screen, desc = ConfigReader.parse_entry(raw)
        logger.success(f"{screen!r:12} -> {desc}")
        SCREENS.append(f"{screen}")
    except ValueError as exc:
        logger.error(f"⚠️  {exc}")    


#=============================================================================
def get_screen_resolution():
    cp = subprocess.run(["xdpyinfo"], text=True, capture_output=True)
    for line in cp.stdout.splitlines():
        if "dimensions:" in line:
            res = line.split()[1]
            x_str, y_str = res.split("x", 1)
            return int(x_str), int(y_str)
    raise RuntimeError("Could not determine screen resolution")

#=============================================================================
def get_kde_panel_height(panel_index=0):

    script = f'print(panelById(panelIds[{panel_index}]).height)'
    cmd = ['qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', script]
    # logger.debug(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=3)
    except Exception as exc:
        logger.error(f"Error running command: {exc}")
        return 50
    
    if result.returncode != 0:
        logger.error(f"qdbus6 command failed: {result.stderr.strip()}")
        return 50
    
    return int(result.stdout.strip())

#=============================================================================
def get_monitor_count() -> int:
    cp = subprocess.run(["xrandr", "--query"], text=True, capture_output=True)
    count = sum(1 for line in cp.stdout.splitlines() if " connected" in line)
    return max(count, 1)

#==============================================================================
def init_konsole_positioning():

    global win_w, win_h, node_screens
    ##
    full_width, full_height = get_screen_resolution()
    # logger.debug(f"Screen resolution: {full_width}x{full_height}")

    monitor_count = get_monitor_count()
    # logger.debug(f"monitor_count detected: {monitor_count}")

    KDE_menu_bar_height = get_kde_panel_height()
    # logger.debug(f"KDE menu bar height: {KDE_menu_bar_height}px")

    # debug_titles()

    screen_w = full_width // monitor_count
    screen_h = full_height - KDE_menu_bar_height

    win_w = full_width // len(NODES)
    # win_w = screen_w // len(NODES)

    win_h = screen_h // len(SCREENS)

    from collections import namedtuple
    global Rect
    Rect = namedtuple('Rect', ['x', 'y', 'w', 'h'])

    logger.info(f"Screen resolution: {win_w}x{win_h} (monitors: {monitor_count}, panel height: {KDE_menu_bar_height}px)")

    node_screens = {}

    for i, node in enumerate(NODES):
        for j, screen in enumerate(SCREENS):
            x = i * win_w +10
            y = j * win_h
            node_screens[(node, screen)] = Rect(x, y, int(0.9*win_w), int(1.0*win_h)) # 10% margin for better visibility

    logger.debug(f"Calculated window positions: {node_screens}")

#=============================================================================
def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

#=============================================================================
def get_wmctrl_lines() -> list[str]:
    cp = run(["wmctrl", "-l"])
    return cp.stdout.splitlines()

#=============================================================================
def window_exists(title:str) -> bool:
    lines = get_wmctrl_lines()
    for line in lines:
        if title in line:
            return True
    return False

#=============================================================================
def debug_titles() -> None:
    logger.info("Current wmctrl windows:")
    for line in get_wmctrl_lines():
        logger.info(line)

#==============================================================================
def check_konsoles()->None:
    for mbs_node in LOGINS:
        for screen in SCREENS:
            title = f"{mbs_node}_{screen}"
            if window_exists(title):
                logger.info(f"Found window: {title}")
            else:
                logger.warning(f"Window not found: {title}")

#==============================================================================
def close_konsole(title:str)->None:
    if window_exists(title):
        try:
            result = run(["wmctrl", "-c", title])
            if result.returncode != 0:
                logger.error(f"Failed to close window {title}: {result.stderr.strip()}")
        except Exception as exc: 
            logger.error(f"Error closing window {title}: {exc}")
        result = run(["wmctrl", "-c", title])
        logger.info(f"Closing {title}")
    else:
        logger.info(f"Window not found, cannot close: {title}")

#==============================================================================
def close_konsoles()->None:
    for mbs_node in LOGINS:
        for screen in SCREENS:
            title = f"{mbs_node}_{screen}"
            close_konsole(title)

#=============================================================================
def open_konsoles()->None:
    for key_login, mbs_node in enumerate(LOGINS):
        pos_x = key_login*win_w

        check_scrn = ["ssh", f"{mbs_node}", "cd ~/mncl;./bin/check_screens.csh"]
        logger.debug(f"Checking screen: {check_scrn}")
        result = run(check_scrn)
        logger.debug(result.stdout)

        for index_screen, screen in enumerate(SCREENS):
            title = f"{mbs_node}_{screen}"


            if window_exists(title):
                logger.info(f"Already running: {title}")
                continue
            
            pos_y = (len(SCREENS)-1-index_screen) * win_h + 1 # top space px

            logger.info(f"Opening {mbs_node} at x={pos_x} y={pos_y}")
            open_konsol(title, mbs_node, screen)


#=============================================================================
def open_konsol(title:str, mbs_node:str, screen:str)->None:

    if window_exists(title):
        logger.info(f"Already running: {title}")
        return

    remote_cmd = (
        f"screen -dr {shlex.quote(screen)} "
        f"|| screen -r {shlex.quote(screen)} "
        f"|| echo 'screen session {screen} not found on {mbs_node}'"
    )

    local_cmd = f"ssh -Y {shlex.quote(mbs_node)} -t {shlex.quote(remote_cmd)};echo;"

    ssh_cmd = [
        "konsole",
        "-p", f"tabtitle={title}",
        "--hold",
        "-e", 
        "bash", "-lc", local_cmd,
    ]

    logger.debug(f"SSH command: {' '.join(ssh_cmd)}")
    subprocess.Popen(ssh_cmd)

#=============================================================================
def move_window(title:str, x:int, y:int, w:int, h:int)->None:
    niter = 3
    for attempt in range(niter):
        move_cmd = ["wmctrl", "-r", f"{title}", "-e", f"0,{x},{y},{w},{h}"]
        ret = run(move_cmd)
        logger.debug(f"Moving command: {' '.join(move_cmd)}")
        if ret.returncode == 0:
            return
        logger.error(f"Failed to move window {title} (attempt {attempt+1}/{niter}): {ret.stderr.strip()}")

#=============================================================================
# main entry point
#=============================================================================
if __name__ == "__main__":

    init_konsole_positioning()

    parser = argparse.ArgumentParser()
    parser.add_argument('--nodes', required=True, help='Comma-separated list of nodes')
    parser.add_argument('--screens', required=True, help='Comma-separated list of screens')

    # Mutually exclusive flags
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--open', '-o', action='store_true')
    action.add_argument('--check', '-c', action='store_true')
    action.add_argument('--close', '-x', action='store_true')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    nodes   = [v.strip() for v in args.nodes.split(',') if v.strip()]
    screens = [v.strip() for v in args.screens.split(',') if v.strip()]

    # Determine which action was chosen
    if args.open:
        logger.info(f"Opening {nodes} on {screens}")
    elif args.check:
        logger.info(f"Checking {nodes} on {screens}")
    elif args.close:
        logger.info(f"Closing {nodes} on {screens}")
    elif args.help:
        parser.print_help()
        sys.exit(0)

    # main loop
    for index_node, mbs_node in enumerate(nodes):
    
        if mbs_node in NODES:
            logger.debug(f"{index_node}: {mbs_node}")
            login=f"{USERNAME}@{mbs_node}"

            for index_screen, screen in enumerate(screens):
                title = f"{login}_{screen}"

                if screen in SCREENS:

                    if args.close:
                        close_konsole(title)

                    elif args.check:
                        if window_exists(title):
                            logger.warning(f"Found window: {title}")
                        else:
                            logger.warning(f"Window not found: {title}")
                    
                    elif args.open:            
                        open_konsol(title, login, screen)
                        time.sleep(SLEEP_TIME)

                        xywh = node_screens.get((f'{mbs_node}', f'{screen}'), Rect(50, 50, 640, 480))
                        move_window(title, xywh.x, xywh.y, xywh.w, xywh.h)
                else:
                    logger.error(f"Screen {screen} not found in {SCREENS}")
        else:
            logger.error(f"Node {mbs_node} not found in {NODES}\n")

