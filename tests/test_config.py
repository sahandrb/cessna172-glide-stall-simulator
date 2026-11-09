"""Defaults from the project specification, section 4.4 and the CONFIG list."""

import pytest

from cessna_sim.config import DEFAULT_CONFIG, Config, format_startup_log, validate_config


def test_homework_defaults() -> None:
    config = DEFAULT_CONFIG
    assert config.mass_kg == pytest.approx(1156.7)
    assert config.wing_area_m2 == pytest.approx(16.165)
    assert config.gravity_m_s2 == pytest.approx(9.80665)
    assert config.density_model == "isa_troposphere"
    assert config.sea_level_density_kg_m3 == pytest.approx(1.225)


def test_control_and_integrator_defaults() -> None:
    config = DEFAULT_CONFIG
    assert config.alpha_min_deg == pytest.approx(-2.0)
    assert config.alpha_max_deg == pytest.approx(20.0)
    assert config.alpha_rate_deg_per_s == pytest.approx(4.0)
    assert config.default_alpha_deg == pytest.approx(6.0)
    assert config.default_h0_m == pytest.approx(1000.0)
    assert config.h_end_m == pytest.approx(10.0)
    assert config.default_t_max_s == pytest.approx(300.0)
    assert config.integrator_method == "RK23"
    assert config.rtol == pytest.approx(1e-6)
    assert config.atol == pytest.approx(1e-8)
    assert config.physics_dt_s == pytest.approx(0.02)
    assert config.v_min_m_s == pytest.approx(0.5)


def test_stall_and_display_defaults() -> None:
    config = DEFAULT_CONFIG
    assert config.alpha_stall_deg == pytest.approx(14.0)
    assert config.post_stall_slope_per_deg == pytest.approx(0.07)
    assert config.post_stall_drag == "hw_formula"
    assert config.post_stall_drag_slope_per_deg == pytest.approx(0.02)
    assert config.sprite_flip_horizontal is True
    assert config.display_pitch_smoothing_s == pytest.approx(0.15)


def test_startup_log_lists_the_values_in_use() -> None:
    line = format_startup_log(DEFAULT_CONFIG)
    assert "m=1156.7 kg" in line
    assert "S=16.165 m^2" in line
    assert "g=9.80665" in line
    assert "density=isa_troposphere" in line
    assert "alpha_stall=14.0 deg" in line


def test_validate_config_rejects_an_unknown_density_model() -> None:
    with pytest.raises(ValueError, match="density_model"):
        validate_config(Config(density_model="jet_standard"))
