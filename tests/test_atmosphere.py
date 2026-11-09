"""Density models from section 4.4."""

import pytest

from cessna_sim.atmosphere import air_density
from cessna_sim.config import DEFAULT_CONFIG, Config


def test_isa_sea_level_and_formula() -> None:
    assert air_density(0.0, DEFAULT_CONFIG) == pytest.approx(1.225)
    altitude = 1000.0
    expected = 1.225 * (1.0 - 2.2558e-5 * altitude) ** 4.2559
    assert air_density(altitude, DEFAULT_CONFIG) == pytest.approx(expected)


def test_constant_density_ignores_altitude() -> None:
    config = Config(density_model="constant")
    assert air_density(0.0, config) == pytest.approx(1.225)
    assert air_density(5000.0, config) == pytest.approx(1.225)
