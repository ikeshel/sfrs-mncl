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
import re
import subprocess
# from loguru import #logger


def read_fpga_temp(sfp, board):
    """Read value from FPGA temperature sensor."""
    result = subprocess.run(
        ["gosipcmd", "-r", "-x", str(sfp), str(board), "0x20005c"],
        stdout=subprocess.PIPE,
        text=True,
        check=True
    )
    out = result.stdout.strip()[2:-2]
    bin_str = f"{int(out, 16):016b}"
    val_int = int(bin_str[-16:], 2)
    t_deg = round(val_int * 503.975 / 4096 - 273.15, 1)

    # out = subprocess.Popen(["gosipcmd", "-r", "-x", f"{sfp}", f"{board}", "0x20005c"], stdout=subprocess.PIPE).communicate()[0][2:-2]
    # print(out)
    # bin_str = "{0:016b}".format(int(out, 16))
    # val_int = int(bin_str[-16:], 2)
    # t_deg = round(val_int*503.975/4096-273.15,1)
    # print("SciFi_652 FPGA: {0}".format(t_deg))

    return t_deg


def read_sipm_temp(sfp, board):
    """Read value from on-board temperature sensor (TMP117)."""
    result = subprocess.run(
        ["gosipcmd", "-r", "-x", str(sfp), str(board), "0x200064"],
        stdout=subprocess.PIPE,
        text=True,
        check=True
    )

    #logger.debug(f"result.stdout={result.stdout.strip()}")
    
    out = result.stdout.strip()[2:-2]
    #logger.debug(f"out={out}")

    bin_str = f"{int(out, 16):016b}"
    #logger.debug(f"bin_str={bin_str}")

    val_int = int(bin_str, 2)
    #logger.debug(f"val_int={val_int}")

    t_deg = round(val_int * 0.0078125, 1)
    #logger.debug(f"t_deg={t_deg}")
    return t_deg


def main():
    """Read temperatures from all SciFi boards."""
    list_sft_board = [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 1),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1),
    ]

    SSH_COMMAND=''
    for sfp, board in list_sft_board:
        SSH_COMMAND+=f"/mbs/driv/mbspexV3_5.10-64_DEB/bin/gosipcmd -rxd {sfp} {board} 0x20005c;" # FPGA temperature
        SSH_COMMAND+=f"/mbs/driv/mbspexV3_5.10-64_DEB/bin/gosipcmd -rxd {sfp} {board} 0x200064;" # SiPM temperature
    
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=1", "ikeshel@X86L-253", SSH_COMMAND],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
# SFP: 0x0 Module: 0x0 Address: 0x20005c  Data: 0x105009f9 
# SFP: 0x0 Module: 0x0 Address: 0x200064  Data: 0x115c 
# SFP: 0x0 Module: 0x1 Address: 0x20005c  Data: 0x107009f7 
# SFP: 0x0 Module: 0x1 Address: 0x200064  Data: 0x1171 
# SFP: 0x0 Module: 0x2 Address: 0x20005c  Data: 0x105009f6 
# SFP: 0x0 Module: 0x2 Address: 0x200064  Data: 0x1174 
# SFP: 0x0 Module: 0x3 Address: 0x20005c  Data: 0x105009db 
# SFP: 0x0 Module: 0x3 Address: 0x200064  Data: 0x1165 
# SFP: 0x0 Module: 0x4 Address: 0x20005c  Data: 0x105009e9 
# SFP: 0x0 Module: 0x4 Address: 0x200064  Data: 0x115a 
# SFP: 0x0 Module: 0x5 Address: 0x20005c  Data: 0x105009e7 
# SFP: 0x0 Module: 0x5 Address: 0x200064  Data: 0x114d 
# SFP: 0x1 Module: 0x0 Address: 0x20005c  Data: 0x10700a11 
# SFP: 0x1 Module: 0x0 Address: 0x200064  Data: 0x11d5 
# SFP: 0x1 Module: 0x1 Address: 0x20005c  Data: 0x10500a22 
# SFP: 0x1 Module: 0x1 Address: 0x200064  Data: 0x11a7 
# SFP: 0x2 Module: 0x0 Address: 0x20005c  Data: 0x105009ff 
# SFP: 0x2 Module: 0x0 Address: 0x200064  Data: 0x11ab 
# SFP: 0x2 Module: 0x1 Address: 0x20005c  Data: 0x105009f5 
# SFP: 0x2 Module: 0x1 Address: 0x200064  Data: 0x11be 
# SFP: 0x2 Module: 0x2 Address: 0x20005c  Data: 0x105009e9 
# SFP: 0x2 Module: 0x2 Address: 0x200064  Data: 0x11b8 
# SFP: 0x2 Module: 0x3 Address: 0x20005c  Data: 0x105009ed 
# SFP: 0x2 Module: 0x3 Address: 0x200064  Data: 0x11a9 
# SFP: 0x2 Module: 0x4 Address: 0x20005c  Data: 0x105009f3 
# SFP: 0x2 Module: 0x4 Address: 0x200064  Data: 0x11ae 
# SFP: 0x2 Module: 0x5 Address: 0x20005c  Data: 0x105009f3 
# SFP: 0x2 Module: 0x5 Address: 0x200064  Data: 0x11a0 
# SFP: 0x3 Module: 0x0 Address: 0x20005c  Data: 0x10500a1f 
# SFP: 0x3 Module: 0x0 Address: 0x200064  Data: 0x1163 
# SFP: 0x3 Module: 0x1 Address: 0x20005c  Data: 0x10500a37 
# SFP: 0x3 Module: 0x1 Address: 0x200064  Data: 0x118e 

    temp_dictionary = {"SFP": 0, "Module": 0, "FPGA": 0.0, "SiPM": 0.0}
    temp_list = [
        {'SFP': 0, 'Module': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 0, 'Module': 1, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 0, 'Module': 2, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 0, 'Module': 3, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 0, 'Module': 4, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 0, 'Module': 5, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 1, 'Module': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 1, 'Module': 1, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 2, 'Module': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 2, 'Module': 1, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 2, 'Module': 2, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 2, 'Module': 3, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 2, 'Module': 4, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 2, 'Module': 5, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 3, 'Module': 0, 'FPGA': 0.0, 'SiPM': 0.0},
        {'SFP': 3, 'Module': 1, 'FPGA': 0.0, 'SiPM': 0.0},
    ]

    # Parse output line by line
    for line in result.stdout.strip().split('\n'):
        temp_dictionary = {"SFP": 0, "Module": 0, "FPGA": 0.0, "SiPM": 0.0}  # Reset dictionary for each line
        if line.strip():
            # Extract SFP, Module, Address, and Data
            parts = line.split()
            print(f"parts={parts}")
            
            sfp   = int(parts[1], 16)
            board = int(parts[3], 16)
            
            # Determine if it's FPGA or SiPM temperature
            if parts[5] == "0x20005c":
                temp_dictionary["FPGA"] = parts[7]
            elif parts[5] == "0x200064":
                temp_dictionary["SiPM"] = parts[7]
            
            # print(f"SFP: {temp_dictionary['SFP']} Module: {temp_dictionary['Module']} {temp_dictionary['FPGA']} {temp_dictionary['SiPM']}")
            temp_list.append(temp_dictionary.copy())  # Append a copy of the dictionary to the list

    for temp in temp_list:
        print(temp)

    if result.stderr:
        print(result.stderr)




        # fpga_temp = read_fpga_temp(sfp, board)
        # sipm_temp = read_sipm_temp(sfp, board)
        # print(f" --sfp {sfp} --board {board} --fpga_temp {fpga_temp} --sipm_temp {sipm_temp}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sfp", "-s", help="SFP number [0...3]")
    parser.add_argument("--board", "-b", help="device number [0...5]")

    args = parser.parse_args()
    if args.sfp is None or args.board is None:
        main()
    else:
        sfp = int(args.sfp)
        board = int(args.board)
        fpga_temp = read_fpga_temp(sfp, board)
        sipm_temp = read_sipm_temp(sfp, board)
        print(f" --sfp {sfp} --board {board} --fpga_temp {fpga_temp} --sipm_temp {sipm_temp}")