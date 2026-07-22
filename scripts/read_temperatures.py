#!/usr/bin/env python3

import argparse
import subprocess


FPGA_TEMP_REGISTER = 0x20005C
SIPM_TEMP_REGISTER = 0x200064
FEB_TEMP_REGISTER = 0x200068

TMP117_RESOLUTION = 0.0078125


def read_register(sfp: int, device: int, address: int) -> int:
    """Read a register using gosipcmd and return its integer value."""
    try:
        result = subprocess.run(
            [
                "gosipcmd",
                "-r",
                "-x",
                str(sfp),
                str(device),
                f"0x{address:x}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("gosipcmd was not found") from exc
    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or exc.stdout.strip()
        raise RuntimeError(f"gosipcmd failed: {error}") from exc

    output = result.stdout.strip()

    try:
        return int(output, 16)
    except ValueError as exc:
        raise RuntimeError(
            f"Unexpected gosipcmd output for register 0x{address:x}: {output!r}"
        ) from exc


def signed_16bit(value: int) -> int:
    """Convert an unsigned 16-bit value to a signed integer."""
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def read_fpga_temperature(sfp: int, device: int) -> float:
    raw_value = read_register(sfp, device, FPGA_TEMP_REGISTER) & 0xFFFF
    return round(raw_value * 503.975 / 4096 - 273.15, 1)


def read_tmp117_temperature(
    sfp: int,
    device: int,
    register: int,
) -> float:
    raw_value = read_register(sfp, device, register)
    raw_value = signed_16bit(raw_value)
    return round(raw_value * TMP117_RESOLUTION, 1)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read SciFi temperature sensors"
    )
    parser.add_argument(
        "sfp",
        type=int,
        choices=range(5),
        metavar="SFP",
        help="SFP number (0–4)",
    )
    parser.add_argument(
        "device",
        type=int,
        choices=range(16),
        metavar="DEVICE",
        help="device number (0–15)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    print(f"Temperatures for SFP {args.sfp}, device {args.device}:")
    print(
        f"  SciFi_652 FPGA:        "
        f"{read_fpga_temperature(args.sfp, args.device):.1f} °C"
    )
    print(
        f"  SciFi_652 SiPM sensor: "
        f"{read_tmp117_temperature(args.sfp, args.device, SIPM_TEMP_REGISTER):.1f} °C"
    )
    print(
        f"  SciFi FEB sensor:      "
        f"{read_tmp117_temperature(args.sfp, args.device, FEB_TEMP_REGISTER):.1f} °C"
    )


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        raise SystemExit(f"Error: {error}")
