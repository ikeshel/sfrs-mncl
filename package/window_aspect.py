"""Ask an X11 window manager to constrain resizing before drawing the window."""

from Xlib import Xutil
from Xlib.display import Display


def set_x11_aspect_ratio(window_id, width, height):
    display = Display()
    try:
        window = display.create_resource_object('window', window_id)
        hints = window.get_wm_normal_hints()
        if hints is None:
            hints = {'flags': 0}
        # Preserve Qt's existing minimum/maximum sizes and other window hints.
        hints['flags'] |= Xutil.PAspect | Xutil.PBaseSize
        hints['min_aspect'] = (width, height)
        hints['max_aspect'] = (width, height)
        hints['base_width'] = 0
        hints['base_height'] = 0
        window.set_wm_normal_hints(hints)
        display.sync()
    finally:
        display.close()
