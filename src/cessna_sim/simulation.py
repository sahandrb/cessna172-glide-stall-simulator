"""Time integration of the glide equations.

Interactive runs advance one fixed physics step at a time because alpha can
change between steps. Homework part (d) is a single solve_ivp call.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.integrate import solve_ivp

from cessna_sim.aerodynamics import is_stalled, maximum_lift_coefficient, stall_speed
from cessna_sim.atmosphere import air_density
from cessna_sim.config import Config
from cessna_sim.dynamics import aerodynamic_state, derivatives, pitch_angle_rad
from cessna_sim.equilibrium import equilibrium_glide


@dataclass
class Trajectory:
    """Samples of one constant-alpha integration."""

    t: np.ndarray
    airspeed: np.ndarray
    gamma_rad: np.ndarray
    altitude: np.ndarray
    distance: np.ndarray
    alpha_deg: float
    message: str = ""


@dataclass
class SimulationEvent:
    time_s: float
    name: str
    altitude_m: float
    airspeed_m_s: float
    alpha_deg: float


@dataclass
class RunLog:
    """One row per recorded physics sample, plus the event list."""

    t: np.ndarray
    alpha_deg: np.ndarray
    cl: np.ndarray
    cd: np.ndarray
    cm: np.ndarray
    lift_to_drag: np.ndarray
    airspeed: np.ndarray
    stall_speed: np.ndarray
    gamma_deg: np.ndarray
    theta_deg: np.ndarray
    altitude: np.ndarray
    distance: np.ndarray
    density: np.ndarray
    load_factor: np.ndarray
    stall_flag: np.ndarray
    events: list[SimulationEvent] = field(default_factory=list)
    message: str = ""

    @property
    def gamma_rad(self) -> np.ndarray:
        return np.radians(self.gamma_deg)


def _terminal_event(function):
    function.terminal = True
    function.direction = -1
    return function


def _events(config: Config, stop_on_altitude: bool) -> list:
    events = []
    if stop_on_altitude:

        def altitude_event(t, state, alpha_deg, active_config):
            del t, alpha_deg, active_config
            return float(state[2]) - config.h_end_m

        events.append(_terminal_event(altitude_event))

    def speed_event(t, state, alpha_deg, active_config):
        del t, alpha_deg, active_config
        return float(state[0]) - config.v_min_m_s

    events.append(_terminal_event(speed_event))
    return events


def _integrate(
    state0: np.ndarray,
    alpha_deg: float,
    t0: float,
    t1: float,
    config: Config,
    stop_on_altitude: bool,
    t_eval: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, str]:
    solution = solve_ivp(
        derivatives,
        (t0, t1),
        np.asarray(state0, dtype=np.float64),
        method=config.integrator_method,
        t_eval=t_eval,
        rtol=config.rtol,
        atol=config.atol,
        args=(alpha_deg, config),
        events=_events(config, stop_on_altitude),
        dense_output=False,
        max_step=1.0,
    )
    if not solution.success and solution.y.size == 0:
        raise RuntimeError(solution.message)
    message = ""
    if solution.t_events:
        altitude_hits = stop_on_altitude and solution.t_events[0].size > 0
        speed_index = 1 if stop_on_altitude else 0
        speed_hits = solution.t_events[speed_index].size > 0
        if speed_hits and (
            not altitude_hits or solution.t_events[speed_index][0] <= solution.t[-1]
        ):
            if solution.y[0, -1] <= config.v_min_m_s + 1e-6:
                message = (
                    f"Stopped because airspeed fell to {config.v_min_m_s:.1f} m/s "
                    "or below."
                )
        if altitude_hits and not message:
            message = f"Stopped because altitude reached {config.h_end_m:.1f} m."
    return solution.t, solution.y, message


def simulate_constant_alpha(
    alpha_deg: float,
    altitude0_m: float,
    duration_s: float,
    config: Config,
    *,
    stop_on_altitude: bool = False,
    sample_dt_s: float | None = None,
) -> Trajectory:
    """One solve_ivp call at fixed alpha. Initial V and gamma are the equilibrium glide."""
    airspeed0, gamma0 = equilibrium_glide(alpha_deg, altitude0_m, config)
    state0 = np.array([airspeed0, gamma0, altitude0_m, 0.0], dtype=np.float64)
    t_eval = None
    if sample_dt_s is not None:
        count = int(round(duration_s / sample_dt_s)) + 1
        t_eval = np.linspace(0.0, duration_s, count)
    times, states, message = _integrate(
        state0,
        alpha_deg,
        0.0,
        duration_s,
        config,
        stop_on_altitude,
        t_eval,
    )
    return Trajectory(
        t=np.asarray(times, dtype=np.float64),
        airspeed=np.asarray(states[0], dtype=np.float64),
        gamma_rad=np.asarray(states[1], dtype=np.float64),
        altitude=np.asarray(states[2], dtype=np.float64),
        distance=np.asarray(states[3], dtype=np.float64),
        alpha_deg=alpha_deg,
        message=message,
    )


def _empty_columns() -> dict[str, list[float]]:
    keys = (
        "t",
        "alpha_deg",
        "cl",
        "cd",
        "cm",
        "lift_to_drag",
        "airspeed",
        "stall_speed",
        "gamma_deg",
        "theta_deg",
        "altitude",
        "distance",
        "density",
        "load_factor",
        "stall_flag",
    )
    return {key: [] for key in keys}


class GlideRun:
    """Interactive glide. Call step() once per physics interval with alpha held fixed."""

    def __init__(self, altitude0_m: float, alpha_deg: float, config: Config) -> None:
        airspeed, gamma = equilibrium_glide(alpha_deg, altitude0_m, config)
        self.config = config
        self.alpha_deg = float(alpha_deg)
        self.state = np.array([airspeed, gamma, altitude0_m, 0.0], dtype=np.float64)
        self.time_s = 0.0
        self.message = ""
        self.finished = False
        self._columns = _empty_columns()
        self.events: list[SimulationEvent] = []
        self._stalled = is_stalled(self.alpha_deg, config)
        self._record_event("engine_failure")
        if self._stalled:
            self._record_event("stall_onset")
        self._record_row()

    @property
    def airspeed(self) -> float:
        return float(self.state[0])

    @property
    def gamma_rad(self) -> float:
        return float(self.state[1])

    @property
    def altitude(self) -> float:
        return float(self.state[2])

    @property
    def distance(self) -> float:
        return float(self.state[3])

    def _record_event(self, name: str) -> None:
        self.events.append(
            SimulationEvent(
                time_s=self.time_s,
                name=name,
                altitude_m=self.altitude,
                airspeed_m_s=self.airspeed,
                alpha_deg=self.alpha_deg,
            )
        )

    def _record_row(self) -> None:
        aero = aerodynamic_state(self.alpha_deg, self.airspeed, self.altitude, self.config)
        cl_max = maximum_lift_coefficient(self.config)
        vs = stall_speed(aero["weight_n"], aero["rho"], self.config.wing_area_m2, cl_max)
        theta = pitch_angle_rad(self.alpha_deg, self.gamma_rad)
        row = {
            "t": self.time_s,
            "alpha_deg": self.alpha_deg,
            "cl": aero["CL"],
            "cd": aero["CD"],
            "cm": aero["Cm"],
            "lift_to_drag": aero["L_over_D"],
            "airspeed": self.airspeed,
            "stall_speed": vs,
            "gamma_deg": math_degrees(self.gamma_rad),
            "theta_deg": math_degrees(theta),
            "altitude": self.altitude,
            "distance": self.distance,
            "density": aero["rho"],
            "load_factor": aero["load_factor"],
            "stall_flag": 1.0 if is_stalled(self.alpha_deg, self.config) else 0.0,
        }
        for key, value in row.items():
            self._columns[key].append(value)

    def _check_stall_transition(self) -> None:
        stalled = is_stalled(self.alpha_deg, self.config)
        if stalled and not self._stalled:
            self._record_event("stall_onset")
        elif self._stalled and not stalled:
            self._record_event("stall_recovery")
        self._stalled = stalled

    def set_alpha(self, alpha_deg: float) -> None:
        """Store the alpha that the next step will hold constant.

        Alpha is updated after a step, so a stall transition is logged at the
        time the new alpha takes effect, before the next integration.
        """
        limited = min(self.config.alpha_max_deg, max(self.config.alpha_min_deg, alpha_deg))
        self.alpha_deg = limited
        self._check_stall_transition()

    def step(self, dt_s: float) -> None:
        """Integrate from t to t+dt at the current alpha, then log the new state."""
        if self.finished:
            return
        times, states, message = _integrate(
            self.state,
            self.alpha_deg,
            self.time_s,
            self.time_s + dt_s,
            self.config,
            True,
            None,
        )
        self.time_s = float(times[-1])
        self.state = np.asarray(states[:, -1], dtype=np.float64)
        self._record_row()
        reached_ground = self.altitude <= self.config.h_end_m + 1e-6
        reached_time_message = message
        if reached_ground or reached_time_message:
            self.finished = True
            self.message = reached_time_message or (
                f"Stopped because altitude reached {self.config.h_end_m:.1f} m."
            )
            self._record_event("end")

    def finish(self, message: str) -> None:
        """Stop a run that hit the time limit rather than an event."""
        if self.finished:
            return
        self.finished = True
        self.message = message
        self._record_event("end")

    def log(self) -> RunLog:
        columns = {
            key: np.asarray(values, dtype=np.float64) for key, values in self._columns.items()
        }
        return RunLog(events=list(self.events), message=self.message, **columns)


def math_degrees(radians: float) -> float:
    return math.degrees(radians)


def initial_state_is_finite(alpha_deg: float, altitude_m: float, config: Config) -> str:
    """Empty string when a run may start, otherwise the reason to refuse."""
    try:
        equilibrium_glide(alpha_deg, altitude_m, config)
    except ValueError as exc:
        return str(exc)
    if not math.isfinite(air_density(altitude_m, config)):
        return "Air density is not finite at the initial altitude."
    return ""
