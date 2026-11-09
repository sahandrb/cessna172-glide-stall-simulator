"""Interactive glide. Physics alpha is exact; only the drawn pitch is smoothed."""

from __future__ import annotations

import math

import pygame
from PIL import Image

from cessna_sim.aerodynamics import is_stalled
from cessna_sim.app.dashboard import draw_dashboard, readout_lines
from cessna_sim.app.propeller import Propeller
from cessna_sim.app.sprite import prepare_aircraft
from cessna_sim.app.theme import GOLD, STALL, TEXT, WHITE, font
from cessna_sim.app.world import (
    Camera,
    CloudField,
    StreakField,
    draw_alpha_cue,
    draw_altitude_scale,
    draw_clouds,
    draw_debug,
    draw_ground,
    draw_sky,
    draw_streaks,
    draw_trail,
)
from cessna_sim.config import Config
from cessna_sim.dynamics import pitch_angle_rad
from cessna_sim.equilibrium import equilibrium_glide
from cessna_sim.simulation import GlideRun, RunLog
from cessna_sim.sprite_geometry import hub_screen_position, pivoted_center, rotate_offset, smooth_display_angle


class FlightSession:
    def __init__(
        self,
        altitude_m: float,
        alpha_deg: float,
        t_max_s: float,
        config: Config,
        previous_trails: list[tuple[list[float], list[float]]] | None = None,
    ) -> None:
        self.config = config
        self.h0 = altitude_m
        self.alpha = alpha_deg
        self.t_max_s = t_max_s
        self.previous = previous_trails or []
        self.phase = "normal"
        self.phase_time = 0.0
        self.accumulator = 0.0
        self.run: GlideRun | None = None
        self.path_r = [0.0]
        self.path_h = [altitude_m]
        self.finished_log: RunLog | None = None
        self.propeller = Propeller()
        self.camera = Camera(config.window_width_px, config.window_height_px)
        self.clouds = CloudField()
        self.streaks = StreakField()
        self.debug = False
        self.slider_drag = False
        self.frame_dt = 1.0 / 60.0
        self.display_theta: float | None = None
        prepared = prepare_aircraft(config)
        self.cg_px = prepared.cg_px
        self.hub_px = prepared.prop_hub_px
        self.scaled, self.cg_scaled, self.hub_scaled = _scale_sprite(prepared.image, config, self.cg_px, self.hub_px)
        self._hold = equilibrium_glide(self.alpha, self.h0, config)

    @property
    def done(self) -> bool:
        return self.phase == "done"

    def state(self) -> tuple[float, float, float, float, float]:
        """time, alpha, V, gamma, and the altitude/distance pair is separate."""
        if self.run is None:
            airspeed, gamma = self._hold
            return 0.0, self.alpha, airspeed, gamma
        return self.run.time_s, self.run.alpha_deg, self.run.airspeed, self.run.gamma_rad

    def altitude(self) -> float:
        return self.h0 if self.run is None else self.run.altitude

    def distance(self) -> float:
        return 0.0 if self.run is None else self.run.distance

    def update(self, dt_s: float, events: list[pygame.event.Event], keys) -> None:
        dt_s = min(dt_s, 0.05)
        self.frame_dt = dt_s
        self._read_input(events, keys, dt_s)
        self.propeller.update(dt_s, self.phase, self.phase_time, self.config)
        if self.phase == "normal":
            self.phase_time += dt_s
            if self.phase_time >= self.config.phase_normal_s:
                self.phase = "failure"
                self.phase_time = 0.0
        elif self.phase == "failure":
            self.phase_time += dt_s
            if self.phase_time >= self.config.phase_failure_banner_s:
                self._begin_glide()
        elif self.phase == "glide":
            self._integrate(dt_s)
        self.camera.update(self.altitude(), dt_s)
        time_s, alpha, airspeed, gamma = self.state()
        del time_s, alpha
        view_width_m = self.config.window_width_px / self.camera.pixels_per_meter
        self.streaks.update(self.distance(), self.altitude(), airspeed, gamma, dt_s, view_width_m)

    def _begin_glide(self) -> None:
        self.phase = "glide"
        self.phase_time = 0.0
        self.run = GlideRun(self.h0, self.alpha, self.config)
        self.path_r = [0.0]
        self.path_h = [self.h0]

    def _integrate(self, frame_dt: float) -> None:
        assert self.run is not None
        self.accumulator += frame_dt
        while self.accumulator >= self.config.physics_dt_s and not self.run.finished:
            self.run.step(self.config.physics_dt_s)
            self._apply_alpha_keys(self.config.physics_dt_s)
            self.run.set_alpha(self.alpha)
            self.path_r.append(self.run.distance)
            self.path_h.append(self.run.altitude)
            self.accumulator -= self.config.physics_dt_s
            if self.run.time_s >= self.t_max_s:
                self.run.finish("Stopped because the time limit was reached.")
        if self.run.finished:
            self.finished_log = self.run.log()
            self.phase = "done"

    def _read_input(self, events: list[pygame.event.Event], keys, dt_s: float) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                self.debug = not self.debug
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._slider_rect().collidepoint(event.pos):
                    self.slider_drag = True
                    self._set_alpha_from_slider(event.pos[0])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.slider_drag = False
            elif event.type == pygame.MOUSEMOTION and self.slider_drag:
                self._set_alpha_from_slider(event.pos[0])
        if self.phase != "glide" and not self.slider_drag:
            self._apply_alpha_keys(dt_s)
        self.alpha = min(self.config.alpha_max_deg, max(self.config.alpha_min_deg, self.alpha))
        if self.phase in {"normal", "failure"}:
            try:
                self._hold = equilibrium_glide(self.alpha, self.h0, self.config)
            except ValueError:
                self.alpha = self.config.default_alpha_deg
                self._hold = equilibrium_glide(self.alpha, self.h0, self.config)

    def _apply_alpha_keys(self, dt_s: float) -> None:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.alpha += self.config.alpha_rate_deg_per_s * dt_s
        if keys[pygame.K_DOWN]:
            self.alpha -= self.config.alpha_rate_deg_per_s * dt_s

    def _slider_rect(self) -> pygame.Rect:
        return pygame.Rect(280, self.config.window_height_px - 42, self.config.window_width_px - 560, 18)

    def _set_alpha_from_slider(self, mouse_x: float) -> None:
        rect = self._slider_rect()
        fraction = (mouse_x - rect.x) / rect.w
        fraction = min(1.0, max(0.0, fraction))
        span = self.config.alpha_max_deg - self.config.alpha_min_deg
        self.alpha = self.config.alpha_min_deg + fraction * span

    def draw(self, screen: pygame.Surface) -> None:
        time_s, alpha, airspeed, gamma = self.state()
        true_theta = math.degrees(pitch_angle_rad(alpha, gamma))
        if self.display_theta is None:
            self.display_theta = true_theta
        draw_sky(screen)
        draw_clouds(screen, self.camera, self.clouds, self.distance())
        draw_ground(screen, self.camera, self.distance())
        for old_r, old_h in self.previous:
            draw_trail(screen, self.camera, self.distance(), old_r, old_h, (170, 178, 186), 1)
        draw_trail(screen, self.camera, self.distance(), self.path_r, self.path_h, (236, 196, 96), 2)
        draw_streaks(screen, self.camera, self.streaks, self.distance(), gamma)
        cg = (self.camera.aircraft_x, self._aircraft_screen_y())
        center = pivoted_center(cg, self.scaled.get_size(), self.cg_scaled, self.display_theta)
        rotated = pygame.transform.rotozoom(self.scaled, self.display_theta, 1.0)
        screen.blit(rotated, rotated.get_rect(center=center))
        hub = hub_screen_position(cg, self.cg_scaled, self.hub_scaled, self.display_theta)
        self.propeller.draw(screen, hub, self.display_theta, self.phase, self.phase_time, self.config)
        nose = (hub[0] + rotate_offset(18.0, 0.0, self.display_theta)[0], hub[1] + rotate_offset(18.0, 0.0, self.display_theta)[1])
        draw_alpha_cue(screen, nose, math.degrees(gamma), self.display_theta, alpha)
        draw_altitude_scale(screen, self.camera)
        if self.debug:
            draw_debug(screen, cg, math.degrees(gamma), true_theta, alpha, self.display_theta)
        self._draw_status(screen, alpha)
        stalled = is_stalled(alpha, self.config)
        lines = readout_lines(time_s, alpha, airspeed, gamma, self.altitude(), self.distance(), self.config)
        flash = int(pygame.time.get_ticks() / 180) % 2 == 0
        draw_dashboard(screen, lines, stalled, flash)
        self._draw_slider(screen)
        # Smoothing uses the frame that was just drawn so the next frame eases.
        # The value stored here is applied on the following draw via display_theta.
        self.display_theta = smooth_display_angle(
            self.display_theta,
            true_theta,
            self.frame_dt,
            self.config.display_pitch_smoothing_s,
        )

    def _aircraft_screen_y(self) -> float:
        _, screen_y = self.camera.to_screen(self.distance(), self.altitude(), self.distance())
        return screen_y

    def _draw_status(self, screen: pygame.Surface, alpha: float) -> None:
        if self.phase == "normal":
            label, color = "NORMAL FLIGHT", (210, 230, 220)
        elif self.phase == "failure":
            label, color = "ENGINE FAILURE", STALL
        elif is_stalled(alpha, self.config) and int(pygame.time.get_ticks() / 180) % 2 == 0:
            label, color = "STALL", STALL
        else:
            return
        text = font(28, bold=True).render(label, True, color)
        screen.blit(text, text.get_rect(center=(screen.get_width() / 2, 48)))

    def _draw_slider(self, screen: pygame.Surface) -> None:
        rect = self._slider_rect()
        pygame.draw.rect(screen, (30, 40, 52), rect, border_radius=4)
        span = self.config.alpha_max_deg - self.config.alpha_min_deg
        fraction = (self.alpha - self.config.alpha_min_deg) / span
        handle_x = rect.x + fraction * rect.w
        pygame.draw.circle(screen, GOLD, (int(handle_x), rect.centery), 9)
        caption = font(15).render(f"alpha {self.alpha:.1f} deg", True, TEXT)
        screen.blit(caption, (rect.right + 12, rect.y - 2))


def _scale_sprite(
    image: Image.Image,
    config: Config,
    cg_px: tuple[float, float],
    hub_px: tuple[float, float],
) -> tuple[pygame.Surface, tuple[float, float], tuple[float, float]]:
    scale = config.aircraft_display_length_px / image.size[0]
    size = (max(1, round(image.size[0] * scale)), max(1, round(image.size[1] * scale)))
    surface = pygame.image.frombytes(image.tobytes(), image.size, "RGBA").convert_alpha()
    scaled = pygame.transform.smoothscale(surface, size)
    applied = size[0] / image.size[0]
    return (
        scaled,
        (cg_px[0] * applied, cg_px[1] * applied),
        (hub_px[0] * applied, hub_px[1] * applied),
    )
