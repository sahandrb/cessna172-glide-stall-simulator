"""Air density used by the glide equations.

Two models, selected by Config.density_model:
- isa_troposphere: the specification's troposphere formula
- constant: sea-level density at every altitude
"""

from __future__ import annotations

from cessna_sim.config import Config

# Specification section 4.4. Valid through the troposphere heights used here.
_ISA_LAPSE_PER_M = 2.2558e-5
_ISA_EXPONENT = 4.2559


def air_density(altitude_m: float, config: Config) -> float:
    """Density in kg/m^3 at geometric altitude in metres."""
    if config.density_model == "constant":
        return config.sea_level_density_kg_m3
    sigma = 1.0 - _ISA_LAPSE_PER_M * altitude_m
    if sigma <= 0.0:
        raise ValueError(
            f"ISA troposphere formula is not valid at altitude {altitude_m:.1f} m"
        )
    return config.sea_level_density_kg_m3 * sigma**_ISA_EXPONENT
