"""Corner readout. Values are the true aerodynamic state, not the smoothed drawing."""

from __future__ import annotations

import math

import pygame

from cessna_sim.aerodynamics import is_stalled, maximum_lift_coefficient, stall_speed
from cessna_sim.app.theme import MUTED, OK, PANEL, PANEL_LINE, STALL, TEXT, mono
from cessna_sim.config import Config
from cessna_sim.dynamics import aerodynamic_state, pitch_angle_rad

KNOT = 1852.0 / 3600.0


def _snapshot(
    time_s: float,
    alpha_deg: float,
    airspeed: float,
    gamma_rad: float,
    altitude: float,
    distance: float,
    config: Config,
) -> list[str]:
    aero = aerodynamic_state(alpha_deg, airspeed, altitude, config)
    cl_max = maximum_lift_coefficient(config)
    vs = stall_speed(aero["weight_n"], aero["rho"], config.wing_area_m2, cl_max)
    theta = pitch_angle_rad(alpha_deg, gamma_rad)
    load = max(aero["load_factor"], 0.0)
    vs_n = vs * math.sqrt(load) if load > 0.0 else vs
    stalled = is_stalled(alpha_deg, config)
    return [
        f"t  {time_s:8.2f} s",
        f"V  {airspeed:8.2f} m/s   {airspeed / KNOT:6.1f} kt",
        f"Vs {vs:8.2f} m/s   Vs_n {vs_n:5.1f}",
        f"h  {altitude:8.1f} m",
        f"r  {distance:8.1f} m",
        f"alpha {alpha_deg:6.2f} deg",
        f"gamma {math.degrees(gamma_rad):6.2f} deg",
        f"theta {math.degrees(theta):6.2f} deg",
        f"CL {aero['CL']:7.3f}   CD {aero['CD']:6.3f}",
        f"Cm {aero['Cm']:7.3f}   L/D {aero['L_over_D']:5.2f}",
        f"sink {-airspeed * math.sin(gamma_rad):6.2f} m/s",
        "STALL" if stalled else "OK",
    ]


def draw_dashboard(
    screen: pygame.Surface,
    lines: list[str],
    stalled: bool,
    flash_on: bool,
) -> None:
    width = 330
    height = 268
    panel = pygame.Surface((width, height), pygame.SRCALPHA)
    panel.fill((*PANEL, 220))
    pygame.draw.rect(panel, PANEL_LINE, panel.get_rect(), 1)
    font = mono(15)
    for index, line in enumerate(lines[:-1]):
        panel.blit(font.render(line, True, TEXT), (12, 8 + index * 18))
    flag = lines[-1]
    flag_color = STALL if stalled and flash_on else (OK if not stalled else (120, 40, 40))
    panel.blit(font.render(flag, True, flag_color), (12, 8 + (len(lines) - 1) * 18))
    note = mono(12).render("Assumption: stall model (see docs)", True, MUTED)
    panel.blit(note, (12, height - 22))
    screen.blit(panel, (screen.get_width() - width - 16, 16))


def readout_lines(
    time_s: float,
    alpha_deg: float,
    airspeed: float,
    gamma_rad: float,
    altitude: float,
    distance: float,
    config: Config,
) -> list[str]:
    return _snapshot(time_s, alpha_deg, airspeed, gamma_rad, altitude, distance, config)
