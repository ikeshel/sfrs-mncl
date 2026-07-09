#!/usr/bin/env python3

__author__     = "Irakli Keshelashvili"
__copyright__  = "Copyright 2026, The Super FRS Project"
__version__    = "0.0.1"
__maintainer__ = "Irakli Keshelashvili"
__email__      = "i.keshelashvili@gsi.de"
__status__     = "Production"

'''
    Script to read FPGA and SiPM temperatures from SciFi boards.
    Modification of Michael Heils read_temp_sfrs.sh and read_temp_scifi.py; 
    Thanks to Michael Heils for the original scripts. ;)
'''
import argparse
from subprocess import call, Popen, PIPE

#=============================================================================
def read_fpga_temp(sfp, board):
    # Read value from FPGA temperature sensor
    out = Popen(["gosipcmd", "-r", "-x", sfp, board, "0x20005c"], stdout=PIPE).communicate()[0][2:-2]
    bin_str = "{0:016b}".format(int(out, 16))
    val_int = int(bin_str[-16:], 2)
    t_deg = round(val_int*503.975/4096-273.15,1)
    return t_deg

#=============================================================================
def read_sipm_temp(sfp, board):
    # Read value from on-board temperature sensor (TMP117)
    out = Popen(["gosipcmd", "-r", "-x", sfp, board, "0x200064"], stdout=PIPE).communicate()[0][2:-2]
    bin_str = "{0:016b}".format(int(out, 16))
    val_int = int(bin_str, 2)
    t_deg = round(val_int*0.0078125,1)
    return t_deg

#=============================================================================
#=============================================================================
def main():
    list_sft_board = [
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (0, 5),
    (1, 0),
    (1, 1),
    (2, 0),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (3, 0),
    (3, 1),
    ]

    for sfp, board in list_sft_board:
        fpga_temp = read_fpga_temp(sfp, board)
        sipm_temp = read_sipm_temp(sfp, board)
        print(f" --sfp {sfp} --board {board} --fpga_temp {fpga_temp} --sipm_temp {sipm_temp}")

#=============================================================================
# main 
#=============================================================================
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--sfp", '-s', help="SFP number [0...3]")
    parser.add_argument("--board", '-b', help="device number [0...5]")

    args = parser.parse_args()
    if args.sfp is None or args.board is None:
        main()
    else:
        sfp = int(args.sfp)
        board = int(args.board)
        fpga_temp = read_fpga_temp(sfp, board)
        sipm_temp = read_sipm_temp(sfp, board)
        print(f" --sfp {sfp} --board {board} --fpga_temp {fpga_temp} --sipm_temp {sipm_temp}")