# mncl (MBS Node Control Library)

Python/PyQt6 desktop tools for managing Super-FRS MBS acquisition nodes,
controlling detector electronics, and monitoring EPICS process variables.

Author: i.keshelashvili@gsi.de

## Desktop prerequisites

The installer targets Debian/Ubuntu with APT and sudo access. Package names
were checked on Debian 13; other releases may require adjustments.
Use an existing graphical desktop session. Console positioning uses X11 tools
(`wmctrl`, `xdpyinfo`, and `xrandr`); KDE Plasma supplies the panel information
queried through `qdbus6`. Full window control under Wayland is not guaranteed.
The installer does not install or configure a desktop session.

Dependencies are maintained in two commented lists:

- [apt_dependencies.txt](apt_dependencies.txt): desktop system tools and runtime libraries.
- [python_dependencies.txt](python_dependencies.txt): Python packages installed with pip.

`apt_dependencies.txt` is a project convention, read by our installer, rather
than an APT-native requirements format. Keep one package name per line; comments
and blank lines are supported. Python packages belong in the pip list, including
`subprocess-tee` (called `python3-subprocess-tee` in Debian/Ubuntu).

## Installation

From the repository root, preview the commands first if desired:

```bash
./scripts/install_dependencies.sh --dry-run
```

Install as your normal user:

```bash
./scripts/install_dependencies.sh
source .venv/bin/activate
```

The script uses sudo for APT, which presents its normal installation prompt.
It creates or reuses `.venv`, installs the Python dependencies there, and runs
`pip check`. It can be invoked from another directory; paths are resolved from
its location. Re-running it reuses installed packages, but the dependency
lists do not pin versions and are not a reproducible lockfile.

To update only the Python dependencies later:

```bash
.venv/bin/python -m pip install -r python_dependencies.txt
```

## Configuration and launch

Review `config/mbs_nodes.yaml` and `config/node_screens.yaml` before connecting.
Console helpers also use `config/list_of_nodes.conf` and
`config/list_of_screens.conf`; keep these consistent with the YAML configuration.
Some scripts contain site-specific usernames, hostnames, and paths that must be
adapted to your installation.

Run applications from the repository root so relative configuration and image
paths resolve correctly:

```bash
source .venv/bin/activate
python mbs_node_manager.py
```

The default manager window shows the TimeSorter node. Its bottom row has three
equal-width buttons, **MUSIC**, **PLSCI**, and **SCIFI**, which open the respective
node windows. Clicking a button again raises the existing window.
Each detector window has a **TimeSorter** action in its top menu bar to open
the main window or bring it forward if it is already open.

To select one or more windows directly (names are case-insensitive):

```bash
python mbs_node_manager.py MUSIC
python mbs_node_manager.py PLSCI
python mbs_node_manager.py SCIFI
./mbs_node_manager.py music plsci
python mbs_node_manager.py all
```

`all` opens four separate windows: TimeSorter, MUSIC, PLSCI, and SCIFI.
Multiple names open only the requested systems; repeated names reuse the same window.
Nodes are grouped from their existing `directory` or `node_name` values in
`config/mbs_nodes.yaml`, including numbered names such as `SCIFI3` and `SCIFI4`.
The equipment label (`host_name`, with `text35` / `X86-XXX` as fallbacks) in `intel_music.svg`
and `intel_x86.svg` displays each node's `host_name` at runtime. The shared SVG
files remain unchanged. The dashboard link shows `sfrs_chamber` from the node
configuration, falling back to the directory for nodes such as TimeSorter that
have no chamber. The full directory and hostname remain available in its tooltip.
The SVG text object `whiterabbit_id` (also accepting `whiterubbit_id`) shows
`WR: <WR_SUBSYSTEM_ID>` from the node's
MURX configuration, replacing the separate subsystem label. It is hidden for TimeSorter.
The SVG element `led_power` displays SSH reachability: green/light green when
reachable, red/pink when unreachable. It replaces the separate status dot and
scales with the illustration; this is connectivity status, not a hardware power measurement.
Each window's menus control only its own nodes and its position is saved
separately. Normal window resizing preserves the width-to-height ratio of its
saved size. Without a saved geometry file, the initial layout uses each node
SVG's original dimensions, plus the menu, margins, spacing and launcher buttons.
That initial window ratio is then preserved. Dragging a side adjusts the
other dimension automatically; maximized/fullscreen windows follow the desktop.
On X11, the window manager enforces this ratio directly during resizing. Other
platforms use a deferred size correction. SVG backgrounds are repainted during
resizing so previous image positions do not leave fragments behind.
Closing one window leaves the others open; it can be reopened from
TimeSorter. Opening a window does not automatically start acquisition processes.

Run `python super_frs_manager.py` for the clickable SuperFRS diagram. Clicking a
named detector rectangle opens a manager for that node only; clicking again raises
its existing window. SVG object IDs match the `directory` fields in
`config/mbs_nodes.yaml`; Inkscape labels are also supported when the object has a
generated ID such as `rect1-6`, including the PLSCI regions. Hovering shows the node name and hostname; objects without
a matching configuration report that they are not configured. Each individual
node window saves its own geometry and runs in a separate process. Closing the
overview leaves all node managers and their dashboards open. Reopening the overview
and clicking a detector brings its existing manager forward. The **Opened nodes**
menu controls running individual node managers for this repository and desktop session.
Each node manager has separate log files under `logs/`.
The **Time sorter** action in the overview's top menu bar opens its independent
main window or brings it forward if already running.
The overview's **MUSIC**, **PLSCI**, and **SCIFI** menus each have **Open all nodes**,
**Close all nodes**, and a checkbox for every configured node. Checking an item
opens its individual manager; unchecking closes that manager and its dashboard.
The checkboxes update when managers are opened or closed separately.
Console checkboxes also refresh every second using the local window titles
(`ikeshel@<host>_<screen>`), including consoles opened or closed outside the manager.
The **Open/Close node konsoles** and **Open/Close all konsoles** items are checked
only when all console windows they control are open. Window checks run in the
background through `wmctrl`; a failed check leaves the previous state unchanged.

An individual manager can also be launched directly:

```bash
./mbs_node_manager.py --node FHF1_SCIFI3
```

Other entry points include `tamex.py`, `mdpp.py`,
`scifi.py`, and `pulser.py`. For example:

```bash
python pulser.py --node x86l-132
```

The existing desktop launchers assume `$HOME/sfrs-mncl` and use the system
Python through the scripts' shebangs. To use `.venv` from a desktop launcher,
set its `Exec` to the absolute path of `.venv/bin/python` followed by the
application's absolute path, and its `Path` to the repository root.

## Remote MBS nodes and hardware

The desktop installer does not provision remote acquisition nodes. They need:

- An SSH server, a configured login account, and SSH access from the desktop.
- GNU Screen (`screen`) and the C shell required by remote helper scripts.
- The site-specific MBS/DABC software, configuration, and hardware drivers.
- `gosipcmd` for register access; its path is configured in `package/ssh_commander.py`.
- The relevant EPICS IOCs and process variables for monitoring scripts and panels.

Remote scripts also assume particular repository and detector directories.
Check these paths and the EPICS network setup with the acquisition environment.
Tools such as `gosipcmd` and the MBS installation are supplied by that environment,
not by the desktop dependency lists.

The legacy demonstration `scripts/dbus_konsole_tabs.sh` calls `qdbus`, whereas
`konsole_manager.py` uses `qdbus6`. The default dependency list supplies `qdbus6`;
adapt the legacy demo or install the matching older tool if you need it.

## Regenerating UI code

Activate `.venv` and run `make` to regenerate the Python UI modules from the
Qt Designer `.ui` files in `gui/` using `pyuic6`:

```bash
source .venv/bin/activate
make
```
