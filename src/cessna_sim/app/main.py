"""Window loop: setup, the glide, then the results."""

from __future__ import annotations

import os

import pygame

from cessna_sim.app.flight import FlightSession
from cessna_sim.app.results_screen import ResultsScreen
from cessna_sim.app.setup_screen import SetupScreen
from cessna_sim.config import DEFAULT_CONFIG, Config, format_startup_log
from cessna_sim.plots import homework_part_d
from cessna_sim.simulation import run_log_from_trajectory


def run_app(config: Config = DEFAULT_CONFIG) -> int:
    os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
    pygame.init()
    pygame.display.set_caption("Cessna 172 glide and stall test")
    screen = pygame.display.set_mode((config.window_width_px, config.window_height_px))
    clock = pygame.time.Clock()
    print(format_startup_log(config))
    setup = SetupScreen(config)
    flight: FlightSession | None = None
    results: ResultsScreen | None = None
    scene = "setup"
    trails: list[tuple[list[float], list[float]]] = []
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
        keys = pygame.key.get_pressed()
        if scene == "setup":
            setup.update(events)
            setup.draw(screen)
            request = setup.consume_run()
            if request is not None:
                if request["mode"] == "homework":
                    homework_config = _config_with_alpha(config, request["alpha"])
                    trajectory = homework_part_d(homework_config)
                    results = ResultsScreen(
                        run_log_from_trajectory(trajectory, homework_config),
                        trajectory.message or "Homework part (d) finished.",
                        homework_config,
                    )
                    scene = "results"
                else:
                    flight = FlightSession(
                        request["altitude"],
                        request["alpha"],
                        request["t_max"],
                        config,
                        trails,
                    )
                    scene = "flight"
        elif scene == "flight" and flight is not None:
            flight.update(dt, events, keys)
            flight.draw(screen)
            if flight.done and flight.finished_log is not None:
                flight.audio.stop()
                trails.append((list(flight.path_r), list(flight.path_h)))
                message = flight.finished_log.message or "Run finished."
                results = ResultsScreen(flight.finished_log, message, config)
                scene = "results"
        elif scene == "results" and results is not None:
            if results.update(events) == "again":
                scene = "setup"
            else:
                results.draw(screen)
        pygame.display.flip()
    if flight is not None:
        flight.audio.stop()
    if pygame.mixer.get_init() is not None:
        pygame.mixer.quit()
    pygame.quit()
    return 0


def _config_with_alpha(config: Config, alpha_deg: float) -> Config:
    from dataclasses import replace

    return replace(config, default_alpha_deg=alpha_deg)
