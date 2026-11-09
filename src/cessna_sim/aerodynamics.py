"""Homework aerodynamic coefficients, with the stall extension of section 6.

Angles that enter these formulas are in degrees. Lift and drag are dimensionless
coefficients; the equations of motion convert them to forces.
"""

from __future__ import annotations

import math

from cessna_sim.config import Config

# Homework polar, section 4.2. Alpha is in degrees.
CL_INTERCEPT = 0.20
CL_SLOPE_PER_DEG = 0.096
CD_PARASITE = 0.032
CD_INDUCED = 0.0524
CM_SLOPE_PER_DEG = -0.01449
CM_TRIM_ALPHA_DEG = 2.25


def lift_coefficient_linear(alpha_deg: float) -> float:
    """Homework line CL = 0.20 + 0.096 * alpha. No stall break."""
    return CL_INTERCEPT + CL_SLOPE_PER_DEG * alpha_deg


def maximum_lift_coefficient(config: Config) -> float:
    """CL at alpha_stall on the homework line. Continuous with the stalled branch."""
    return lift_coefficient_linear(config.alpha_stall_deg)


def lift_coefficient(alpha_deg: float, config: Config) -> float:
    """Section 6.2. Linear at and below alpha_stall; the stall slope replaces it above."""
    if alpha_deg <= config.alpha_stall_deg:
        return lift_coefficient_linear(alpha_deg)
    cl_max = maximum_lift_coefficient(config)
    return cl_max - config.post_stall_slope_per_deg * (alpha_deg - config.alpha_stall_deg)


def drag_coefficient(cl: float, alpha_deg: float, config: Config) -> float:
    """Section 4.2 drag polar, plus the optional assumed post-stall rise."""
    cd = CD_PARASITE + CD_INDUCED * cl * cl
    if (
        config.post_stall_drag == "assumed_rise"
        and alpha_deg > config.alpha_stall_deg
    ):
        cd += config.post_stall_drag_slope_per_deg * (alpha_deg - config.alpha_stall_deg)
    return cd


def pitching_moment_coefficient(alpha_deg: float) -> float:
    """Cm about the homework trim angle. Display and plots only; not in the EOM."""
    return CM_SLOPE_PER_DEG * (alpha_deg - CM_TRIM_ALPHA_DEG)


def lift_to_drag(cl: float, cd: float) -> float:
    if cd == 0.0:
        return math.inf
    return cl / cd


def maximum_lift_to_drag() -> tuple[float, float, float]:
    """CL*, (L/D)max, and alpha* from the section 4.6 formulas.

    The three numbers are computed here. They are not stored as literals.
    """
    cl_star = math.sqrt(CD_PARASITE / CD_INDUCED)
    ld_max = 1.0 / (2.0 * math.sqrt(CD_PARASITE * CD_INDUCED))
    alpha_star_deg = (cl_star - CL_INTERCEPT) / CL_SLOPE_PER_DEG
    return cl_star, ld_max, alpha_star_deg


def stall_speed(weight_n: float, density: float, wing_area_m2: float, cl_max: float) -> float:
    """1-g stall speed, Vs = sqrt(2 W / (rho S CL_max))."""
    return math.sqrt((2.0 * weight_n) / (density * wing_area_m2 * cl_max))


def is_stalled(alpha_deg: float, config: Config) -> bool:
    """Strictly above alpha_stall, matching section 6.5."""
    return alpha_deg > config.alpha_stall_deg
