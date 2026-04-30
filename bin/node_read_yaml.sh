#!/bin/bash

# Install yq if needed: sudo apt-get install yq

YAML_FILE="config/mbs_nodes.yaml"

count=$(yq '.nodes | length' $YAML_FILE)

for i in $(seq 0 $((count - 1))); do
    echo "--- Node $((i + 1)) ---"
    echo "host_name:  $(yq ".nodes[$i].host_name" $YAML_FILE)"
    echo "node_name:  $(yq ".nodes[$i].node_name" $YAML_FILE)"
    echo "directory:  $(yq ".nodes[$i].directory" $YAML_FILE)"
    echo "active:     $(yq ".nodes[$i].active"    $YAML_FILE)"
    echo "pc_type:    $(yq ".nodes[$i].pc_type"   $YAML_FILE)"
    echo ""
done