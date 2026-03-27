#!/bin/csh

# i.keshelashvili@gsi.de

set conf_file = "list_of_screens.conf"

# If -v flag is provided, print the list of nodes and names
set vv = 0 # do not use var name 'verbouse' because it is csh reserved word

if ($#argv > 0) then
    foreach arg ($argv)
        if ("$arg" == "-v") then
            set vv = 1
            echo "\033[32mVerbose mode enabled\033[0m"
            break
        endif
    end
endif


# Check if the list_of_nodes.csv file exists
if (! $?conf_file) then
    echo "\033[5;31mError: conf_file variable is not set\033[0m"
    exit 1
endif

# Read the list of nodes and names from the file
set list_paras = ()
set list_names = ()
foreach line ("`cat $conf_file`")
    if ("$line" == "") continue  # Skip empty lines
    if ("$line" =~ \#*) continue # Skip comment lines
    set line = `echo $line | tr -d '\r' | tr -d '\n' | tr -s ' '` # Remove carriage returns, newlines, and extra spaces
    set line = ($line) # Split the line into an array
    set para = $line[1] # First element is the para
    set name = $line[2] # Second element is the name
    if ($vv) then
        echo "Read para: $para, name: $name"
    endif
    set list_paras = ($list_paras $para)
    set list_names = ($list_names $name)
end

