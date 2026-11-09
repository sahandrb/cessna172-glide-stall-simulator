"""Section 9 log files."""

import csv

from cessna_sim.config import Config
from cessna_sim.records import RUN_COLUMNS, write_run_csv
from cessna_sim.simulation import GlideRun


def test_csv_log_contains_stall_transitions(tmp_path) -> None:
    config = Config(density_model="constant", h_end_m=1.0)
    run = GlideRun(800.0, 6.0, config)
    run.step(0.02)
    run.set_alpha(18.0)
    run.step(0.02)
    run.set_alpha(4.0)
    run.step(0.02)
    run_path, events_path = write_run_csv(run.log(), tmp_path)

    with run_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == list(RUN_COLUMNS)
    assert len(rows) == 4  # initial sample plus three steps
    assert any(float(row["stall_flag"]) == 1.0 for row in rows)

    with events_path.open(newline="", encoding="utf-8") as handle:
        events = list(csv.DictReader(handle))
    names = [row["event"] for row in events]
    assert names[0] == "engine_failure"
    assert "stall_onset" in names
    assert "stall_recovery" in names
