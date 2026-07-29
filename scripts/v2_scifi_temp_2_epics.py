#!/usr/bin/env python3

"""
Read FPGA and SiPM temperatures from Super-FRS SciFi boards
and publish them to EPICS process variables.

Detector:
    SFRS:FHF1:SCIFI3

PV examples:
    SFRS:FHF1:SCIFI3:SFP0:DEV0:FPGA:TEMP
    SFRS:FHF1:SCIFI3:SFP0:DEV0:SIPM:TEMP
"""

from __future__ import annotations

__author__ = "Irakli Keshelashvili"
__copyright__ = "Copyright 2026, The Super FRS Project"
__version__ = "0.2.1"
__maintainer__ = "Irakli Keshelashvili"
__email__ = "i.keshelashvili@gsi.de"
__status__ = "Production"

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass

import epics
from loguru import logger


GOSIP_COMMAND = "gosipcmd"
GOSIP_TIMEOUT_SECONDS = 2.0
POLL_INTERVAL_SECONDS = 3.0

FPGA_TEMP_REGISTER = 0x20005C
SIPM_TEMP_REGISTER = 0x200064

TMP117_RESOLUTION = 0.0078125

PV_PREFIX = "SFRS:FHF1:SCIFI3"

SCIFI_BOARDS: tuple[tuple[int, int], ...] = (
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
)


@dataclass(frozen=True)
class TemperatureReading:
    sfp: int
    device: int
    fpga: float
    sipm: float


class TemperatureReadError(RuntimeError):
    """Raised when a SciFi temperature register cannot be read."""


def configure_logging(debug: bool = False) -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        level="DEBUG" if debug else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>"
        ),
    )

    logger.add(
        "scifi_temp_reader.log",
        level="DEBUG",
        rotation="1 MB",
        retention="10 days",
        compression="gz",
        enqueue=True,
    )


def pv_name(sfp: int, device: int, sensor: str) -> str:
    """Return the EPICS PV name for one temperature sensor."""
    return (
        f"{PV_PREFIX}:"
        f"SFP{sfp}:"
        f"DEV{device}:"
        f"{sensor}:TEMP"
    )


def validate_board(sfp: int, device: int) -> None:
    if (sfp, device) not in SCIFI_BOARDS:
        raise ValueError(
            f"SFP {sfp}, DEV {device} is not configured as a SciFi board"
        )


def read_register(sfp: int, device: int, address: int) -> int:
    command = [
        GOSIP_COMMAND,
        "-r",
        "-x",
        str(sfp),
        str(device),
        f"0x{address:06x}",
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=GOSIP_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise TemperatureReadError(
            f"{GOSIP_COMMAND!r} was not found"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise TemperatureReadError(
            f"Timeout reading SFP {sfp}, DEV {device}"
        ) from error
    except subprocess.CalledProcessError as error:
        details = (
            error.stderr.strip()
            or error.stdout.strip()
            or f"exit status {error.returncode}"
        )

        raise TemperatureReadError(
            f"gosipcmd failed for SFP {sfp}, DEV {device}: {details}"
        ) from error

    output = result.stdout.strip()

    if not output:
        raise TemperatureReadError(
            f"Empty output for SFP {sfp}, DEV {device}"
        )

    for token in reversed(output.replace(",", " ").split()):
        try:
            return int(token, 0)
        except ValueError:
            continue

    raise TemperatureReadError(
        f"Cannot parse gosipcmd output: {output!r}"
    )


def signed_16bit(value: int) -> int:
    """Convert an unsigned 16-bit value to signed."""
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def read_fpga_temp(sfp: int, device: int) -> float:
    raw_value = read_register(
        sfp,
        device,
        FPGA_TEMP_REGISTER,
    )

    adc_value = raw_value & 0x0FFF
    temperature = adc_value * 503.975 / 4096.0 - 273.15

    return round(temperature, 1)


def read_sipm_temp(sfp: int, device: int) -> float:
    raw_value = read_register(
        sfp,
        device,
        SIPM_TEMP_REGISTER,
    )

    signed_value = signed_16bit(raw_value)
    temperature = signed_value * TMP117_RESOLUTION

    return round(temperature, 1)


def read_temperatures(
    sfp: int,
    device: int,
) -> TemperatureReading:
    validate_board(sfp, device)

    return TemperatureReading(
        sfp=sfp,
        device=device,
        fpga=read_fpga_temp(sfp, device),
        sipm=read_sipm_temp(sfp, device),
    )


def connect_pvs() -> dict[tuple[int, int, str], epics.PV]:
    """Create and connect all EPICS PV objects."""
    pvs: dict[tuple[int, int, str], epics.PV] = {}

    for sfp, device in SCIFI_BOARDS:
        for sensor in ("FPGA", "SIPM"):
            name = pv_name(sfp, device, sensor)

            pv = epics.PV(
                name,
                auto_monitor=False,
                connection_timeout=2.0,
            )

            pvs[(sfp, device, sensor)] = pv

            if pv.wait_for_connection(timeout=2.0):
                logger.info("Connected to {}", name)
            else:
                logger.warning("PV is not connected: {}", name)

    return pvs


def write_pv(
    pv: epics.PV,
    value: float,
    old_value: float | None,
) -> bool:
    """
    Write a PV only if the value changed.

    Returns True if the write succeeded.
    """
    if old_value is not None and value == old_value:
        return True

    if not pv.connected:
        logger.warning("PV disconnected: {}", pv.pvname)

        if not pv.wait_for_connection(timeout=1.0):
            return False

    success = pv.put(
        value,
        wait=True,
        timeout=2.0,
    )

    if success is None:
        logger.error(
            "Failed to write {} = {:.1f}",
            pv.pvname,
            value,
        )
        return False

    logger.success(
        "{} = {:.1f} °C",
        pv.pvname,
        value,
    )

    return True


def monitor_temperatures(interval: float) -> None:
    """Continuously read hardware and update EPICS PVs."""
    pvs = connect_pvs()

    previous_values: dict[tuple[int, int, str], float] = {}

    logger.info(
        "Starting temperature monitor for {} with {:.1f} s interval",
        PV_PREFIX,
        interval,
    )

    while True:
        cycle_started = time.monotonic()

        for sfp, device in SCIFI_BOARDS:
            try:
                reading = read_temperatures(sfp, device)
            except TemperatureReadError as error:
                logger.error(
                    "Cannot read SFP {}, DEV {}: {}",
                    sfp,
                    device,
                    error,
                )
                continue

            values = {
                "FPGA": reading.fpga,
                "SIPM": reading.sipm,
            }

            for sensor, value in values.items():
                key = (sfp, device, sensor)
                pv = pvs[key]
                old_value = previous_values.get(key)

                if write_pv(pv, value, old_value):
                    previous_values[key] = value

        elapsed = time.monotonic() - cycle_started
        sleep_time = max(0.0, interval - elapsed)

        time.sleep(sleep_time)


def read_single_board(sfp: int, device: int) -> int:
    """Read and print one board without starting the monitor loop."""
    try:
        reading = read_temperatures(sfp, device)
    except TemperatureReadError as error:
        logger.error("{}", error)
        return 1

    print(
        f"--sfp {reading.sfp} "
        f"--dev {reading.device} "
        f"--fpga_temp {reading.fpga:.1f} "
        f"--sipm_temp {reading.sipm:.1f}"
    )

    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read SciFi board temperatures and publish them to EPICS"
        )
    )

    parser.add_argument(
        "--sfp",
        "-s",
        type=int,
        help="read only one SFP",
    )
    parser.add_argument(
        "--dev",
        "-d",
        type=int,
        help="read only one device",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        default=POLL_INTERVAL_SECONDS,
        help="EPICS update interval in seconds, default: 3",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    if (args.sfp is None) != (args.dev is None):
        parser.error("--sfp and --dev must be supplied together")

    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    if args.sfp is not None:
        try:
            validate_board(args.sfp, args.dev)
        except ValueError as error:
            parser.error(str(error))

    return args


def main() -> int:
    args = parse_arguments()
    configure_logging(args.debug)

    if args.sfp is not None:
        return read_single_board(args.sfp, args.dev)

    try:
        monitor_temperatures(args.interval)
    except KeyboardInterrupt:
        logger.info("Temperature monitoring stopped")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
