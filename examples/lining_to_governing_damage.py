"""Qualified lining history -> lining DF -> governing/all-mechanism composition.

Demonstration inputs only; excluded mechanisms require actual applicability review.
"""
from datetime import date, timedelta
from api581 import Context
from api581.api import damage

installed = date(2000,1,1)
result = damage.lining_assessment(damage.LiningAssessmentInput(
    lining_type="glass_lined",applicability_basis="Illustrative qualified glass protective lining",
    age=dict(lining_family="inorganic",installed_on=installed,evaluated_on=installed+timedelta(days=3650),
        inspections=[dict(inspection_id="inspection-1",inspected_on=installed+timedelta(days=1825),effectiveness="b",
            qualified_for_age_reset=True,qualification_basis="Illustrative qualified thorough B lining inspection")],
        age_basis_policy="step1_installation_or_last_ab",year_length_days=365),
    lookup_policy="exact_rows_only",first_year_policy="reject_below_first_year",condition=dict(condition="average"),
    monitoring=dict(monitoring_used=True,known_effective_for_lining_deterioration=True,
        effectiveness_basis="Illustrative effective early detection allowing orderly shutdown"),
    base_material_thinning_damage_factor=50.,base_material_thinning_basis="Independent section4 fixture; not inferred from lining"),
    context=Context(asset_id="DEMO-LINED-VESSEL-001",component_id="shell",source_revision="lining-fixture-v1"))
o = result.outputs
assert o.effective_age_years == 5
assert abs(o.lining_damage_factor-1.8)<1e-12

# Explicit illustrative exclusion of other damage mechanisms: zero/empty is not automatic screening.
combined = damage.combine(damage.CombineInput(thinning=o.base_material_thinning_damage_factor,lining=o.lining_damage_factor,
    external=[],scc=[],htha=0.,fatigue=0.,brittle_fracture=0.,temper_embrittlement=0.,embrittlement_885f=0.,
    sigma_embrittlement=0.,thinning_external_distribution="local"))
assert combined.outputs.governing_thinning == o.governing_thinning_damage_factor
print("Age baseline / effective years:",o.age_baseline_date,o.effective_age_years)
print("Base / condition / monitoring:",o.base_damage_factor,o.condition_factor,o.monitoring_factor)
print("Lining DF / governing thinning DF:",o.lining_damage_factor,o.governing_thinning_damage_factor)
print("Illustrative explicitly scoped total DF:",combined.outputs.total_damage_factor)
