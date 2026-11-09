"""Procedural propeller. The drawing in the PNG is masked out and never shown."""

from __future__ import annotations

import pygame

from cessna_sim.config import Config
from cessna_sim.sprite_geometry import rotate_offset


class Propeller:
    def __init__(self) -> None:
        self.spin_deg = 18.0
        self._fast_deg_per_s = 1400.0

    def rate(self, phase: str, phase_time_s: float, config: Config) -> float:
        if phase == "normal":
            return self._fast_deg_per_s
        if phase == "failure":
            spun = min(1.0, phase_time_s / config.prop_spindown_s)
            return self._fast_deg_per_s * (1.0 - spun)
        return 0.0

    def update(self, dt_s: float, phase: str, phase_time_s: float, config: Config) -> None:
        self.spin_deg = (self.spin_deg + self.rate(phase, phase_time_s, config) * dt_s) % 360.0

    def draw(
        self,
        screen: pygame.Surface,
        hub: tuple[float, float],
        theta_deg: float,
        phase: str,
        phase_time_s: float,
        config: Config,
    ) -> None:
        radius = max(18, int(config.aircraft_display_length_px * 0.09))
        blend = self.rate(phase, phase_time_s, config) / self._fast_deg_per_s
        if blend > 0.04:
            self._draw_disc(screen, hub, radius, int(90 + 80 * blend))
        if blend < 0.92:
            blade_alpha = int(255 * (1.0 - blend))
            self._draw_blades(screen, hub, radius, theta_deg + self.spin_deg, blade_alpha)

    def _draw_disc(self, screen: pygame.Surface, hub: tuple[float, float], radius: int, alpha: int) -> None:
        diameter = radius * 2
        disc = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(disc, (214, 220, 226, alpha), (radius, radius), radius)
        pygame.draw.circle(disc, (255, 255, 255, min(255, alpha)), (radius, radius), max(2, radius // 8))
        for spoke in range(6):
            direction = rotate_offset(0.0, float(radius - 2), self.spin_deg + spoke * 60.0)
            pygame.draw.line(
                disc,
                (255, 255, 255, min(180, alpha)),
                (radius, radius),
                (radius + direction[0], radius + direction[1]),
                2,
            )
        screen.blit(disc, (hub[0] - radius, hub[1] - radius))

    def _draw_blades(
        self,
        screen: pygame.Surface,
        hub: tuple[float, float],
        radius: int,
        angle_deg: float,
        alpha: int,
    ) -> None:
        direction = rotate_offset(0.0, -1.0, angle_deg)
        start = (hub[0] - direction[0] * radius, hub[1] - direction[1] * radius)
        end = (hub[0] + direction[0] * radius, hub[1] + direction[1] * radius)
        layer = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        color = (28, 32, 36, alpha)
        pygame.draw.line(layer, color, start, end, 4)
        pygame.draw.circle(layer, (20, 22, 26, alpha), (int(hub[0]), int(hub[1])), 4)
        screen.blit(layer, (0, 0))
