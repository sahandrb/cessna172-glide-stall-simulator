"""Integration checks from section 11.2."""

import numpy as np
import pytest

from cessna_sim.aerodynamics import maximum_lift_to_drag
from cessna_sim.config import DEFAULT_CONFIG, Config
from cessna_sim.simulation import GlideRun, simulate_constant_alpha


def test_equilibrium_state_stays_put_for_ten_seconds() -> None:
    config = Config(density_model="constant")
    alpha = 6.0
    trajectory = simulate_constant_alpha(alpha, 1500.0, 10.0, config, sample_dt_s=0.1)
    assert trajectory.airspeed[-1] == pytest.approx(trajectory.airspeed[0], abs=1e-3)
    assert trajectory.gamma_rad[-1] == pytest.approx(trajectory.gamma_rad[0], abs=1e-3)
    assert np.all(np.isfinite(trajectory.altitude))


def test_best_glide_distance_is_close_to_height_times_ld_max() -> None:
    config = Config(density_model="constant")
    _, ld_max, alpha_star = maximum_lift_to_drag()
    h0 = 1000.0
    trajectory = simulate_constant_alpha(
        alpha_star,
        h0,
        4000.0,
        config,
        stop_on_altitude=True,
    )
    assert trajectory.altitude[-1] == pytest.approx(config.h_end_m, abs=0.05)
    expected = (h0 - config.h_end_m) * ld_max
    assert trajectory.distance[-1] == pytest.approx(expected, rel=0.03)
    assert "altitude" in trajectory.message


def test_homework_part_d_covers_ten_seconds() -> None:
    trajectory = simulate_constant_alpha(
        DEFAULT_CONFIG.default_alpha_deg,
        DEFAULT_CONFIG.hw_part_d_h0_m,
        DEFAULT_CONFIG.hw_part_d_duration_s,
        DEFAULT_CONFIG,
        stop_on_altitude=False,
        sample_dt_s=DEFAULT_CONFIG.hw_part_d_sample_dt_s,
    )
    assert trajectory.t[0] == pytest.approx(0.0)
    assert trajectory.t[-1] == pytest.approx(10.0)
    assert len(trajectory.t) == 1001
    for series in (
        trajectory.airspeed,
        trajectory.gamma_rad,
        trajectory.altitude,
        trajectory.distance,
    ):
        assert series.shape == trajectory.t.shape
        assert np.all(np.isfinite(series))
    assert trajectory.distance[0] == pytest.approx(0.0)
    assert trajectory.altitude[0] == pytest.approx(10.0)


def test_stall_onset_and_recovery_are_logged() -> None:
    config = Config(density_model="constant", h_end_m=1.0)
    run = GlideRun(800.0, 6.0, config)
    run.step(config.physics_dt_s)
    run.set_alpha(16.0)
    run.step(config.physics_dt_s)
    run.set_alpha(6.0)
    run.step(config.physics_dt_s)
    names = [event.name for event in run.events]
    assert names[0] == "engine_failure"
    assert "stall_onset" in names
    assert "stall_recovery" in names
    log = run.log()
    assert set(np.unique(log.stall_flag)).issubset({0.0, 1.0})
    assert log.stall_flag.max() == 1.0
