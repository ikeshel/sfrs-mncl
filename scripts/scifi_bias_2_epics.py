#!/usr/bin/env python3

"""
Read SiPM bias set and measured values from Super-FRS SciFi boards
and publish them to EPICS process variables.

Detector:
    SFRS:FHF1:SCIFI3

PV examples:
    SFRS:FHF1:SCIFI3:SFP0:DEV0:SIPM:BIAS_SET
    SFRS:FHF1:SCIFI3:SFP0:DEV0:SIPM:BIAS_RBV

The 32-bit bias readback register contains:
    upper 16 bits: bias set value
    lower 16 bits: measured ADC value
"""

from __future__ import annotations

__author__ = "Irakli Keshelashvili"
__copyright__ = "Copyright 2026, The Super FRS Project"
__version__ = "0.3.0"
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
POLL_INTERVAL_SECONDS = 1.0

BIAS_READ_REGISTER = 0x20011C
PWM_FACTOR = 755.0
ADC_FACTOR = 400.0

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
class BiasReading:
    sfp: int
    device: int
    set_raw: int
    adc_raw: int
    set_voltage: float
    measured_voltage: float


class BiasReadError(RuntimeError):
    """Raised when a SciFi bias register cannot be read."""


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
        "logs/scifi_bias_2_epics.log",
        level="DEBUG",
        rotation="1 MB",
        retention="10 days",
        compression="gz",
        enqueue=True,
    )


def pv_name(sfp: int, device: int, field: str) -> str:
    """Return the EPICS PV name for one SiPM bias value."""
    return (
        f"{PV_PREFIX}:"
        f"SFP{sfp}:"
        f"DEV{device}:"
        f"SIPM:{field}"
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
        raise BiasReadError(
            f"{GOSIP_COMMAND!r} was not found"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise BiasReadError(
            f"Timeout reading SFP {sfp}, DEV {device}"
        ) from error
    except subprocess.CalledProcessError as error:
        details = (
            error.stderr.strip()
            or error.stdout.strip()
            or f"exit status {error.returncode}"
        )

        raise BiasReadError(
            f"gosipcmd failed for SFP {sfp}, DEV {device}: {details}"
        ) from error

    output = result.stdout.strip()

    if not output:
        raise BiasReadError(
            f"Empty output for SFP {sfp}, DEV {device}"
        )

    for token in reversed(output.replace(",", " ").split()):
        try:
            return int(token, 0)
        except ValueError:
            continue

    raise BiasReadError(
        f"Cannot parse gosipcmd output: {output!r}"
    )


def decode_bias_register(
    sfp: int,
    device: int,
    register_value: int,
) -> BiasReading:
    """Decode the packed set and ADC values from the bias register."""
    set_raw = (register_value >> 16) & 0xFFFF
    adc_raw = register_value & 0xFFFF

    return BiasReading(
        sfp=sfp,
        device=device,
        set_raw=set_raw,
        adc_raw=adc_raw,
        set_voltage=set_raw / PWM_FACTOR,
        measured_voltage=adc_raw / ADC_FACTOR,
    )


def read_bias(sfp: int, device: int) -> BiasReading:
    validate_board(sfp, device)

    register_value = read_register(
        sfp,
        device,
        BIAS_READ_REGISTER,
    )

    return decode_bias_register(
        sfp,
        device,
        register_value,
    )


def connect_pvs() -> dict[tuple[int, int, str], epics.PV]:
    """Create and connect all EPICS PV objects."""
    pvs: dict[tuple[int, int, str], epics.PV] = {}

    for sfp, device in SCIFI_BOARDS:
        for field in ("BIAS_SET", "BIAS_RBV"):
            name = pv_name(sfp, device, field)

            pv = epics.PV(
                name,
                auto_monitor=False,
                connection_timeout=2.0,
            )

            pvs[(sfp, device, field)] = pv

            if pv.wait_for_connection(timeout=2.0):
                logger.info("Connected to {}", name)
            else:
                logger.warning("PV is not connected: {}", name)

    return pvs


def write_pv(
    pv: epics.PV,
    value: float | int,
    old_value: float | int | None,
    field: str,
) -> bool:
    """
    Write a PV only if the value changed.

    Returns True if no write was needed or the write succeeded.
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

    displayed_value = f"{float(value):.3f} V"

    if success != 1:
        logger.error(
            "Failed to write {} = {}",
            pv.pvname,
            displayed_value,
        )
        return False

    logger.success(
        "{} = {}",
        pv.pvname,
        displayed_value,
    )

    return True


def monitor_bias(interval: float) -> None:
    """Continuously read all boards and update their EPICS PVs."""
    pvs = connect_pvs()

    previous_values: dict[tuple[int, int, str], float | int] = {}

    logger.info(
        "Starting SiPM bias monitor for {} with {:.1f} s interval",
        PV_PREFIX,
        interval,
    )

    while True:
        cycle_started = time.monotonic()

        for sfp, device in SCIFI_BOARDS:
            try:
                reading = read_bias(sfp, device)
            except BiasReadError as error:
                logger.error(
                    "Cannot read SFP {}, DEV {}: {}",
                    sfp,
                    device,
                    error,
                )

                continue

            logger.debug(
                (
                    "SFP {}, DEV {} | set raw: {} ({:.3f} V), "
                    "ADC raw: {} ({:.3f} V)"
                ),
                sfp,
                device,
                reading.set_raw,
                reading.set_voltage,
                reading.adc_raw,
                reading.measured_voltage,
            )

            values = {
                "BIAS_SET": reading.set_voltage,
                "BIAS_RBV": reading.measured_voltage,
            }

            for field, value in values.items():
                key = (sfp, device, field)
                pv = pvs[key]
                old_value = previous_values.get(key)

                if write_pv(pv, value, old_value, field):
                    previous_values[key] = value

        elapsed = time.monotonic() - cycle_started
        sleep_time = max(0.0, interval - elapsed)

        time.sleep(sleep_time)


def read_single_board(sfp: int, device: int) -> int:
    """Read and print one board without starting the EPICS monitor."""
    try:
        reading = read_bias(sfp, device)
    except BiasReadError as error:
        logger.error("{}", error)
        return 1

    print(
        f"--sfp {reading.sfp} "
        f"--dev {reading.device} "
        f"--bias_set {reading.set_voltage:.3f} "
        f"--bias_rbv {reading.measured_voltage:.3f} "
        f"--set_raw {reading.set_raw} "
        f"--adc_raw {reading.adc_raw}"
    )

    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read SciFi SiPM bias values and publish them to EPICS"
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
        help="EPICS update interval in seconds, default: 1",
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
        monitor_bias(args.interval)
    except KeyboardInterrupt:
        logger.info("SiPM bias monitoring stopped")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
