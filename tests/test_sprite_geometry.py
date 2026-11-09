"""Pitch sign and the CG pivot. No window is opened."""

import pytest

from cessna_sim.sprite_geometry import (
    cg_screen_position,
    pivoted_center,
    rotate_offset,
    smooth_display_angle,
)


def test_positive_theta_raises_the_nose() -> None:
    _, screen_y = rotate_offset(100.0, 0.0, 15.0)
    assert screen_y < 0.0


def test_negative_theta_lowers_the_nose() -> None:
    _, screen_y = rotate_offset(100.0, 0.0, -15.0)
    assert screen_y > 0.0


def test_cg_stays_on_the_aircraft_position() -> None:
    cg_screen = (420.0, 280.0)
    image_size = (360.0, 130.0)
    cg_px = (250.0, 60.0)
    for theta in (-25.0, 0.0, 8.0, 18.0, 40.0):
        center = pivoted_center(cg_screen, image_size, cg_px, theta)
        landed = cg_screen_position(center, image_size, cg_px, theta)
        assert landed[0] == pytest.approx(cg_screen[0], abs=1e-6)
        assert landed[1] == pytest.approx(cg_screen[1], abs=1e-6)


def test_display_smoothing_does_not_jump() -> None:
    eased = smooth_display_angle(0.0, 10.0, dt_s=0.15, tau_s=0.15)
    assert 0.0 < eased < 10.0
    assert smooth_display_angle(4.0, 4.0, 0.1, 0.0) == pytest.approx(4.0)
