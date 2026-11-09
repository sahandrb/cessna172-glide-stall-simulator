"""Side-view world: camera, ground, clouds, streaks, trails, and the alpha cue.

Nothing here is a flow field from CFD. Streaks are a uniform free stream drawn
opposite the velocity vector.
"""

from __future__ import annotations

import math
import random

import pygame

from cessna_sim.app.theme import GROUND, GROUND_LINE, MUTED, SKY_HORIZON, SKY_TOP, TEXT, font
from cessna_sim.sprite_geometry import rotate_offset


class Camera:
    """Keeps the aircraft in the left-center third and eases toward its altitude."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.aircraft_x = width * 0.32
        self.aircraft_y = height * 0.42
        self.pixels_per_meter = 2.4
        self.follow_altitude = None
        self.tau_s = 0.45

    def update(self, altitude_m: float, dt_s: float) -> None:
        if self.follow_altitude is None:
            self.follow_altitude = altitude_m
            return
        blend = 1.0 - math.exp(-dt_s / self.tau_s)
        self.follow_altitude += (altitude_m - self.follow_altitude) * blend

    def to_screen(self, distance_m: float, altitude_m: float, aircraft_distance: float) -> tuple[float, float]:
        screen_x = self.aircraft_x + (distance_m - aircraft_distance) * self.pixels_per_meter
        screen_y = self.aircraft_y - (altitude_m - self.follow_altitude) * self.pixels_per_meter
        return screen_x, screen_y

    def visible_distance(self, aircraft_distance: float) -> tuple[float, float]:
        left = aircraft_distance + (0.0 - self.aircraft_x) / self.pixels_per_meter
        right = aircraft_distance + (self.width - self.aircraft_x) / self.pixels_per_meter
        return left, right


class CloudField:
    def __init__(self) -> None:
        rng = random.Random(172)
        self.clouds = []
        for _ in range(14):
            self.clouds.append(
                {
                    "r": rng.uniform(-400.0, 2500.0),
                    "h": rng.uniform(40.0, 280.0),
                    "depth": rng.uniform(0.25, 0.7),
                    "span": rng.uniform(70.0, 160.0),
                }
            )


class StreakField:
    def __init__(self) -> None:
        self.points: list[tuple[float, float]] = []
        self._seeded = False

    def update(
        self,
        aircraft_r: float,
        aircraft_h: float,
        airspeed: float,
        gamma_rad: float,
        dt_s: float,
        view_width_m: float,
    ) -> None:
        if not self._seeded:
            rng = random.Random(7)
            for _ in range(48):
                self.points.append(
                    (
                        aircraft_r + rng.uniform(-40.0, view_width_m * 0.7),
                        aircraft_h + rng.uniform(-80.0, 80.0),
                    )
                )
            self._seeded = True
        step = airspeed * dt_s
        cosine = math.cos(gamma_rad)
        sine = math.sin(gamma_rad)
        moved = []
        for distance, altitude in self.points:
            distance -= cosine * step
            altitude -= sine * step
            if distance < aircraft_r - 60.0 or abs(altitude - aircraft_h) > 140.0:
                distance = aircraft_r + view_width_m * 0.75
                altitude = aircraft_h + random.uniform(-80.0, 80.0)
            moved.append((distance, altitude))
        self.points = moved


def draw_sky(screen: pygame.Surface) -> None:
    height = screen.get_height()
    for y in range(height):
        blend = y / max(1, height - 1)
        color = tuple(int(SKY_TOP[channel] + (SKY_HORIZON[channel] - SKY_TOP[channel]) * blend) for channel in range(3))
        pygame.draw.line(screen, color, (0, y), (screen.get_width(), y))


def draw_ground(screen: pygame.Surface, camera: Camera, aircraft_r: float) -> None:
    _, ground_y = camera.to_screen(aircraft_r, 0.0, aircraft_r)
    if ground_y >= screen.get_height():
        return
    top = max(0, int(ground_y))
    pygame.draw.rect(screen, GROUND, (0, top, screen.get_width(), screen.get_height() - top))
    pygame.draw.line(screen, GROUND_LINE, (0, top), (screen.get_width(), top), 2)
    left, right = camera.visible_distance(aircraft_r)
    start = math.floor(left / 100.0) * 100
    label_font = font(14)
    marker = start
    while marker <= right:
        x, y = camera.to_screen(marker, 0.0, aircraft_r)
        pygame.draw.line(screen, (40, 52, 36), (x, y), (x, y + 10), 1)
        if marker % 500 == 0:
            text = label_font.render(f"{marker:.0f} m", True, (230, 236, 220))
            screen.blit(text, (x + 4, y + 12))
        marker += 100


def draw_clouds(screen: pygame.Surface, camera: Camera, clouds: CloudField, aircraft_r: float) -> None:
    for cloud in clouds.clouds:
        parallax_r = aircraft_r + (cloud["r"] - aircraft_r) * cloud["depth"]
        x, y = camera.to_screen(parallax_r, camera.follow_altitude + cloud["h"] * cloud["depth"], aircraft_r)
        span = cloud["span"] * cloud["depth"]
        pygame.draw.ellipse(screen, (236, 242, 246), (x, y, span, span * 0.42))


def draw_trail(
    screen: pygame.Surface,
    camera: Camera,
    aircraft_r: float,
    distances: list[float],
    altitudes: list[float],
    color: tuple[int, int, int],
    width: int,
) -> None:
    if len(distances) < 2:
        return
    points = [camera.to_screen(r, h, aircraft_r) for r, h in zip(distances, altitudes)]
    visible = [point for point in points if -200 <= point[0] <= screen.get_width() + 200]
    if len(visible) >= 2:
        pygame.draw.lines(screen, color, False, visible, width)


def draw_streaks(
    screen: pygame.Surface,
    camera: Camera,
    streaks: StreakField,
    aircraft_r: float,
    gamma_rad: float,
) -> None:
    direction = rotate_offset(14.0, 0.0, math.degrees(gamma_rad))
    for distance, altitude in streaks.points:
        x, y = camera.to_screen(distance, altitude, aircraft_r)
        end = (x - direction[0], y - direction[1])
        pygame.draw.line(screen, (255, 255, 255), (x, y), end, 1)


def draw_alpha_cue(
    screen: pygame.Surface,
    nose: tuple[float, float],
    gamma_deg: float,
    theta_deg: float,
    alpha_deg: float,
) -> None:
    """Arrow along the flight path and an arc across to the fuselage."""
    wind = rotate_offset(1.0, 0.0, gamma_deg)
    tail = (nose[0] + wind[0] * 78, nose[1] + wind[1] * 78)
    head = (nose[0] + wind[0] * 28, nose[1] + wind[1] * 28)
    pygame.draw.line(screen, (255, 244, 210), tail, head, 2)
    tip = rotate_offset(8.0, 0.0, gamma_deg + 150.0)
    tip_b = rotate_offset(8.0, 0.0, gamma_deg - 150.0)
    pygame.draw.line(screen, (255, 244, 210), head, (head[0] + tip[0], head[1] + tip[1]), 2)
    pygame.draw.line(screen, (255, 244, 210), head, (head[0] + tip_b[0], head[1] + tip_b[1]), 2)
    arc_points = []
    start = gamma_deg
    end = theta_deg
    steps = 12
    for step in range(steps + 1):
        angle = start + (end - start) * step / steps
        offset = rotate_offset(36.0, 0.0, angle)
        arc_points.append((nose[0] + offset[0], nose[1] + offset[1]))
    if len(arc_points) >= 2:
        pygame.draw.lines(screen, (255, 196, 96), False, arc_points, 2)
    label = font(16).render(f"alpha = {alpha_deg:.1f} deg", True, TEXT)
    screen.blit(label, (nose[0] + 40, nose[1] - 28))


def draw_altitude_scale(screen: pygame.Surface, camera: Camera) -> None:
    label_font = font(13)
    top_h = camera.follow_altitude - (0 - camera.aircraft_y) / camera.pixels_per_meter
    bottom_h = camera.follow_altitude - (screen.get_height() - camera.aircraft_y) / camera.pixels_per_meter
    low = math.floor(min(top_h, bottom_h) / 100.0) * 100
    high = math.ceil(max(top_h, bottom_h) / 100.0) * 100
    marker = low
    while marker <= high:
        _, y = camera.to_screen(0.0, marker, 0.0)
        pygame.draw.line(screen, (30, 40, 52), (0, y), (14, y), 1)
        text = label_font.render(f"{marker:.0f}", True, MUTED)
        screen.blit(text, (18, y - 8))
        marker += 100


def draw_debug(
    screen: pygame.Surface,
    cg: tuple[float, float],
    gamma_deg: float,
    theta_deg: float,
    alpha_deg: float,
    displayed_theta_deg: float,
) -> None:
    pygame.draw.circle(screen, (255, 80, 80), (int(cg[0]), int(cg[1])), 4)
    horizon_a = (0, cg[1])
    horizon_b = (screen.get_width(), cg[1])
    pygame.draw.line(screen, (180, 200, 220), horizon_a, horizon_b, 1)
    body = rotate_offset(70.0, 0.0, theta_deg)
    path = rotate_offset(70.0, 0.0, gamma_deg)
    pygame.draw.line(screen, (255, 210, 80), cg, (cg[0] + body[0], cg[1] + body[1]), 2)
    pygame.draw.line(screen, (120, 210, 255), cg, (cg[0] + path[0], cg[1] + path[1]), 2)
    text = font(16).render(
        f"alpha {alpha_deg:.2f}   gamma {gamma_deg:.2f}   theta {theta_deg:.2f}   drawn {displayed_theta_deg:.2f}",
        True,
        TEXT,
    )
    screen.blit(text, (16, screen.get_height() - 28))
