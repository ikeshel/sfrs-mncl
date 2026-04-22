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
from matplotlib.pyplot import title

##
sys.path.append('package')
from config_reader import ConfigReader

## constants
USERNAME = "ikeshel"
NODES    = [] # ['x86l-132', 'x86l-170', 'x86l-253', 'x86l-157']
LOGINS   = [] # ['ikeshel@x86l-132', 'ikeshel@x86l-170', 'ikeshel@x86l-253', 'ikeshel@x86l-157']
SCREENS  = [] # ["mbs", "web", "com"]
SLEEP_TIME = 0.5

cfg = ConfigReader("config/list_of_nodes.conf")
for raw in cfg:
    try:
        node, desc = ConfigReader.parse_entry(raw)
        logger.success(f"{node!r:12} -> {desc}")
        NODES.append(node)
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
def get_monitor_count() -> int:
    cp = run(["xrandr", "--query"])
    count = sum(1 for line in cp.stdout.splitlines() if " connected" in line)
    return max(count, 1)

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

    win_w = xx // len(LOGINS)
    # win_w = screen_w // len(LOGINS)
    win_h = screen_h // len(SCREENS)

    for key_login, mbs_node in enumerate(LOGINS):
        pos_x = key_login*win_w

        check_scrn = ["ssh", f"{mbs_node}", "cd ~/mncl;./bin/check_screens.csh"]
        logger.debug(f"Checking screen: {check_scrn}")
        result = run(check_scrn)
        logger.debug(result.stdout)

        for key_screen, screen in enumerate(SCREENS):
            title = f"{mbs_node}_{screen}"


            if window_exists(title):
                logger.info(f"Already running: {title}")
                continue
            
            pos_y = (len(SCREENS)-1-key_screen) * win_h + 1 # top space px

            logger.info(f"Opening {mbs_node} at x={pos_x} y={pos_y}")
            open_konsol(title, mbs_node, screen)

            time.sleep(SLEEP_TIME)
            move_window(title, int(pos_x+0.1*win_w), pos_y, int(0.8*win_w), win_h)

#=============================================================================
# main entry point
#=============================================================================
if __name__ == "__main__":

    # this is help message if no arguments are provided
    if len(sys.argv) == 1:
        print("\033[93m PLEASE NOTE ARGUMENT SEQUENCE: node <node_name> screen <screen_name> [open|close|check]\033[0m")
        print(f" Usage: python {sys.argv[0]} [node all|<node_name>] [screen all|<screen_name>] [open|close|check]")
        print(f"   node all screen all open  - Open konsole windows for all nodes and screens")
        print(f"   node all screen all close - Close all konsole windows")
        print(f"   node all screen all check - Check if konsole windows exist")
        print(f"   node node <node_name> screen <screen_name> - open specific node")
        print(f"\033[92m    (e.g. '{sys.argv[0]} node x86l-XXX screen com open')\033[0m")
        sys.exit(0)

    # Parse command line arguments
    node_arg = "all"
    screen_arg = "all"
    action = "check"

    if "node" in sys.argv:
        idx = sys.argv.index("node")
        if idx + 1 < len(sys.argv):
            node_arg = sys.argv[idx + 1]

    if "screen" in sys.argv:
        idx = sys.argv.index("screen")
        if idx + 1 < len(sys.argv):
            screen_arg = sys.argv[idx + 1]

    if "close" in sys.argv:
        action = "close"
    elif "check" in sys.argv:
        action = "check"
    elif "open" in sys.argv:
        action = "open"

    print(f"Node argument: {node_arg} | Screen argument: {screen_arg} | Action: {action}")

    if node_arg == "all" and screen_arg == "all":
        if action == "close":
            close_konsoles()
        elif action == "check":
            check_konsoles()
        elif action == "open":
            open_konsoles()

    # if "close" in sys.argv:
    #     close_konsoles()

    # if "check" in sys.argv:
    #     check_konsoles()

    # if "open" in sys.argv:
    #     open_konsoles()

    # # node-specific logic
    # if "node" in sys.argv:
    #     for index, mbs_node in enumerate(sys.argv):
    #         if mbs_node in NODES:
    #             print(f"{index}: {mbs_node}")
    #             login=f"{USERNAME}@{mbs_node}"
    #             for key_screen, screen in enumerate(SCREENS):
    #                 title = f"{login}_{screen}"
    #                 open_konsol(title, login, screen)
    #             break
    #     else:
    #         sys.stderr.write(f"Node {mbs_node} not found in {NODES}\n")

    #     # open_konsoles()

