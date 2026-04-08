#!/bin/bash

# Get screen resolution
resolution=$(xdpyinfo | grep dimensions | awk '{print $2}')
xx=$(echo "$resolution" | cut -d'x' -f1) # Get width
yy=$(echo "$resolution" | cut -d'x' -f2) # Get height
nn=$(xrandr --query | grep " connected" | wc -l) # Get number of connected monitors
echo "Screen resolution: ${xx}x${yy}, Monitors: ${nn}"
# Desired window size
win_w=$((xx / 2 / nn))
win_h=$((yy / 2))

# Compute top-right position
pos_x=$((xx - win_w))
pos_y=0

# Start konsole with tabs
konsole \
  --new-tab -p tabtitle="mbs" -e bash -lc 'ssh -Y ikeshel@X86L-132 -t "screen -r mbs"' \
  --new-tab -p tabtitle="web" -e bash -lc 'ssh -Y ikeshel@X86L-132 -t "screen -r web"' &

# Give it time to appear, then move it
sleep 1
wmctrl -r :ACTIVE: -e 0,$pos_x,$pos_y,$win_w,$win_h