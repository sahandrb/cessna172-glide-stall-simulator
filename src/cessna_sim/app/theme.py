"""Shared colours and fonts for the engineering view."""

from __future__ import annotations

import pygame

SKY_TOP = (72, 116, 158)
SKY_HORIZON = (198, 220, 232)
PANEL = (18, 24, 34)
PANEL_LINE = (64, 78, 96)
TEXT = (236, 240, 244)
MUTED = (154, 164, 174)
OK = (72, 176, 118)
STALL = (214, 52, 52)
GOLD = (224, 176, 78)
GROUND = (92, 112, 74)
GROUND_LINE = (54, 68, 46)
WHITE = (248, 248, 248)


def font(size: int, bold: bool = False) -> pygame.font.Font:
    name = "segoeui"
    loaded = pygame.font.SysFont(name, size, bold=bold)
    return loaded


def mono(size: int) -> pygame.font.Font:
    return pygame.font.SysFont("consolas", size)
