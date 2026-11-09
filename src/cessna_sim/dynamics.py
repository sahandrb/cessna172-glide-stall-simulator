"""Point-mass longitudinal equations with thrust equal to zero.

State vector x = [V, gamma, h, r]. gamma, and the theta returned for drawing,
are in radians. alpha_deg is the aerodynamic angle in degrees.
"""

from __future__ import annotations

import math

import numpy as np

from cessna_sim.aerodynamics import (
    drag_coefficient,
    lift_coefficient,
    pitching_moment_coefficient,
)
from cessna_sim.atmosphere import air_density
from cessna_sim.config import Config


def pitch_angle_rad(alpha_deg: float, gamma_rad: float) -> float:
    """theta = alpha + gamma, with both angles in radians."""
    return math.radians(alpha_deg) + gamma_rad


def aerodynamic_state(alpha_deg: float, airspeed_m_s: float, altitude_m: float, config: Config) -> dict[str, float]:
    """Forces and coefficients at one instant. Cm does not enter the derivatives."""
    density = air_density(altitude_m, config)
    cl = lift_coefficient(alpha_deg, config)
    cd = drag_coefficient(cl, alpha_deg, config)
    dynamic_pressure = 0.5 * density * airspeed_m_s * airspeed_m_s
    lift_n = dynamic_pressure * config.wing_area_m2 * cl
    drag_n = dynamic_pressure * config.wing_area_m2 * cd
    weight_n = config.mass_kg * config.gravity_m_s2
    load_factor = lift_n / weight_n if weight_n != 0.0 else math.nan
    return {
        "rho": density,
        "CL": cl,
        "CD": cd,
        "Cm": pitching_moment_coefficient(alpha_deg),
        "L_over_D": cl / cd if cd != 0.0 else math.inf,
        "lift_n": lift_n,
        "drag_n": drag_n,
        "weight_n": weight_n,
        "load_factor": load_factor,
        "dynamic_pressure": dynamic_pressure,
    }


def derivatives(t: float, state: np.ndarray, alpha_deg: float, config: Config) -> np.ndarray:
    """d/dt [V, gamma, h, r] from section 4.3.

    The speed floor avoids a division by zero if a solver step passes the
    terminal V event. The simulation still stops and reports that event.
    """
    del t  # autonomous; solve_ivp passes time anyway
    airspeed = float(state[0])
    gamma = float(state[1])
    altitude = float(state[2])
    speed_for_force = airspeed if airspeed > config.v_min_m_s else config.v_min_m_s
    aero = aerodynamic_state(alpha_deg, speed_for_force, altitude, config)
    mass = config.mass_kg
    gravity = config.gravity_m_s2
    d_airspeed = -aero["drag_n"] / mass - gravity * math.sin(gamma)
    d_gamma = (aero["lift_n"] - aero["weight_n"] * math.cos(gamma)) / (mass * speed_for_force)
    d_altitude = airspeed * math.sin(gamma)
    d_range = airspeed * math.cos(gamma)
    return np.array([d_airspeed, d_gamma, d_altitude, d_range], dtype=np.float64)
