import importlib.util
import runpy

import pytest

from api581 import DomainError, evaluate


pytestmark = pytest.mark.skipif(importlib.util.find_spec("slabx") is None,
                                reason="optional SLABx native engine is unavailable")


def test_native_dispersion_public_boundaries():
    pool_request = runpy.run_path("examples/native_dispersion_pool.py")["request"]
    pool = pool_request("slabx").model_dump()
    pool_footprint = {**pool, "crosswind_half_span_m": 100.0, "crosswind_points_per_side": 33}
    pool_fire = {**pool_footprint, "criterion_role": "qualified_lfl", "receptor_height_m": 0.0}
    assert evaluate("dispersion/native-pool-footprint", pool_footprint)["outputs"]
    with pytest.raises(DomainError, match="footprint unusable"):
        evaluate("dispersion/native-pool-flash-fire", pool_fire)

    jet_request = runpy.run_path("examples/native_jet_dispersion.py")["request"]
    jet = jet_request("slabx").model_dump()
    jet["crosswind_half_span_m"] = 100.0
    jet["crosswind_points_per_side"] = 33
    assert evaluate("dispersion/native-jet-footprint", jet)["outputs"]

    partition = {"adjusted_mass_rate_kg_s": 2.0, "released_mass_kg": 120.0,
                 "rainout_mass_fraction": 0.25, "equation_basis": "post_flash_mass_balance",
                 "post_flash_vapor_mass_fraction": 0.5,
                 "rainout_basis_source": "qualified rainout fixture",
                 "flash_property_source": "qualified flash fixture"}
    geometry = {k: v for k, v in jet_request("slabx", source_temperature_k=231.0).model_dump().items()
                if k not in {"mass_source_rate_kg_s", "release_duration_s", "jet_liquid_mass_fraction"}}
    geometry_fp = {**geometry, "crosswind_half_span_m": 30.0, "crosswind_points_per_side": 33}
    assert evaluate("dispersion/partitioned-jet-centreline", {"partition": partition, "jet": geometry})["outputs"]
    assert evaluate("dispersion/partitioned-jet-footprint", {"partition": partition, "jet": geometry_fp})["outputs"]

    toxic = runpy.run_path("examples/native_toxic_pool.py")["request"]().model_dump()
    assert evaluate("dispersion/native-pool-toxic-consequence", toxic)["outputs"]

    flashed_request = runpy.run_path("examples/flashed_boiling_pool.py")["request"]
    flashed = flashed_request().model_dump()
    flashed_fp = {**flashed, "crosswind_half_span_m": 100.0, "crosswind_points_per_side": 33}
    flashed_fire = {**flashed_fp, "criterion_role": "qualified_lfl", "receptor_height_m": 0.0}
    assert evaluate("dispersion/flashed-boiling-pool-centreline", flashed)["outputs"]
    assert evaluate("dispersion/flashed-boiling-pool-footprint", flashed_fp)["outputs"]
    assert evaluate("dispersion/flashed-boiling-pool-flash-fire", flashed_fire)["outputs"]
