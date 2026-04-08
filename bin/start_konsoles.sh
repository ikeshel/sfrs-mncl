#!/bin/bash

# Get total screen resolution
resolution=$(xdpyinfo | awk '/dimensions:/ {print $2}')
xx=$(echo "$resolution" | cut -d'x' -f1)
yy=$(echo "$resolution" | cut -d'x' -f2)

# Number of connected monitors
nn=$(xrandr --query | grep " connected" | wc -l)

echo "Screen resolution: ${xx}x${yy}, Monitors: ${nn}"

# Decoration compensation for KDE titlebar/frame
frame_y=30

# Per-monitor size estimate
screen_w=$((xx / nn))
screen_h=$yy

# Desired outer window size
win_w=$((screen_w / 4)) # of one monitor's width
win_h=$((screen_h / 2)) # half of one monitor's height, minus frame compensation

sleep_time=1

username="ikeshel"
echo "Current user: $username"

# List of logins
logins=(
  "$username@X86L-132"
  "$username@X86L-170"
  # "$username@X86L-253"
)

tabs=(
  "mbs"
  "web"
)

# Start konsole windows for each login
nn=0
for login in "${logins[@]}"; do
  for tab in "${tabs[@]}"; do
    # pos_x=$((nn*win_w))
    # pos_y=$(((nn % 2+1) * (win_h + frame_y)))
    pos_x=$((nn*20))
    pos_y=$((nn*10))

    wind_title="${login}_${tab}"
    echo "Calculated position for $wind_title: x=$pos_x, y=$pos_y"
    # konsole --new-tab -p tabtitle="${login}_$tab" -e bash -lc "ssh -Y $login -t 'screen -r $tab'" &
    
    cmd="konsole --new-tab -p tabtitle=\"name_${nn}\" -e bash -lc \"ssh -Y $login -t 'screen -r $tab'\" &"
    echo "command: $cmd"
    sleep $sleep_time
    # wmctrl -r :ACTIVE: -e 0,$pos_x,$pos_y,$win_w,$win_h
    wmctrl -r "name_${nn}" -e 0,$pos_x,$pos_y,$win_w,$win_h

    nn=$((nn + 1))
  done
done