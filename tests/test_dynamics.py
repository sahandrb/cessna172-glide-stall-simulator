"""Equilibrium is a stationary point of the equations of motion."""

import numpy as np
import pytest

from cessna_sim.config import Config
from cessna_sim.dynamics import derivatives
from cessna_sim.equilibrium import EquilibriumError, equilibrium_glide


def test_equilibrium_derivatives_are_zero() -> None:
    config = Config(density_model="constant")
    alpha = 6.0
    altitude = 1000.0
    airspeed, gamma = equilibrium_glide(alpha, altitude, config)
    rates = derivatives(0.0, np.array([airspeed, gamma, altitude, 0.0]), alpha, config)
    assert rates[0] == pytest.approx(0.0, abs=1e-8)
    assert rates[1] == pytest.approx(0.0, abs=1e-8)
    assert rates[2] == pytest.approx(airspeed * np.sin(gamma))
    assert rates[3] == pytest.approx(airspeed * np.cos(gamma))


def test_negative_lift_is_refused() -> None:
    config = Config()
    with pytest.raises(EquilibriumError):
        equilibrium_glide(-5.0, 1000.0, config)
