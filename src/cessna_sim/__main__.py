"""Command line entry: python -m cessna_sim."""

from __future__ import annotations

import argparse

from cessna_sim.config import DEFAULT_CONFIG, format_startup_log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cessna 172 glide and stall simulator."
    )
    parser.add_argument(
        "--hw",
        action="store_true",
        help="Write homework parts (a)-(d) plots without the interactive view.",
    )
    args = parser.parse_args(argv)
    print(format_startup_log(DEFAULT_CONFIG))
    if args.hw:
        print("Homework plots are not built yet.")
        return 0
    print("Interactive glide view is not built yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
