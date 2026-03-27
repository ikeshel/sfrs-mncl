#!/bin/csh

# i.keshelashvili@gsi.de

set list_of_screens = "list_of_screens.csv"

if (! -f $list_of_screens) then
    echo "\033[5;31mError: list_of_screens.csv file not found\033[0m"
    exit 1
endif

