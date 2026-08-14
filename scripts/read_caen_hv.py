#!/usr/bin/env python3

import time
import serial

PORT = "/dev/ttyACM0"   # change if necessary
BOARD_ADDRESS = 0
CHANNEL = 1             # CAEN channels are CH0, CH1, CH2, CH3


def read_parameter(device, parameter):
    command = (
        f"$BD:{BOARD_ADDRESS:02d},"
        f"CMD:MON,CH:{CHANNEL},PAR:{parameter}\r\n"
    )

    device.reset_input_buffer()
    device.write(command.encode("ascii"))
    device.flush()

    while True:
        raw = device.readline()

        if not raw:
            raise TimeoutError(f"No response to: {command.strip()}")

        response = raw.decode("ascii", errors="replace").strip()

        # Ignore any banner or echoed lines
        if response.startswith("#BD:"):
            break

    if ",CMD:OK,VAL:" not in response:
        raise RuntimeError(f"CAEN returned: {response}")

    return response.split("VAL:", 1)[1]


with serial.Serial(
    port=PORT,
    baudrate=9600,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    xonxoff=True,
    rtscts=False,
    timeout=2,
    write_timeout=2,
) as hv:
    time.sleep(0.2)

    vmon = float(read_parameter(hv, "VMON"))
    polarity = read_parameter(hv, "POL")

    signed_vmon = -abs(vmon) if polarity == "-" else abs(vmon)

    print(f"CH{CHANNEL}: VMon = {signed_vmon:.1f} V")
    print(f"Polarity: {polarity}")

