"""Direct public evaluate() coverage for remaining chemistry/rate primitives."""

from api581 import evaluate

from test_acid_sour_water import route as acid_route
from test_alkaline_sour_water import estimate as alkaline_estimate
from test_hydrochloric_acid import alloy_model as hcl_alloy_model
from test_hydrofluoric_acid import alloy as hf_alloy
from test_sulfuric_acid import table as sulfuric_table, classification as sulfuric_classification
from test_h2sh2_corrosion import service as h2sh2_service
from test_sulfidic_corrosion import table as sulfidic_table


def test_damage_rate_primitives_public_boundaries():
    assert evaluate("damage/acid-sour-water-other-material-rate", {
        "service_suitability_qualified": True, "other_degradation_assessed": True,
        "rate_policy": "figure_nominal_2mpy", "body_unit_basis": None,
        "qualification_basis": "Qualified public material suitability fixture",
    })["outputs"]
    assert evaluate("damage/alkaline-sour-water-nh4hs-estimate", alkaline_estimate())["outputs"]
    assert evaluate("damage/alkaline-sour-water-base-rate", {
        "nh4hs_mass_fraction": 0.1, "selected_velocity_m_s": 6.1,
        "unit_basis": "printed_si", "lookup_policy": "exact_nodes_only",
    })["outputs"]
    hcl = hcl_alloy_model()
    assert evaluate("damage/hcl-alloy-rate", {
        "material": "alloy_400", "chloride_mass_fraction": hcl["chloride"]["chloride_mass_fraction"],
        "maximum_temperature_k": hcl["maximum_temperature_k"], "oxidants_present": hcl["oxidants_present"],
        "unit_basis": hcl["unit_basis"], "lookup_policy": hcl["lookup_policy"],
    })["outputs"]
    hf = hf_alloy()
    assert evaluate("damage/hf-alloy400-rate", {
        "hf_mass_fraction": hf["hf_mass_fraction"], "concentrated_extension_policy": hf["concentrated_extension_policy"],
        "maximum_temperature_k": hf["maximum_temperature_k"], "aerated_or_oxidants_present": hf["aerated_or_oxidants_present"],
        "unit_basis": hf["unit_basis"], "lookup_policy": hf["lookup_policy"],
    })["outputs"]
    assert evaluate("damage/sulfuric-table-rate", sulfuric_table())["outputs"]
    assert evaluate("damage/sulfuric-thinning-classification", sulfuric_classification())["outputs"]
    h2 = h2sh2_service()
    assert evaluate("damage/h2sh2-table-rate", {k: h2[k] for k in ("material", "unit_basis", "h2s_mole_fraction", "maximum_temperature_k", "stream_case", "lookup_policy")})["outputs"]
    assert evaluate("damage/sulfidic-table-rate", sulfidic_table())["outputs"]

