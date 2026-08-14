#!/usr/bin/env python3
"""Publish the first three CAEN NDT1470 channels to EPICS.

Mapping:
    CAEN CH0 -> SFRS:FHF1:MUSIC1:FC1
    CAEN CH1 -> SFRS:FHF1:MUSIC1:FC2
    CAEN CH2 -> SFRS:FHF1:MUSIC1:FC3

For each field cage, the script publishes VMON, VSET, and the raw CAEN
channel-status bitmask to HV_RBV, HV_SET, and HV_STAT respectively.

Dependencies:
    python3-serial (pyserial)
    pyepics
"""

from __future__ import annotations

import argparse
import logging
import time
from dataclasses import dataclass

import serial
from epics import PV


DEFAULT_PORT = "/dev/ttyACM0"
DEFAULT_BAUD_RATE = 9600
DEFAULT_BOARD_ADDRESS = 0
DEFAULT_PREFIX = "SFRS:FHF1:MUSIC1"
DEFAULT_INTERVAL = 3.0
NUMBER_OF_CAEN_CHANNELS = 4
NUMBER_OF_USED_CHANNELS = 3


@dataclass(frozen=True)
class ChannelValues:
    hv_v_rbv: float
    hv_v_set: float
    hv_v_stat: int


@dataclass(frozen=True)
class ChannelPVs:
    hv_v_rbv: PV
    hv_v_set: PV
    hv_v_stat: PV


class CaenNDT1470:
    """Minimal reader for the CAEN NDT1470 ASCII serial protocol."""

    def __init__(self, port: str, baud_rate: int, board_address: int) -> None:
        self.board_address = board_address
        self.serial = serial.Serial(
            port=port,
            baudrate=baud_rate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=True,
            rtscts=False,
            dsrdtr=False,
            timeout=2.0,
            write_timeout=2.0,
        )
        time.sleep(0.2)

    def close(self) -> None:
        self.serial.close()

    def __enter__(self) -> "CaenNDT1470":
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback) -> None:
        self.close()

    def query_all(self, parameter: str) -> list[str]:
        """Read one parameter from all four channels."""
        command = (
            f"$BD:{self.board_address:02d},CMD:MON,"
            f"CH:{NUMBER_OF_CAEN_CHANNELS},PAR:{parameter}\r\n"
        )

        self.serial.reset_input_buffer()
        self.serial.write(command.encode("ascii"))
        self.serial.flush()

        # Ignore possible banner or echoed lines and wait for the CAEN reply.
        for _ in range(20):
            raw_reply = self.serial.readline()
            if not raw_reply:
                raise TimeoutError(f"No CAEN response to {command.strip()}")

            reply = raw_reply.decode("ascii", errors="replace").strip()
            if reply.startswith("#BD:"):
                break
        else:
            raise RuntimeError("No valid CAEN reply received")

        expected = f"#BD:{self.board_address:02d},CMD:OK,VAL:"
        if not reply.startswith(expected):
            raise RuntimeError(f"CAEN returned: {reply}")

        values = reply[len(expected) :].split(";")
        if len(values) != NUMBER_OF_CAEN_CHANNELS:
            raise RuntimeError(
                f"Expected {NUMBER_OF_CAEN_CHANNELS} values for {parameter}, "
                f"received {len(values)}: {reply}"
            )

        return values

    def read_first_three_channels(self) -> list[ChannelValues]:
        vmon = [float(value) for value in self.query_all("VMON")]
        vset = [float(value) for value in self.query_all("VSET")]
        # STAT is returned as a decimal status bitmask, sometimes zero-padded.
        status = [int(value, 10) for value in self.query_all("STAT")]
        polarity = self.query_all("POL")

        result: list[ChannelValues] = []
        for channel in range(NUMBER_OF_USED_CHANNELS):
            sign = -1.0 if polarity[channel] == "-" else 1.0
            result.append(
                ChannelValues(
                    hv_v_rbv=sign * abs(vmon[channel]),
                    hv_v_set=sign * abs(vset[channel]),
                    hv_v_stat=status[channel],
                )
            )
        return result


def build_pvs(prefix: str, timeout: float) -> list[ChannelPVs]:
    result: list[ChannelPVs] = []
    missing: list[str] = []

    for field_cage in range(1, NUMBER_OF_USED_CHANNELS + 1):
        pv_prefix = f"{prefix}:FC{field_cage}"
        channel_pvs = ChannelPVs(
            hv_v_rbv=PV(f"{pv_prefix}:HV_V_RBV", auto_monitor=False),
            hv_v_set=PV(f"{pv_prefix}:HV_V_SET", auto_monitor=False),
            hv_v_stat=PV(f"{pv_prefix}:HV_STAT", auto_monitor=False),
        )
        result.append(channel_pvs)

        for pv in (channel_pvs.hv_v_rbv, channel_pvs.hv_v_set, channel_pvs.hv_v_stat):
            if not pv.wait_for_connection(timeout=timeout):
                missing.append(pv.pvname)

    if missing:
        raise RuntimeError("EPICS PVs not connected: " + ", ".join(missing))

    return result


def publish(pvs: list[ChannelPVs], values: list[ChannelValues]) -> None:
    for field_cage, (channel_pvs, channel_values) in enumerate(
        zip(pvs, values), start=1
    ):
        writes = (
            (channel_pvs.hv_v_rbv, channel_values.hv_v_rbv),
            (channel_pvs.hv_v_set, channel_values.hv_v_set),
            (channel_pvs.hv_v_stat, channel_values.hv_v_stat),
        )

        for pv, value in writes:
            if pv.put(value, wait=False) is None:
                raise RuntimeError(f"Failed to write EPICS PV {pv.pvname}")

        logging.debug(
            "FC%d: HV_RBV=%.1f V HV_SET=%.1f V HV_STAT=%d (0x%04X)",
            field_cage,
            channel_values.hv_v_rbv,
            channel_values.hv_v_set,
            channel_values.hv_v_stat,
            channel_values.hv_v_stat,
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish CAEN NDT1470 CH0-CH2 values to MUSIC1 EPICS PVs"
    )
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud-rate", type=int, default=DEFAULT_BAUD_RATE)
    parser.add_argument(
        "--board-address", type=int, choices=range(32), default=DEFAULT_BOARD_ADDRESS
    )
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument("--pv-timeout", type=float, default=5.0)
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval must be greater than zero")
    if args.pv_timeout <= 0:
        parser.error("--pv-timeout must be greater than zero")
    if args.reconnect_delay <= 0:
        parser.error("--reconnect-delay must be greater than zero")

    return args


def main() -> int:
    args = parse_arguments()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    pvs = build_pvs(args.prefix, args.pv_timeout)
    logging.info("Connected to all nine MUSIC1 EPICS PVs")

    while True:
        try:
            with CaenNDT1470(
                args.port, args.baud_rate, args.board_address
            ) as device:
                logging.info(
                    "Connected to CAEN NDT1470 on %s at %d baud",
                    args.port,
                    args.baud_rate,
                )

                next_poll = time.monotonic()
                while True:
                    values = device.read_first_three_channels()
                    publish(pvs, values)

                    if args.once:
                        return 0

                    next_poll += args.interval
                    time.sleep(max(0.0, next_poll - time.monotonic()))

        except KeyboardInterrupt:
            logging.info("Stopped")
            return 0
        except (OSError, serial.SerialException, TimeoutError, RuntimeError) as error:
            logging.error("%s", error)
            if args.once:
                return 1
            logging.info("Retrying in %.1f seconds", args.reconnect_delay)
            time.sleep(args.reconnect_delay)


if __name__ == "__main__":
    raise SystemExit(main())
