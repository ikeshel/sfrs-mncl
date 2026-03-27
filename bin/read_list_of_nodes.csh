#!/bin/csh

# i.keshelashvili@gsi.de

set list_of_nodes = "list_of_nodes.conf"

# Check if the list_of_nodes.csv file exists
if (! -f $list_of_nodes) then
    echo "\033[5;31mError: $list_of_nodes file not found\033[0m"
    exit 1
endif

# Read the list of nodes and names from the file
set list_nodes = ()
set list_names = ()
foreach line ("`cat $list_of_nodes`")
    if ("$line" == "") continue  # Skip empty lines
    if ("$line" =~ \#*) continue # Skip comment lines
    set line = `echo $line | tr -d '\r' | tr -d '\n' | tr -s ' '` # Remove carriage returns, newlines, and extra spaces
    set line = ($line) # Split the line into an array
    set node = $line[1] # First element is the node
    set name = $line[2] # Second element is the name
    set list_nodes = ($list_nodes $node)
    set list_names = ($list_names $name)
end

# If -v flag is provided, print the list of nodes and names
if ($#argv > 0) then
    foreach arg ($argv)
        if ("$arg" == "-v") then
            echo "Successfully read from $list_of_nodes"
            echo "Nodes: $#list_nodes"
            foreach node ($list_nodes)
                echo $node
            end
            break
        endif
    end
    endif
endif

