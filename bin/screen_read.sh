#!/bin/bash

SCREENS_FILE='config/node_screens.yaml'

# Skip comment lines (#) and empty lines, then parse
while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^#  ]] && continue
    [[ -z "$line"     ]] && continue

    # Extract node name (first word) and description (text inside quotes)
    node=$(echo "$line" | awk '{print $1}')
    desc=$(echo "$line" | grep -o "'[^']*'" | tr -d "'")

    echo "screen=$node  desc=$desc"

done < "$SCREENS_FILE"