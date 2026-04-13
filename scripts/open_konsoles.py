#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
script to open konsole windows for each mbs_node and screen, and arrange them on the screen
'''

import sys
import subprocess
import time
import shlex
from loguru import logger

##
sys.path.append('package')
from config_reader import ConfigReader

##
USERNAME = "ikeshel"
LOGINS = [] #
SCREENS = [] #["mbs", "web", "com"]
SLEEP_TIME = 0.5

cfg = ConfigReader("config/list_of_nodes.conf")
for raw in cfg:
    try:
        node, desc = ConfigReader.parse_entry(raw)
        logger.success(f"{node!r:12} -> {desc}")
        LOGINS.append(f"{USERNAME}@{node}")
    except ValueError as exc:
        logger.error(f"⚠️  {exc}")    

cfg = ConfigReader("config/list_of_screens.conf")
for raw in cfg:
    try:
        screen, desc = ConfigReader.parse_entry(raw)
        logger.success(f"{screen!r:12} -> {desc}")
        SCREENS.append(f"{screen}")
    except ValueError as exc:
        logger.error(f"⚠️  {exc}")    


#=============================================================================
def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

#=============================================================================
def get_kde_panel_height(panel_index=0):
    script = f'print(panelById(panelIds[{panel_index}]).height)'
    cmd = ['qdbus6', 'org.kde.plasmashell', '/PlasmaShell', 'org.kde.PlasmaShell.evaluateScript', script]
    logger.debug(f"Command: {' '.join(cmd)}")
    try:
        result = run(cmd)
    except Exception as exc:
        logger.error(f"Error running command: {exc}")
        return 50
    
    if result.returncode != 0:
        logger.error(f"qdbus6 command failed: {result.stderr.strip()}")
        return 50
    
    return int(result.stdout.strip())

#=============================================================================
def get_screen_resolution():
    cp = run(["xdpyinfo"])
    for line in cp.stdout.splitlines():
        if "dimensions:" in line:
            res = line.split()[1]
            x_str, y_str = res.split("x", 1)
            return int(x_str), int(y_str)
    raise RuntimeError("Could not determine screen resolution")

#=============================================================================
def get_monitor_count():
    cp = run(["xrandr", "--query"])
    count = sum(1 for line in cp.stdout.splitlines() if " connected" in line)
    return max(count, 1)

#=============================================================================
def get_wmctrl_lines():
    cp = run(["wmctrl", "-l"])
    return cp.stdout.splitlines()

#=============================================================================
def window_exists(title:str)->bool:
    lines = get_wmctrl_lines()

    for line in lines:
        if title in line:
            return True

    return False

#=============================================================================
def debug_titles():
    print("Current wmctrl windows:")
    for line in get_wmctrl_lines():
        print(line)

#=============================================================================
def move_window(title:str, x:int, y:int, w:int, h:int)->None:
    for attempt in range(3):
        move_cmd = ["wmctrl", "-r", f"{title}", "-e", f"0,{x},{y},{w},{h}"]
        ret = run(move_cmd)
        logger.debug(f"Moving command: {' '.join(move_cmd)}")
        if ret.returncode == 0:
            return
        logger.error(f"Failed to move window {title} (attempt {attempt+1}/3): {ret.stderr.strip()}")
        time.sleep(SLEEP_TIME)


#=============================================================================
def open_konsol(title:str, mbs_node:str, screen:str)->None:

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
def close_konsoles()->None:
    for mbs_node in LOGINS:
        for screen in SCREENS:
            title = f"{mbs_node}_{screen}"
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

#=============================================================================
def open_konsoles()->None:

    xx, yy = get_screen_resolution()
    logger.debug(f"Screen resolution: {xx}x{yy}")

    monitors = get_monitor_count()
    logger.debug(f"Monitors detected: {monitors}")

    KDE_menu_bar_height = get_kde_panel_height()
    logger.debug(f"KDE menu bar height: {KDE_menu_bar_height}px")

    # debug_titles()

    screen_w = xx // monitors
    screen_h = yy - KDE_menu_bar_height

    win_w = screen_w // len(LOGINS)
    win_h = screen_h // len(SCREENS)

    for key_login, mbs_node in enumerate(LOGINS):
        pos_x = key_login*win_w

        for key_screen, screen in enumerate(SCREENS):
            title = f"{mbs_node}_{screen}"

            check_scrn = ["ssh", f"{mbs_node}", "cd ~/mncl;./bin/check_screens.csh"]
            logger.debug(f"Checking screen: {check_scrn}")
            result = run(check_scrn)
            logger.debug(result.stdout)

            if window_exists(title):
                logger.info(f"Already running: {title}")
                continue
            
            pos_y = (len(SCREENS)-1-key_screen) * win_h + 1 # top space px

            logger.info(f"Opening {mbs_node} at x={pos_x} y={pos_y}")
            open_konsol(title, mbs_node, screen)

            time.sleep(SLEEP_TIME)
            move_window(title, pos_x, pos_y, win_w, win_h)

#=============================================================================
# main entry point
#=============================================================================
if __name__ == "__main__":

    if "close" in sys.argv:
        close_konsoles()

    if "check" in sys.argv:
        check_konsoles()

    if "node" in sys.argv:
        for index, mbs_node in enumerate(sys.argv):
            print(f"{index}: {mbs_node}")

    if "open" in sys.argv:
        open_konsoles()
