
#!/bin/bash

# i.keshelashvili@gsi.de
# This script demonstrates how to create new tabs in Konsole using D-Bus.

konsole --title "mbs" -p tabtitle="mbs" -e bash &
PID=$!

sleep 0.5

service="org.kde.konsole-$PID"
session=$(qdbus "$service" /Windows/1 newSession)
echo "Service: $service"
echo "Session: $session"
session=$(qdbus "$service" /Windows/1 newSession)
echo "Service: $service"
echo "Session: $session"
# qdbus "$service" "$session" setTitle 0 "mbs"
# qdbus "$service" "$session" setTitle 0 "web"
# qdbus "$service" "$session" runCommand "echo 'Hello from mbs!'"