"""Owner-editable configuration.

Every value the specification marks CONFIG lives here. Homework polynomial
coefficients stay in the aerodynamics module; they are the course model, not
runtime settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def project_root() -> Path:
    """Repository root (the directory that contains src/ and assets/)."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    """Constants for the glide test.

    Sprite fields describe the supplied PNG after it is prepared: flipped so
    the nose points right, leveled once, and with the drawn propeller masked
    out. Only the procedural propeller is drawn.
    """

    mass_kg: float = 1156.7
    wing_area_m2: float = 16.165
    gravity_m_s2: float = 9.80665
    density_model: str = "isa_troposphere"
    sea_level_density_kg_m3: float = 1.225

    alpha_min_deg: float = -2.0
    alpha_max_deg: float = 20.0
    alpha_rate_deg_per_s: float = 4.0
    default_alpha_deg: float = 6.0

    default_h0_m: float = 1000.0
    h0_min_m: float = 50.0
    h0_max_m: float = 5000.0
    h_end_m: float = 10.0
    default_t_max_s: float = 300.0

    integrator_method: str = "RK23"
    rtol: float = 1e-6
    atol: float = 1e-8
    physics_dt_s: float = 0.02
    v_min_m_s: float = 0.5

    alpha_stall_deg: float = 14.0
    post_stall_slope_per_deg: float = 0.07
    post_stall_drag: str = "hw_formula"
    post_stall_drag_slope_per_deg: float = 0.02

    # None means the equilibrium-altitude plot uses alpha at (L/D)max.
    equilibrium_alpha_deg: float | None = None
    equilibrium_altitude_max_m: float = 5000.0
    equilibrium_family_alphas_deg: tuple[float, ...] = (0.0, 6.0, 10.0, 14.0)

    hw_part_d_h0_m: float = 10.0
    hw_part_d_duration_s: float = 10.0
    hw_part_d_sample_dt_s: float = 0.01

    phase_normal_s: float = 3.0
    phase_failure_banner_s: float = 2.0
    prop_spindown_s: float = 1.5
    # Airspeed at which the looping wind cue reaches full volume.
    wind_reference_m_s: float = 45.0

    sprite_flip_horizontal: bool = True
    sprite_level_correction_deg: float = 0.0
    aircraft_display_length_px: int = 360
    # Source-image pixels, nose still pointing left, before flip and level.
    prop_hub_source_px: tuple[float, float] = (40.0, 293.0)
    prop_mask_radius_px: float = 22.0
    # Prepared-image pixels, nose pointing right, level correction applied.
    # CG is one third of the fuselage aft of the nose, just under the wing.
    cg_px: tuple[float, float] = (852.67, 181.0)
    prop_hub_px: tuple[float, float] = (1239.0, 293.0)
    display_pitch_smoothing_s: float = 0.15

    window_width_px: int = 1280
    window_height_px: int = 720


DEFAULT_CONFIG = Config()


def validate_config(config: Config) -> None:
    """Raise ValueError when a setting cannot be used by the simulator."""
    if config.density_model not in {"isa_troposphere", "constant"}:
        raise ValueError(
            "density_model must be 'isa_troposphere' or 'constant', "
            f"got {config.density_model!r}"
        )
    if config.post_stall_drag not in {"hw_formula", "assumed_rise"}:
        raise ValueError(
            "post_stall_drag must be 'hw_formula' or 'assumed_rise', "
            f"got {config.post_stall_drag!r}"
        )
    if config.mass_kg <= 0.0 or config.wing_area_m2 <= 0.0:
        raise ValueError("mass_kg and wing_area_m2 must be positive")
    if config.alpha_min_deg >= config.alpha_max_deg:
        raise ValueError("alpha_min_deg must be below alpha_max_deg")
    if not config.alpha_min_deg <= config.default_alpha_deg <= config.alpha_max_deg:
        raise ValueError("default_alpha_deg is outside the input range")
    if config.h0_min_m <= 0.0 or config.h0_min_m >= config.h0_max_m:
        raise ValueError("altitude limits must satisfy 0 < h0_min_m < h0_max_m")
    if not config.h0_min_m <= config.default_h0_m <= config.h0_max_m:
        raise ValueError("default_h0_m is outside the altitude range")
    if config.h_end_m <= 0.0:
        raise ValueError("h_end_m must be positive")
    if config.physics_dt_s <= 0.0 or config.rtol <= 0.0 or config.atol <= 0.0:
        raise ValueError("integrator tolerances and physics_dt_s must be positive")
    if config.v_min_m_s <= 0.0:
        raise ValueError("v_min_m_s must be positive")
    if config.display_pitch_smoothing_s < 0.0:
        raise ValueError("display_pitch_smoothing_s must be zero or positive")
    if config.wind_reference_m_s <= 0.0:
        raise ValueError("wind_reference_m_s must be positive")
    if config.aircraft_display_length_px <= 0:
        raise ValueError("aircraft_display_length_px must be positive")


def format_startup_log(config: Config) -> str:
    """One line listing the constants the run will actually use."""
    validate_config(config)
    return (
        "Cessna 172 glide sim | "
        f"m={config.mass_kg:.1f} kg | "
        f"S={config.wing_area_m2:.3f} m^2 | "
        f"g={config.gravity_m_s2:.5f} | "
        f"density={config.density_model} | "
        f"alpha_stall={config.alpha_stall_deg:.1f} deg"
    )
