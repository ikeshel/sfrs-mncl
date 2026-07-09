#!/usr/bin/env python3

import argparse
import sys
from subprocess import call, Popen, PIPE

def read_fpga_temp(sfp, board):
    # Read value from FPGA temperature sensor
    out = Popen(["gosipcmd", "-r", "-x", sfp, board, "0x20005c"], stdout=PIPE).communicate()[0][2:-2]
    bin_str = "{0:016b}".format(int(out, 16))
    val_int = int(bin_str[-16:], 2)
    t_deg = round(val_int*503.975/4096-273.15,1)
    return t_deg

def read_sipm_temp(sfp, board):
    # Read value from on-board temperature sensor (TMP117)
    #out = Popen(["gosipcmd", "-w", "-x", sfp, board, "0x200074"], stdout=PIPE).communicate()[0][2:-2]
    #sleep 0.05
    out = Popen(["gosipcmd", "-r", "-x", sfp, board, "0x200064"], stdout=PIPE).communicate()[0][2:-2]
    bin_str = "{0:016b}".format(int(out, 16))
    val_int = int(bin_str, 2)
    t_deg = round(val_int*0.0078125,1)
    return t_deg


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





# # Read value from FEB temperature sensor (TMP117)
# #out = Popen(["gosipcmd", "-w", "-x", sfp, dev, "0x200074"], stdout=PIPE).communicate()[0][2:-2]
# #sleep 0.05
# out = Popen(["gosipcmd", "-r", "-x", sfp, dev, "0x200068"], stdout=PIPE).communicate()[0][2:-2]
# bin_str = "{0:016b}".format(int(out, 16))
# val_int = int(bin_str, 2)
# t_deg = round(val_int*0.0078125,1)
# print("SciFi FEB sensor: {0}".format(t_deg))



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--sfp", help="SFP number [0...3]")
    parser.add_argument("--board", help="device number [0...5]")
    args = parser.parse_args()

    sfp = int(args.sfp)
    board = int(args.board)

    main()
    