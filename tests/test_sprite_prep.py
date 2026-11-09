"""The supplied PNG is masked, turned nose-right, and keeps its measured CG."""

import pytest

from cessna_sim.app.sprite import disk_is_clear, prepare_aircraft
from cessna_sim.config import DEFAULT_CONFIG


def test_prepared_sprite_points_match_config() -> None:
    prepared = prepare_aircraft(DEFAULT_CONFIG)
    assert prepared.prop_hub_px[0] == pytest.approx(DEFAULT_CONFIG.prop_hub_px[0], abs=1.5)
    assert prepared.prop_hub_px[1] == pytest.approx(DEFAULT_CONFIG.prop_hub_px[1], abs=1.5)
    assert prepared.cg_px[0] == pytest.approx(DEFAULT_CONFIG.cg_px[0], abs=1.5)
    assert prepared.cg_px[1] == pytest.approx(DEFAULT_CONFIG.cg_px[1], abs=1.5)
    assert prepared.prop_hub_px[0] > prepared.cg_px[0]
    assert disk_is_clear(prepared.image, prepared.prop_hub_px, DEFAULT_CONFIG.prop_mask_radius_px)
    assert prepared.level_correction_deg == pytest.approx(0.0)
