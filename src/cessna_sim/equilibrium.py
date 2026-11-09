"""Steady glide at constant angle of attack. Homework part (c)."""

from __future__ import annotations

import math

import numpy as np

from cessna_sim.aerodynamics import drag_coefficient, lift_coefficient
from cessna_sim.atmosphere import air_density
from cessna_sim.config import Config


class EquilibriumError(ValueError):
    """Raised when a steady glide does not exist at the requested alpha."""


def equilibrium_glide(alpha_deg: float, altitude_m: float, config: Config) -> tuple[float, float]:
    """Return (V_eq, gamma_eq) with gamma in radians.

    tan(gamma) = -CD/CL and V comes from lift balancing the weight component.
    CL must be positive.
    """
    cl = lift_coefficient(alpha_deg, config)
    if cl <= 0.0:
        raise EquilibriumError(
            f"CL is {cl:.4f} at alpha {alpha_deg:.2f} deg. A steady glide needs CL > 0."
        )
    cd = drag_coefficient(cl, alpha_deg, config)
    gamma = -math.atan(cd / cl)
    weight = config.mass_kg * config.gravity_m_s2
    density = air_density(altitude_m, config)
    airspeed = math.sqrt(
        (2.0 * weight * math.cos(gamma)) / (density * config.wing_area_m2 * cl)
    )
    return airspeed, gamma


def equilibrium_vs_altitude(
    alpha_deg: float,
    altitudes_m: np.ndarray,
    config: Config,
) -> tuple[np.ndarray, np.ndarray]:
    """V_eq and gamma_eq sampled over an altitude array."""
    speeds = np.empty(len(altitudes_m), dtype=np.float64)
    gammas = np.empty(len(altitudes_m), dtype=np.float64)
    for index, altitude in enumerate(altitudes_m):
        speed, gamma = equilibrium_glide(alpha_deg, float(altitude), config)
        speeds[index] = speed
        gammas[index] = gamma
    return speeds, gammas
