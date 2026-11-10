"""Engine, stall-warning beep, and airspeed-scaled wind.

Playback follows the flight phases. The volume mapping itself does not import
pygame, so it can be tested without an audio device.
"""

from __future__ import annotations

import pygame

from cessna_sim.config import Config, project_root


def wind_volume(airspeed_m_s: float, reference_m_s: float) -> float:
    """Map true airspeed to a mixer volume in [0, 1].

    Faster flight is louder. The result is 1 at and above reference_m_s.
    """
    if reference_m_s <= 0.0:
        return 0.0
    if airspeed_m_s <= 0.0:
        return 0.0
    return min(1.0, airspeed_m_s / reference_m_s)


class FlightAudio:
    """One-shot engine, one-shot beep, then a looping wind bed."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.available = False
        self._wind_channel: pygame.mixer.Channel | None = None
        self._engine: pygame.mixer.Sound | None = None
        self._beep: pygame.mixer.Sound | None = None
        self._wind: pygame.mixer.Sound | None = None
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            folder = project_root() / "assets" / "audio"
            self._engine = pygame.mixer.Sound(str(folder / "enginsound3sec.wav"))
            self._beep = pygame.mixer.Sound(str(folder / "bibbib1.5sec.wav"))
            self._wind = pygame.mixer.Sound(str(folder / "windsound8sec.wav"))
            self.available = True
        except pygame.error:
            self.available = False

    def play_engine(self) -> None:
        """Normal flight. The clip is three seconds and is not looped."""
        if self._engine is not None:
            self._engine.play(loops=0)

    def play_beep(self) -> None:
        """Engine-failure warning. Stops the engine first."""
        if self._engine is not None:
            self._engine.stop()
        if self._beep is not None:
            self._beep.play(loops=0)

    def play_wind(self, airspeed_m_s: float) -> None:
        """Start the glide wind and keep repeating the eight-second clip."""
        if self._beep is not None:
            self._beep.stop()
        if self._wind is None:
            return
        self._wind_channel = self._wind.play(loops=-1)
        self.set_wind_volume(airspeed_m_s)

    def set_wind_volume(self, airspeed_m_s: float) -> None:
        if self._wind_channel is None:
            return
        self._wind_channel.set_volume(
            wind_volume(airspeed_m_s, self.config.wind_reference_m_s)
        )

    def stop(self) -> None:
        """Silence every cue. Safe when the mixer never started."""
        self._wind_channel = None
        if self._engine is not None:
            self._engine.stop()
        if self._beep is not None:
            self._beep.stop()
        if self._wind is not None:
            self._wind.stop()
