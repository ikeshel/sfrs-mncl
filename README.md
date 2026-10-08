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

Other entry points include `super_frs_manager.py`, `tamex.py`, `mdpp.py`,
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
