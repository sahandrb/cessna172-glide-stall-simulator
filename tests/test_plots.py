"""Headless homework figures."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from cessna_sim.__main__ import main
from cessna_sim.plots import write_homework_plots


def test_homework_writer_saves_four_figures(tmp_path: Path) -> None:
    output = write_homework_plots(tmp_path)
    names = sorted(path.name for path in output.glob("*.png"))
    assert names == [
        "figure1_coefficients.png",
        "figure2_lift_to_drag.png",
        "figure3_equilibrium.png",
        "figure4_time_history.png",
    ]
    assert all(path.stat().st_size > 1000 for path in output.glob("*.png"))


def test_hw_command_writes_an_output_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["--hw"]) == 0
    folders = list(Path("outputs").glob("hw_*"))
    assert len(folders) == 1
    assert (folders[0] / "figure4_time_history.png").is_file()
