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
import subprocess
from loguru import logger

###############################################################################
def read_fpga_temp(sfp, dev):
    """Read value from FPGA temperature sensor."""
    out = subprocess.Popen(["gosipcmd", "-r", "-x", f"{sfp}", f"{dev}", "0x20005c"], stdout=subprocess.PIPE).communicate()[0][2:-2]

    bin_str = "{0:016b}".format(int(out, 16))

    val_int = int(bin_str[-16:], 2)

    t_deg = round(val_int*503.975/4096-273.15,1)

    return t_deg

###############################################################################
def read_sipm_temp(sfp, dev):
    """Read value from on-board temperature sensor (TMP117)."""

    # Read value from on-board temperature sensor (TMP117)
    #out = Popen(["gosipcmd", "-w", "-x", sfp, dev, "0x200074"], stdout=PIPE).communicate()[0][2:-2]
    #sleep 0.05
    out = subprocess.Popen(["gosipcmd", "-r", "-x", f"{sfp}", f"{dev}", "0x200064"], stdout=subprocess.PIPE).communicate()[0][2:-2]
    bin_str = "{0:016b}".format(int(out, 16))
    val_int = int(bin_str, 2)
    t_deg = round(val_int*0.0078125,1)
    print("SciFi_652 SiPM sensor: {0}".format(t_deg))

    return t_deg

###############################################################################
###############################################################################
def main():
    """Read temperatures from all SciFi boards."""
    list_sft_board = [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 1),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1),
    ]

    temp_dictionary = {"SFP": 0, "DEV": 0, "FPGA": 0.0, "SiPM": 0.0}
    temp_list = [
        # {'SFP': 0, 'DEV': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 0, 'DEV': 1, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 0, 'DEV': 2, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 0, 'DEV': 3, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 0, 'DEV': 4, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 0, 'DEV': 5, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 1, 'DEV': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 1, 'DEV': 1, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 2, 'DEV': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 2, 'DEV': 1, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 2, 'DEV': 2, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 2, 'DEV': 3, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 2, 'DEV': 4, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 2, 'DEV': 5, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 3, 'DEV': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        # {'SFP': 3, 'DEV': 1, 'FPGA': 0.0, 'SiPM': 0.0},
    ]

    for sfp, dev in list_sft_board:
        temp_fpga = read_fpga_temp(sfp, dev)
        temp_sipm = read_sipm_temp(sfp, dev)
        temp_dictionary = {"SFP": sfp, "DEV": dev, "FPGA": temp_fpga, "SiPM": temp_sipm}
        logger.info(f"Read temperatures for SFP {sfp}, DEV {dev}: FPGA={temp_fpga}, SiPM={temp_sipm}")
        temp_list.append(temp_dictionary.copy())
        temp_dictionary.clear()  # Clear the dictionary for the next iteration

    for temp in temp_list:
        print(temp)

###############################################################################
###############################################################################
###############################################################################
if __name__ == "__main__":

    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--sfp", "-s", help="SFP number [0...3]")
    parser.add_argument("--dev", "-d", help="device number [0...5]")

    args = parser.parse_args()

    if args.sfp is None or args.dev is None:
        # If no arguments are provided, read temperatures from all SciFi boards
        main()
    else:
        # If arguments are provided, read temperatures from the specified SFP and device
        sfp = int(args.sfp)
        dev = int(args.dev)
        fpga_temp = read_fpga_temp(sfp, dev)
        sipm_temp = read_sipm_temp(sfp, dev)
        print(f" --sfp {sfp} --dev {dev} --fpga_temp {fpga_temp} --sipm_temp {sipm_temp}")