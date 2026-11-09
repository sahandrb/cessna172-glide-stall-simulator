"""Screen-space rotation about the aircraft CG.

pygame's y axis points down. Positive pitch raises the nose when the nose
points to the right. These functions do not import pygame, so the sign can be
tested without a window.
"""

from __future__ import annotations

import math


def rotate_offset(dx: float, dy: float, theta_deg: float) -> tuple[float, float]:
    """Rotate an offset counter-clockwise in y-down screen axes.

    A vector (1, 0) at positive theta moves upward, toward smaller y.
    """
    angle = math.radians(theta_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return (dx * cosine + dy * sine, -dx * sine + dy * cosine)


def pivoted_center(
    cg_screen: tuple[float, float],
    image_size: tuple[float, float],
    cg_px: tuple[float, float],
    theta_deg: float,
) -> tuple[float, float]:
    """Center of a rotated image so that the CG pixel lands on cg_screen.

    Rotation is about the image center. The returned point is the center to
    pass to Surface.get_rect(center=...).
    """
    width, height = image_size
    offset = (cg_px[0] - width / 2.0, cg_px[1] - height / 2.0)
    rotated = rotate_offset(offset[0], offset[1], theta_deg)
    return (cg_screen[0] - rotated[0], cg_screen[1] - rotated[1])


def cg_screen_position(
    image_center: tuple[float, float],
    image_size: tuple[float, float],
    cg_px: tuple[float, float],
    theta_deg: float,
) -> tuple[float, float]:
    """Inverse of pivoted_center, used to prove the CG does not wander."""
    width, height = image_size
    offset = (cg_px[0] - width / 2.0, cg_px[1] - height / 2.0)
    rotated = rotate_offset(offset[0], offset[1], theta_deg)
    return (image_center[0] + rotated[0], image_center[1] + rotated[1])


def hub_screen_position(
    cg_screen: tuple[float, float],
    cg_px: tuple[float, float],
    hub_px: tuple[float, float],
    theta_deg: float,
) -> tuple[float, float]:
    """Propeller hub after the same rotation that is applied to the airframe."""
    relative = (hub_px[0] - cg_px[0], hub_px[1] - cg_px[1])
    rotated = rotate_offset(relative[0], relative[1], theta_deg)
    return (cg_screen[0] + rotated[0], cg_screen[1] + rotated[1])


def smooth_display_angle(displayed_deg: float, target_deg: float, dt_s: float, tau_s: float) -> float:
    """Ease only the drawn pitch. Physics keeps the true angle."""
    if tau_s <= 0.0:
        return target_deg
    blend = 1.0 - math.exp(-dt_s / tau_s)
    return displayed_deg + (target_deg - displayed_deg) * blend
