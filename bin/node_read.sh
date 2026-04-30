#!/bin/bash

YAML_FILE='config/mbs_nodes.yaml'

hosts=$(grep 'host_name:' "$YAML_FILE"  | awk -F': ' '{print $2}' | tr -d "'")
names=$(grep 'node_name:' "$YAML_FILE"  | awk -F': ' '{print $2}' | tr -d "'")
dirs=$(grep 'directory:'  "$YAML_FILE"  | awk -F': ' '{print $2}' | tr -d "'")
actives=$(grep 'active:'  "$YAML_FILE"  | awk -F': ' '{print $2}' | tr -d "'")
types=$(grep 'pc_type:'   "$YAML_FILE"  | awk -F': ' '{print $2}' | tr -d "'")

paste <(echo "$hosts") <(echo "$names") <(echo "$dirs") <(echo "$actives") <(echo "$types") \
| while IFS=$'\t' read -r host name dir active pc_type; do
    echo "host=$host  name=$name  dir=$dir  active=$active  type=$pc_type"
done