"""Numbers after the glide, plus plot and export actions."""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pygame

from cessna_sim.app.theme import GOLD, MUTED, PANEL, TEXT, WHITE, font
from cessna_sim.config import Config, project_root
from cessna_sim.plots import export_run_plots, show_run_plots
from cessna_sim.records import write_run_csv
from cessna_sim.simulation import RunLog


class ResultsScreen:
    def __init__(self, log: RunLog, message: str, config: Config) -> None:
        self.log = log
        self.message = message
        self.config = config
        self.note = ""
        self.action = ""

    def update(self, events: list[pygame.event.Event]) -> str | None:
        self.action = ""
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._buttons()["plots"].collidepoint(event.pos):
                    self.action = "plots"
                elif self._buttons()["export"].collidepoint(event.pos):
                    self.action = "export"
                elif self._buttons()["again"].collidepoint(event.pos):
                    self.action = "again"
        if self.action == "plots":
            show_run_plots(self.log, self.config)
            return None
        if self.action == "export":
            self.note = f"Exported to {export_run(self.log, self.config)}"
            return None
        if self.action == "again":
            return "again"
        return None

    def _buttons(self) -> dict[str, pygame.Rect]:
        return {
            "plots": pygame.Rect(80, 520, 200, 46),
            "export": pygame.Rect(300, 520, 200, 46),
            "again": pygame.Rect(520, 520, 200, 46),
        }

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill((24, 36, 52))
        screen.blit(font(34, bold=True).render("Run complete", True, WHITE), (80, 60))
        if self.message:
            screen.blit(font(18).render(self.message, True, MUTED), (80, 112))
        stalls = [event for event in self.log.events if event.name == "stall_onset"]
        times = ", ".join(f"{event.time_s:.2f} s" for event in stalls) or "none"
        rows = [
            f"Final distance    {self.log.distance[-1]:.1f} m",
            f"Flight time       {self.log.t[-1]:.2f} s",
            f"Average L/D       {float(np.mean(self.log.lift_to_drag)):.2f}",
            f"Minimum speed     {float(np.min(self.log.airspeed)):.2f} m/s",
            f"Stall events      {len(stalls)}",
            f"Stall times       {times}",
        ]
        for index, row in enumerate(rows):
            screen.blit(font(22).render(row, True, TEXT), (80, 170 + index * 42))
        for name, label in (("plots", "Show plots"), ("export", "Export"), ("again", "Run again")):
            rect = self._buttons()[name]
            pygame.draw.rect(screen, GOLD if name == "again" else PANEL, rect, border_radius=4)
            pygame.draw.rect(screen, GOLD, rect, 2, border_radius=4)
            text = font(18, bold=True).render(label, True, WHITE if name != "again" else (24, 28, 32))
            screen.blit(text, text.get_rect(center=rect.center))
        if self.note:
            screen.blit(font(16).render(self.note, True, MUTED), (80, 590))


def export_run(log: RunLog, config: Config) -> str:
    folder = project_root() / "outputs" / datetime.now().strftime("run_%Y%m%d_%H%M%S")
    write_run_csv(log, folder)
    export_run_plots(log, folder, config)
    return str(folder)
