"""Engineering figures for the homework parts and for a completed glide run."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np

from cessna_sim.aerodynamics import (
    drag_coefficient,
    lift_coefficient,
    lift_coefficient_linear,
    lift_to_drag,
    maximum_lift_to_drag,
    pitching_moment_coefficient,
)
from cessna_sim.config import DEFAULT_CONFIG, Config
from cessna_sim.equilibrium import equilibrium_vs_altitude
from cessna_sim.simulation import RunLog, Trajectory, simulate_constant_alpha

_BLUE = "#1f4e79"
_TEAL = "#2a6f6f"
_GOLD = "#c47b2b"
_STALL = "#b33a3a"
_GREY = "#5c6670"


def _pyplot():
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "axes.grid": True,
            "grid.alpha": 0.35,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "font.size": 10,
        }
    )
    return plt


def _alpha_grid(config: Config) -> np.ndarray:
    return np.linspace(config.alpha_min_deg, config.alpha_max_deg, 441)


def _stall_decoration(axis, onsets: list[float], intervals: list[tuple[float, float]]) -> None:
    for start, end in intervals:
        axis.axvspan(start, end, color=_STALL, alpha=0.12, linewidth=0)
    for onset in onsets:
        axis.axvline(onset, color=_STALL, linestyle="--", linewidth=1.0)
        axis.text(
            onset,
            0.98,
            f"stall onset t = {onset:.2f} s",
            transform=axis.get_xaxis_transform(),
            rotation=90,
            va="top",
            ha="right",
            color=_STALL,
            fontsize=8,
        )


def _highlight_alpha(axis, low: float | None, high: float | None) -> None:
    if low is None or high is None:
        return
    if abs(high - low) < 1e-6:
        axis.axvline(low, color=_GOLD, linewidth=1.2, label="run alpha")
    else:
        axis.axvspan(low, high, color=_GOLD, alpha=0.18, label="run alpha")


def figure_coefficients(
    config: Config = DEFAULT_CONFIG,
    alpha_low: float | None = None,
    alpha_high: float | None = None,
):
    """Figure 1. Linear CL is dashed; the stall model is solid."""
    plt = _pyplot()
    alpha = _alpha_grid(config)
    cl_linear = np.array([lift_coefficient_linear(a) for a in alpha])
    cl_stall = np.array([lift_coefficient(a, config) for a in alpha])
    cd = np.array([drag_coefficient(c, a, config) for c, a in zip(cl_stall, alpha)])
    cm = np.array([pitching_moment_coefficient(a) for a in alpha])

    figure, axes = plt.subplots(3, 1, figsize=(8.0, 8.5), sharex=True)
    axes[0].plot(alpha, cl_linear, linestyle="--", color=_GREY, label="HW linear CL")
    axes[0].plot(alpha, cl_stall, color=_BLUE, label="stall model CL")
    axes[0].axvline(config.alpha_stall_deg, color=_STALL, linestyle=":", label="alpha stall")
    axes[0].set_ylabel("CL")
    axes[0].set_title("Figure 1 — Lift, drag, and pitching moment")
    axes[1].plot(alpha, cd, color=_TEAL)
    axes[1].set_ylabel("CD")
    axes[2].plot(alpha, cm, color=_BLUE)
    axes[2].set_ylabel("Cm")
    axes[2].set_xlabel("angle of attack (deg)")
    for axis in axes:
        axis.axvline(config.alpha_stall_deg, color=_STALL, linestyle=":", linewidth=1.0)
        _highlight_alpha(axis, alpha_low, alpha_high)
    axes[0].legend(frameon=False)
    figure.tight_layout()
    return figure


def figure_lift_to_drag(config: Config = DEFAULT_CONFIG):
    """Figure 2. (L/D)max and alpha* come from the polar formulas."""
    plt = _pyplot()
    _, ld_max, alpha_star = maximum_lift_to_drag()
    alpha = _alpha_grid(config)
    ratios = []
    for angle in alpha:
        cl = lift_coefficient(float(angle), config)
        cd = drag_coefficient(cl, float(angle), config)
        ratios.append(lift_to_drag(cl, cd))
    figure, axis = plt.subplots(figsize=(8.0, 4.6))
    axis.plot(alpha, ratios, color=_BLUE, label="L/D")
    axis.axvline(alpha_star, color=_GOLD, linestyle="--", label=f"alpha* = {alpha_star:.2f} deg")
    axis.axhline(ld_max, color=_TEAL, linestyle="--", label=f"(L/D)max = {ld_max:.2f}")
    axis.plot([alpha_star], [ld_max], "o", color=_STALL)
    axis.set_xlabel("angle of attack (deg)")
    axis.set_ylabel("L/D")
    axis.set_title("Figure 2 — Lift-to-drag ratio")
    axis.legend(frameon=False)
    figure.tight_layout()
    return figure


def figure_equilibrium(config: Config = DEFAULT_CONFIG):
    """Figure 3. Primary curve at alpha*, plus the configured family."""
    plt = _pyplot()
    _, _, alpha_star = maximum_lift_to_drag()
    primary = config.equilibrium_alpha_deg
    if primary is None:
        primary = alpha_star
    altitudes = np.linspace(0.0, config.equilibrium_altitude_max_m, 81)
    figure, axes = plt.subplots(2, 1, figsize=(8.0, 7.0), sharex=True)
    speed, gamma = equilibrium_vs_altitude(primary, altitudes, config)
    axes[0].plot(altitudes, speed, color=_BLUE, linewidth=2.2, label=f"alpha = {primary:.2f} deg")
    axes[1].plot(
        altitudes,
        np.degrees(gamma),
        color=_BLUE,
        linewidth=2.2,
        label=f"alpha = {primary:.2f} deg",
    )
    for angle in config.equilibrium_family_alphas_deg:
        if abs(angle - primary) < 0.05:
            continue
        try:
            family_speed, family_gamma = equilibrium_vs_altitude(angle, altitudes, config)
        except ValueError:
            continue
        axes[0].plot(altitudes, family_speed, linewidth=1.0, label=f"{angle:.0f} deg")
        axes[1].plot(altitudes, np.degrees(family_gamma), linewidth=1.0, label=f"{angle:.0f} deg")
    axes[0].set_ylabel("V_eq (m/s)")
    axes[0].set_title("Figure 3 — Equilibrium glide versus altitude")
    axes[1].set_ylabel("gamma_eq (deg)")
    axes[1].set_xlabel("altitude (m)")
    axes[0].legend(frameon=False, ncol=2)
    axes[1].legend(frameon=False, ncol=2)
    figure.tight_layout()
    return figure


def figure_time_history(
    time_s: np.ndarray,
    airspeed: np.ndarray,
    gamma_deg: np.ndarray,
    altitude: np.ndarray,
    distance: np.ndarray,
    onsets: list[float] | None = None,
    intervals: list[tuple[float, float]] | None = None,
):
    """Figure 4. Four homework time histories."""
    plt = _pyplot()
    onsets = onsets or []
    intervals = intervals or []
    figure, axes = plt.subplots(2, 2, figsize=(9.5, 7.0))
    series = (
        (axes[0, 0], airspeed, "V (m/s)", "Airspeed"),
        (axes[0, 1], gamma_deg, "gamma (deg)", "Flight-path angle"),
        (axes[1, 0], altitude, "h (m)", "Altitude"),
        (axes[1, 1], distance, "r (m)", "Horizontal distance"),
    )
    for axis, values, ylabel, title in series:
        axis.plot(time_s, values, color=_BLUE)
        axis.set_xlabel("time (s)")
        axis.set_ylabel(ylabel)
        axis.set_title(title)
        _stall_decoration(axis, onsets, intervals)
    figure.suptitle("Figure 4 — Time histories")
    figure.tight_layout()
    return figure


def figure_run_signals(
    log: RunLog,
    onsets: list[float] | None = None,
    intervals: list[tuple[float, float]] | None = None,
):
    """Figure 5. Alpha, CL, L/D, and airspeed with stall speed."""
    plt = _pyplot()
    onsets = onsets or []
    intervals = intervals or []
    figure, axes = plt.subplots(2, 2, figsize=(9.5, 7.0))
    panels = (
        (axes[0, 0], log.alpha_deg, "alpha (deg)", "Angle of attack"),
        (axes[0, 1], log.cl, "CL", "Lift coefficient"),
        (axes[1, 0], log.lift_to_drag, "L/D", "Lift-to-drag ratio"),
    )
    for axis, values, ylabel, title in panels:
        axis.plot(log.t, values, color=_BLUE)
        axis.set_xlabel("time (s)")
        axis.set_ylabel(ylabel)
        axis.set_title(title)
        _stall_decoration(axis, onsets, intervals)
    axes[1, 1].plot(log.t, log.airspeed, color=_BLUE, label="V")
    axes[1, 1].plot(log.t, log.stall_speed, color=_STALL, linestyle="--", label="Vs")
    axes[1, 1].set_xlabel("time (s)")
    axes[1, 1].set_ylabel("speed (m/s)")
    axes[1, 1].set_title("Airspeed and stall speed")
    axes[1, 1].legend(frameon=False)
    _stall_decoration(axes[1, 1], onsets, intervals)
    figure.suptitle("Figure 5 — Run signals")
    figure.tight_layout()
    return figure


def stall_onsets(log: RunLog) -> list[float]:
    return [event.time_s for event in log.events if event.name == "stall_onset"]


def stalled_intervals(log: RunLog) -> list[tuple[float, float]]:
    """Closed intervals where stall_flag is 1, using sample times."""
    intervals: list[tuple[float, float]] = []
    start: float | None = None
    for time_s, flag in zip(log.t, log.stall_flag):
        if flag >= 0.5 and start is None:
            start = float(time_s)
        elif flag < 0.5 and start is not None:
            intervals.append((start, float(time_s)))
            start = None
    if start is not None:
        intervals.append((start, float(log.t[-1])))
    return intervals


def save_figure(figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=300, bbox_inches="tight")
    figure.clf()
    import matplotlib.pyplot as plt

    plt.close(figure)


def homework_part_d(config: Config = DEFAULT_CONFIG) -> Trajectory:
    """Constant-alpha 0..10 s run. The altitude stop is intentionally off."""
    return simulate_constant_alpha(
        config.default_alpha_deg,
        config.hw_part_d_h0_m,
        config.hw_part_d_duration_s,
        config,
        stop_on_altitude=False,
        sample_dt_s=config.hw_part_d_sample_dt_s,
    )


def write_homework_plots(
    output_dir: Path | None = None,
    config: Config = DEFAULT_CONFIG,
) -> Path:
    """Write figures 1–4 for a headless homework check."""
    if output_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("outputs") / f"hw_{stamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectory = homework_part_d(config)
    alpha = config.default_alpha_deg
    figures = {
        "figure1_coefficients.png": figure_coefficients(config, alpha, alpha),
        "figure2_lift_to_drag.png": figure_lift_to_drag(config),
        "figure3_equilibrium.png": figure_equilibrium(config),
        "figure4_time_history.png": figure_time_history(
            trajectory.t,
            trajectory.airspeed,
            np.degrees(trajectory.gamma_rad),
            trajectory.altitude,
            trajectory.distance,
        ),
    }
    for name, figure in figures.items():
        save_figure(figure, output_dir / name)
    return output_dir


def show_run_plots(log: RunLog, config: Config = DEFAULT_CONFIG) -> None:
    """Open figures 1–5 for the results screen. Blocks until the windows close."""
    onsets = stall_onsets(log)
    intervals = stalled_intervals(log)
    alpha_low = float(np.min(log.alpha_deg))
    alpha_high = float(np.max(log.alpha_deg))
    figure_coefficients(config, alpha_low, alpha_high)
    figure_lift_to_drag(config)
    figure_equilibrium(config)
    figure_time_history(
        log.t,
        log.airspeed,
        log.gamma_deg,
        log.altitude,
        log.distance,
        onsets,
        intervals,
    )
    figure_run_signals(log, onsets, intervals)
    plt = _pyplot()
    plt.show()


def export_run_plots(log: RunLog, output_dir: Path, config: Config = DEFAULT_CONFIG) -> None:
    """PNG copies of figures 1–5."""
    onsets = stall_onsets(log)
    intervals = stalled_intervals(log)
    alpha_low = float(np.min(log.alpha_deg))
    alpha_high = float(np.max(log.alpha_deg))
    figures = {
        "figure1_coefficients.png": figure_coefficients(config, alpha_low, alpha_high),
        "figure2_lift_to_drag.png": figure_lift_to_drag(config),
        "figure3_equilibrium.png": figure_equilibrium(config),
        "figure4_time_history.png": figure_time_history(
            log.t,
            log.airspeed,
            log.gamma_deg,
            log.altitude,
            log.distance,
            onsets,
            intervals,
        ),
        "figure5_run_signals.png": figure_run_signals(log, onsets, intervals),
    }
    for name, figure in figures.items():
        save_figure(figure, output_dir / name)
