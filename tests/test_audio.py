"""Wind loudness follows true airspeed and stays inside the mixer range."""

import pytest

from cessna_sim.app.audio import wind_volume


def test_wind_volume_rises_and_falls_with_airspeed() -> None:
    reference = 45.0
    slow = wind_volume(20.0, reference)
    fast = wind_volume(40.0, reference)
    assert fast > slow
    assert wind_volume(10.0, reference) < slow


def test_wind_volume_stays_inside_zero_and_one() -> None:
    assert wind_volume(0.0, 45.0) == pytest.approx(0.0)
    assert wind_volume(-5.0, 45.0) == pytest.approx(0.0)
    assert wind_volume(45.0, 45.0) == pytest.approx(1.0)
    assert wind_volume(80.0, 45.0) == pytest.approx(1.0)
    assert wind_volume(22.5, 45.0) == pytest.approx(0.5)
