#!/bin/bash

# Get total screen resolution
resolution=$(xdpyinfo | awk '/dimensions:/ {print $2}')
xx=$(echo "$resolution" | cut -d'x' -f1)
yy=$(echo "$resolution" | cut -d'x' -f2)

# Number of connected monitors
nn=$(xrandr --query | grep " connected" | wc -l)

echo "Screen resolution: ${xx}x${yy}, Monitors: ${nn}"

# Decoration compensation for KDE titlebar/frame
frame_y=25

gap_x=10
gap_y=10

# Per-monitor size estimate
screen_w=$((xx / nn))
screen_h=$yy

# Desired outer window size
win_w=$((screen_w / 2 - gap_x)) # of one monitor's width
win_h=$((screen_h / 2 - frame_y - gap_y)) # half of one monitor's height, minus frame compensation

sleep_time=1

username="ikeshel"
echo "Current user: $username"

# List of logins
logins=(
  "$username@X86L-170"
  "$username@X86L-132"
  "$username@X86L-253"
  "$username@X86L-260"
  "$username@X86L-261"  
)

tabs=(
  "mbs"
  "web"
)

# Start konsole windows for each login
nx=0
ny=0
for login in "${logins[@]}"; do
  pos_x=$((nx * (win_w+gap_x)))

  for tab in "${tabs[@]}"; do
    pos_y=$((ny * (win_h - frame_y + gap_y)))
    
    wind_title="${login}_${tab}"
    echo "Calculated position for $wind_title: x=$pos_x, y=$pos_y"
    
    cmd="konsole -p tabtitle=\"$wind_title\" -e bash -lc 'ssh $login -t \"./sfrs-mncl/bin/check_screens.csh;screen -d $tab;screen -r $tab\"'"
    
    echo "command: $cmd"
    eval $cmd &

    sleep $sleep_time
    # wmctrl -r :ACTIVE: -e 0,$pos_x,$pos_y,$win_w,$win_h
    wmctrl -r "$wind_title" -e 0,$pos_x,$pos_y,$win_w,$win_h

    ny=$((ny + 1))
  done
  ny=0
  nx=$((nx + 1))
done