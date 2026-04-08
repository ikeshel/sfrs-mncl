#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
script to open konsole windows for each login and tab, and arrange them on the screen
'''

import subprocess
import time
import shlex
from loguru import logger
import sys


USERNAME = "ikeshel"

LOGINS = [
    f"{USERNAME}@x86l-132",
    f"{USERNAME}@x86l-170",
    f"{USERNAME}@x86l-253",
]

TABS = ["mbs", "web"]

SLEEP_TIME = 0.3

#=============================================================================
def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

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
    ret = run(["wmctrl", "-r", title, "-e", f"0,{x},{y},{w},{h}"])
    if ret.returncode != 0:
        logger.error(f"Failed to move window {title}: {ret.stderr.strip()}")

#=============================================================================
def open_konsole(title:str, login:str, tab:str)->None:
    remote_cmd = (
        f"screen -dr {shlex.quote(tab)} "
        f"|| screen -r {shlex.quote(tab)} "
        f"|| echo 'screen session {tab} not found on {login}'"
    )

    local_cmd = f"ssh -Y {shlex.quote(login)} -t {shlex.quote(remote_cmd)}; exec bash"

    subprocess.Popen([
        "konsole",
        "--separate",
        "--title", title,
        "-p", f"tabtitle={title}",
        "--hold",
        "-e", "bash", "-lc", local_cmd,
    ])

#==============================================================================
def check_konsoles()->None:
    for login in LOGINS:
        for tab in TABS:
            title = f"{login}_{tab}"
            if window_exists(title):
                logger.info(f"Found window: {title}")
            else:
                logger.warning(f"Window not found: {title}")

#==============================================================================
def close_all()->None:
    for login in LOGINS:
        for tab in TABS:
            title = f"{login}_{tab}"
            if window_exists(title):
                logger.info(f"Closing {title}")
                run(["wmctrl", "-c", title])
            else:
                logger.info(f"Window not found, cannot close: {title}")

def open_konsoles()->None:
    
    xx, yy = get_screen_resolution()
    logger.info(f"Screen resolution: {xx}x{yy}")

    monitors = get_monitor_count()
    logger.info(f"Monitors detected: {monitors}")

    # debug_titles()

    KDE_menu_bar_height = 40
    KDE_top_bar_height = 30
    screen_w = xx // monitors
    screen_h = yy - KDE_menu_bar_height

    win_w = screen_w // 2
    win_h = screen_h // 2 - KDE_menu_bar_height

    for key, login in enumerate(LOGINS):
        pos_x = key*win_w

        for tab_key, tab in enumerate(TABS):
            title = f"{login}_{tab}"

            if window_exists(title):
                logger.info(f"Already running: {title}")
                continue
            
            pos_y = tab_key * screen_h // 2 + 30

            logger.info(f"Opening {login} at x={pos_x} y={pos_y}")
            open_konsole(title, login, tab)

            time.sleep(SLEEP_TIME)
            move_window(title, pos_x, pos_y, win_w, win_h)

#
if __name__ == "__main__":

    if "close" in sys.argv:
        close_all()

    elif "check" in sys.argv:
        check_konsoles()

    else:        
        open_konsoles()