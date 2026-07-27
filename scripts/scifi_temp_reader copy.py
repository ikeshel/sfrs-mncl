#!/usr/bin/env python3

"""
Read FPGA and SiPM temperatures from Super-FRS SciFi boards.

Based on the original read_temp_sfrs.sh and read_temp_scifi.py
scripts by Michael Heil.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass

from loguru import logger


__author__ = "Irakli Keshelashvili"
__copyright__ = "Copyright 2026, The Super-FRS Project"
__version__ = "0.1.0"
__maintainer__ = "Irakli Keshelashvili"
__email__ = "i.keshelashvili@gsi.de"
__status__ = "Development"


GOSIP_COMMAND = "gosipcmd"
GOSIP_TIMEOUT_SECONDS = 2.0

FPGA_TEMP_REGISTER = 0x20005C
SIPM_TEMP_REGISTER = 0x200064

TMP117_RESOLUTION = 0.0078125

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
    """Configure console and rotating-file logging."""
    logger.remove()

    console_level = "DEBUG" if debug else "INFO"

    logger.add(
        sys.stderr,
        level=console_level,
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
        backtrace=False,
        diagnose=False,
    )


def validate_board(sfp: int, device: int) -> None:
    """Verify that an SFP/device pair exists in the SciFi topology."""
    if (sfp, device) not in SCIFI_BOARDS:
        valid_devices = [
            board_device
            for board_sfp, board_device in SCIFI_BOARDS
            if board_sfp == sfp
        ]

        if valid_devices:
            devices_text = ", ".join(str(value) for value in valid_devices)
            raise ValueError(
                f"Invalid device {device} for SFP {sfp}. "
                f"Valid devices: {devices_text}"
            )

        valid_sfps = sorted({board_sfp for board_sfp, _ in SCIFI_BOARDS})
        sfps_text = ", ".join(str(value) for value in valid_sfps)

        raise ValueError(
            f"Invalid SFP {sfp}. Valid SFP values: {sfps_text}"
        )


def read_register(sfp: int, device: int, address: int) -> int:
    """Read one GOSIP register and return its integer value."""
    command = [
        GOSIP_COMMAND,
        "-r",
        "-x",
        str(sfp),
        str(device),
        f"0x{address:06x}",
    ]

    logger.debug("Executing command: {}", " ".join(command))

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
            f"{GOSIP_COMMAND!r} was not found in PATH"
        ) from error
    except subprocess.TimeoutExpired as error:
        raise TemperatureReadError(
            f"Timeout reading SFP {sfp}, DEV {device}, "
            f"register 0x{address:06x}"
        ) from error
    except subprocess.CalledProcessError as error:
        details = (
            error.stderr.strip()
            or error.stdout.strip()
            or f"exit status {error.returncode}"
        )

        raise TemperatureReadError(
            f"gosipcmd failed for SFP {sfp}, DEV {device}, "
            f"register 0x{address:06x}: {details}"
        ) from error

    output = result.stdout.strip()

    if not output:
        raise TemperatureReadError(
            f"Empty gosipcmd output for SFP {sfp}, DEV {device}, "
            f"register 0x{address:06x}"
        )

    # Some gosipcmd versions may print additional text. Use the last token
    # that can be parsed as an integer.
    for token in reversed(output.replace(",", " ").split()):
        try:
            return int(token, 0)
        except ValueError:
            continue

    raise TemperatureReadError(
        f"Cannot parse gosipcmd output for SFP {sfp}, DEV {device}, "
        f"register 0x{address:06x}: {output!r}"
    )


def signed_16bit(value: int) -> int:
    """Convert an unsigned 16-bit integer to a signed integer."""
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def read_fpga_temp(sfp: int, device: int) -> float:
    """Read the FPGA internal temperature in degrees Celsius."""
    raw_value = read_register(
        sfp,
        device,
        FPGA_TEMP_REGISTER,
    )

    # Verify this mask against the FPGA register documentation.
    adc_value = raw_value & 0x0FFF

    temperature = adc_value * 503.975 / 4096.0 - 273.15
    return round(temperature, 1)


def read_sipm_temp(sfp: int, device: int) -> float:
    """Read the on-board TMP117 SiPM temperature in degrees Celsius."""
    raw_value = read_register(
        sfp,
        device,
        SIPM_TEMP_REGISTER,
    )

    signed_value = signed_16bit(raw_value)
    temperature = signed_value * TMP117_RESOLUTION

    return round(temperature, 1)


def read_temperatures(sfp: int, device: int) -> TemperatureReading:
    """Read all available temperatures from one SciFi board."""
    validate_board(sfp, device)

    return TemperatureReading(
        sfp=sfp,
        device=device,
        fpga=read_fpga_temp(sfp, device),
        sipm=read_sipm_temp(sfp, device),
    )


def log_reading(reading: TemperatureReading) -> None:
    """Write a temperature reading to the configured logger."""
    logger.info(
        "SFP: {}, DEV: {}, FPGA Temp: {:.1f} °C, SiPM Temp: {:.1f} °C",
        reading.sfp,
        reading.device,
        reading.fpga,
        reading.sipm,
    )


def read_all_boards() -> list[TemperatureReading]:
    """
    Read temperatures from every configured SciFi board.

    A failure on one board is logged, but does not stop the remaining reads.
    """
    readings: list[TemperatureReading] = []

    for sfp, device in SCIFI_BOARDS:
        try:
            reading = read_temperatures(sfp, device)
        except TemperatureReadError as error:
            logger.error(
                "Failed to read SFP {}, DEV {}: {}",
                sfp,
                device,
                error,
            )
            continue

        readings.append(reading)
        log_reading(reading)

    return readings


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Read FPGA and SiPM temperatures from Super-FRS SciFi boards"
        )
    )

    parser.add_argument(
        "--sfp",
        "-s",
        type=int,
        help="SFP number",
    )
    parser.add_argument(
        "--dev",
        "-d",
        type=int,
        help="device number",
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

    if args.sfp is not None:
        try:
            validate_board(args.sfp, args.dev)
        except ValueError as error:
            parser.error(str(error))

    return args


def main() -> int:
    """Run the SciFi temperature reader."""
    args = parse_arguments()
    configure_logging(debug=args.debug)

    if args.sfp is None:
        readings = read_all_boards()

        if not readings:
            logger.error("No SciFi temperature readings were successful")
            return 1

        logger.info(
            "Successfully read {} of {} SciFi boards",
            len(readings),
            len(SCIFI_BOARDS),
        )

        return 0 if len(readings) == len(SCIFI_BOARDS) else 2

    try:
        reading = read_temperatures(args.sfp, args.dev)
    except TemperatureReadError as error:
        logger.error("{}", error)
        return 1

    # Preserve the machine-readable output used by existing scripts.
    print(
        f"--sfp {reading.sfp} "
        f"--dev {reading.device} "
        f"--fpga_temp {reading.fpga:.1f} "
        f"--sipm_temp {reading.sipm:.1f}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())