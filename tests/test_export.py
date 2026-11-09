"""Post-run PNG and CSV export, including a stalled interval."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from cessna_sim.config import Config
from cessna_sim.plots import export_run_plots
from cessna_sim.records import write_run_csv
from cessna_sim.simulation import GlideRun


def test_export_writes_figures_and_csv(tmp_path: Path) -> None:
    config = Config(density_model="constant", h_end_m=1.0)
    run = GlideRun(600.0, 6.0, config)
    run.step(0.05)
    run.set_alpha(17.0)
    run.step(0.05)
    log = run.log()
    write_run_csv(log, tmp_path)
    export_run_plots(log, tmp_path, config)
    assert (tmp_path / "run.csv").is_file()
    assert (tmp_path / "events.csv").is_file()
    for name in (
        "figure1_coefficients.png",
        "figure2_lift_to_drag.png",
        "figure3_equilibrium.png",
        "figure4_time_history.png",
        "figure5_run_signals.png",
    ):
        assert (tmp_path / name).stat().st_size > 1000
