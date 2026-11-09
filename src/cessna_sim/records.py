"""CSV logs specified in section 9."""

from __future__ import annotations

import csv
from pathlib import Path

from cessna_sim.simulation import RunLog

RUN_COLUMNS = (
    "t",
    "alpha_deg",
    "CL",
    "CD",
    "Cm",
    "L_over_D",
    "V",
    "Vs",
    "gamma_deg",
    "theta_deg",
    "h",
    "r",
    "rho",
    "load_factor",
    "stall_flag",
)


def _column(log: RunLog, name: str):
    return {
        "t": log.t,
        "alpha_deg": log.alpha_deg,
        "CL": log.cl,
        "CD": log.cd,
        "Cm": log.cm,
        "L_over_D": log.lift_to_drag,
        "V": log.airspeed,
        "Vs": log.stall_speed,
        "gamma_deg": log.gamma_deg,
        "theta_deg": log.theta_deg,
        "h": log.altitude,
        "r": log.distance,
        "rho": log.density,
        "load_factor": log.load_factor,
        "stall_flag": log.stall_flag,
    }[name]


def write_run_csv(log: RunLog, output_dir: Path) -> tuple[Path, Path]:
    """Write run.csv and events.csv. One physics sample per run row."""
    output_dir.mkdir(parents=True, exist_ok=True)
    run_path = output_dir / "run.csv"
    events_path = output_dir / "events.csv"
    with run_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(RUN_COLUMNS)
        rows = zip(*(_column(log, name) for name in RUN_COLUMNS))
        for row in rows:
            writer.writerow([f"{value:.8g}" for value in row])
    with events_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("time", "event", "h", "V", "alpha_deg"))
        for event in log.events:
            writer.writerow(
                (
                    f"{event.time_s:.8g}",
                    event.name,
                    f"{event.altitude_m:.8g}",
                    f"{event.airspeed_m_s:.8g}",
                    f"{event.alpha_deg:.8g}",
                )
            )
    return run_path, events_path
