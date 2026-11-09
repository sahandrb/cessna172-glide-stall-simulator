"""Inputs collected before a run. V and gamma are not typed."""

from __future__ import annotations

import pygame

from cessna_sim.app.theme import GOLD, MUTED, PANEL, STALL, TEXT, WHITE, font
from cessna_sim.config import Config
from cessna_sim.simulation import initial_state_is_finite


class SetupScreen:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.altitude = f"{config.default_h0_m:.0f}"
        self.alpha = f"{config.default_alpha_deg:.1f}"
        self.t_max = f"{config.default_t_max_s:.0f}"
        self.mode = "glide"
        self.focus = "altitude"
        self.error = ""

    def update(self, events: list[pygame.event.Event]) -> str | None:
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._click(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._type(event)
        return None

    def _fields(self) -> dict[str, pygame.Rect]:
        return {
            "altitude": pygame.Rect(460, 210, 220, 36),
            "alpha": pygame.Rect(460, 270, 220, 36),
            "t_max": pygame.Rect(460, 330, 220, 36),
            "glide": pygame.Rect(300, 400, 280, 40),
            "homework": pygame.Rect(600, 400, 280, 40),
            "run": pygame.Rect(490, 480, 220, 48),
        }

    def _click(self, pos: tuple[int, int]) -> None:
        fields = self._fields()
        for name in ("altitude", "alpha", "t_max"):
            if fields[name].collidepoint(pos):
                self.focus = name
        if fields["glide"].collidepoint(pos):
            self.mode = "glide"
        if fields["homework"].collidepoint(pos):
            self.mode = "homework"
        if fields["run"].collidepoint(pos):
            self.error = self._validate() or "RUN"

    def _type(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_TAB:
            order = ["altitude", "alpha", "t_max"]
            self.focus = order[(order.index(self.focus) + 1) % len(order)]
            return
        if event.key == pygame.K_RETURN:
            self.error = self._validate() or "RUN"
            return
        target = {"altitude": "altitude", "alpha": "alpha", "t_max": "t_max"}[self.focus]
        current = getattr(self, target)
        if event.key == pygame.K_BACKSPACE:
            setattr(self, target, current[:-1])
            return
        char = event.unicode
        if char.isdigit() or (char == "." and "." not in current) or (char == "-" and not current):
            setattr(self, target, current + char)

    def consume_run(self) -> dict | None:
        if self.error != "RUN":
            return None
        self.error = ""
        altitude = float(self.altitude)
        alpha = float(self.alpha)
        t_max = float(self.t_max)
        if self.mode == "homework":
            altitude = self.config.hw_part_d_h0_m
            t_max = self.config.hw_part_d_duration_s
        return {"altitude": altitude, "alpha": alpha, "t_max": t_max, "mode": self.mode}

    def _validate(self) -> str:
        try:
            altitude = float(self.altitude)
            alpha = float(self.alpha)
            t_max = float(self.t_max)
        except ValueError:
            return "Enter numeric values."
        if self.mode == "glide":
            if not self.config.h0_min_m <= altitude <= self.config.h0_max_m:
                return f"Altitude must be {self.config.h0_min_m:.0f} to {self.config.h0_max_m:.0f} m."
            if t_max <= 0.0:
                return "Max time must be positive."
        if not self.config.alpha_min_deg <= alpha <= self.config.alpha_max_deg:
            return (
                f"Alpha must be {self.config.alpha_min_deg:.0f} to "
                f"{self.config.alpha_max_deg:.0f} deg."
            )
        check_altitude = self.config.hw_part_d_h0_m if self.mode == "homework" else altitude
        reason = initial_state_is_finite(alpha, check_altitude, self.config)
        return reason

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((24, 36, 52))
        title = font(36, bold=True).render("Cessna 172 glide test", True, WHITE)
        screen.blit(title, (80, 70))
        subtitle = font(18).render(
            "Engine-out point mass. The only control is angle of attack.",
            True,
            MUTED,
        )
        screen.blit(subtitle, (80, 124))
        labels = (
            ("Initial altitude h0 (m)", "altitude", self.altitude),
            ("Initial angle of attack (deg)", "alpha", self.alpha),
            ("Max simulated time (s)", "t_max", self.t_max),
        )
        label_font = font(18)
        for index, (label, name, value) in enumerate(labels):
            screen.blit(label_font.render(label, True, TEXT), (80, 214 + index * 60))
            rect = self._fields()[name]
            pygame.draw.rect(screen, PANEL, rect)
            border = GOLD if self.focus == name else (90, 104, 120)
            pygame.draw.rect(screen, border, rect, 2)
            screen.blit(font(20).render(value, True, WHITE), (rect.x + 10, rect.y + 6))
        self._mode_button(screen, "glide", "Glide test")
        self._mode_button(screen, "homework", "HW part (d)")
        run = self._fields()["run"]
        pygame.draw.rect(screen, GOLD, run, border_radius=4)
        caption = font(22, bold=True).render("Run", True, (24, 28, 32))
        screen.blit(caption, caption.get_rect(center=run.center))
        if self.mode == "homework":
            note = "HW part (d): h0 = 10 m, t = 0..10 s, constant alpha, equilibrium start."
            screen.blit(font(16).render(note, True, MUTED), (80, 560))
        if self.error and self.error != "RUN":
            screen.blit(font(18).render(self.error, True, STALL), (80, 600))

    def _mode_button(self, screen: pygame.Surface, name: str, label: str) -> None:
        rect = self._fields()[name]
        active = self.mode == name
        pygame.draw.rect(screen, GOLD if active else PANEL, rect, border_radius=4)
        color = (24, 28, 32) if active else TEXT
        text = font(18, bold=True).render(label, True, color)
        screen.blit(text, text.get_rect(center=rect.center))
