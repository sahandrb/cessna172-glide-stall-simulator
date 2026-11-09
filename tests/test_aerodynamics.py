"""Homework polar and the stall extension."""

import math

import pytest

from cessna_sim.aerodynamics import (
    CD_INDUCED,
    CD_PARASITE,
    CL_INTERCEPT,
    CL_SLOPE_PER_DEG,
    drag_coefficient,
    lift_coefficient,
    lift_coefficient_linear,
    maximum_lift_coefficient,
    maximum_lift_to_drag,
    stall_speed,
)
from cessna_sim.config import DEFAULT_CONFIG, Config


def test_maximum_lift_to_drag_matches_the_formula() -> None:
    cl_star, ld_max, alpha_star = maximum_lift_to_drag()
    expected_cl = math.sqrt(CD_PARASITE / CD_INDUCED)
    expected_ld = 1.0 / (2.0 * math.sqrt(CD_PARASITE * CD_INDUCED))
    expected_alpha = (expected_cl - CL_INTERCEPT) / CL_SLOPE_PER_DEG
    assert cl_star == pytest.approx(expected_cl)
    assert ld_max == pytest.approx(expected_ld)
    assert alpha_star == pytest.approx(expected_alpha)
    assert ld_max == pytest.approx(12.2, abs=0.05)
    assert alpha_star == pytest.approx(6.05, abs=0.02)


def test_lift_is_continuous_at_stall() -> None:
    stall = DEFAULT_CONFIG.alpha_stall_deg
    at_stall = lift_coefficient(stall, DEFAULT_CONFIG)
    assert at_stall == pytest.approx(lift_coefficient_linear(stall))
    assert at_stall == pytest.approx(maximum_lift_coefficient(DEFAULT_CONFIG))
    just_above = stall + 1.0e-9
    assert lift_coefficient(just_above, DEFAULT_CONFIG) == pytest.approx(at_stall, abs=1e-8)


def test_post_stall_slope_reduces_lift() -> None:
    stall = DEFAULT_CONFIG.alpha_stall_deg
    cl_max = maximum_lift_coefficient(DEFAULT_CONFIG)
    alpha = stall + 4.0
    expected = cl_max - DEFAULT_CONFIG.post_stall_slope_per_deg * 4.0
    assert lift_coefficient(alpha, DEFAULT_CONFIG) == pytest.approx(expected)


def test_assumed_drag_rise_is_off_by_default() -> None:
    cl = lift_coefficient(18.0, DEFAULT_CONFIG)
    baseline = CD_PARASITE + CD_INDUCED * cl * cl
    assert drag_coefficient(cl, 18.0, DEFAULT_CONFIG) == pytest.approx(baseline)
    rising = Config(post_stall_drag="assumed_rise")
    extra = rising.post_stall_drag_slope_per_deg * (18.0 - rising.alpha_stall_deg)
    assert drag_coefficient(cl, 18.0, rising) == pytest.approx(baseline + extra)


def test_stall_speed_matches_the_poh_back_calculation() -> None:
    weight = 1156.7 * 9.80665
    vs = stall_speed(weight, 1.225, 16.165, 1.541)
    assert vs == pytest.approx(27.3, abs=0.1)
    expected = math.sqrt(2.0 * weight / (1.225 * 16.165 * 1.541))
    assert vs == pytest.approx(expected)
