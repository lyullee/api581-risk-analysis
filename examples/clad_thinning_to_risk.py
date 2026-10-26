"""Clad vessel DF composed with independent frequency/consequence risk APIs.

Illustrative qualified inputs only; no site or all-mechanism assessment is implied.
"""
from api581 import Context
from api581.api import damage, risk

context = Context(asset_id="DEMO-VESSEL-001",component_id="shell",source_revision="clad-fixture-v1")
result = damage.thinning_clad(damage.ThinningCladInput(
    assessment_scope="non_ast_pressure_vessel_sequential_cladding",
    qualification_basis="Illustrative qualified baseline, sequential internal corrosion and constant rates",
    wall=dict(starting_total_thickness_m=.012,original_base_material_thickness_m=.01,
        cladding_corrosion_rate_m_year=.0002,base_corrosion_rate_m_year=.0005,elapsed_years=15.),
    strength=dict(method="design_thickness_eq2_17",allowable_stress_pa=120e6,weld_efficiency=.85,
        flow_stress_pa=300e6,starting_thickness_m=.012,minimum_required_thickness_m=.004,
        minimum_structural_thickness_m=.006,design_thickness_basis="Illustrative qualified design/load-combination fixture"),
    inspections=dict(confidence="medium",inspections_b=1),injection_point_factor=1.,deadleg_factor=1.,
    online_monitoring_factor=1.),context=context)
assert abs(result.outputs.wall_loss_fraction-.375)<1e-12
assert abs(result.outputs.strength_ratio-.17)<1e-12

# For actual use, damage.combine must include all applicable damage mechanisms.
# This illustrative vessel explicitly assumes no other applicable mechanisms.
assessed = risk.assessment(risk.AssessmentInput(component_type="DRUM",management_score=500.,
    total_damage_factor=result.outputs.thinning_damage_factor,
    damage_factor_source="Same-example clad DF; demonstration assumes no other applicable damage mechanisms",
    consequences=[dict(hole=h,equipment_area_m2=a,personnel_area_m2=2*a,financial_consequence=c)
        for h,a,c in [("small",10.,10000.),("medium",30.,30000.),("large",100.,100000.),("rupture",300.,300000.)]],
    consequence_source="Illustrative externally qualified hole-specific consequences, already event/weather weighted",
    currency="USD"),context=context)
print("Cladding depletion years / loss branch:",result.outputs.cladding_depletion_age_years,result.outputs.wall_loss_branch)
print("Clad/base losses (m):",result.outputs.cladding_wall_loss_m,result.outputs.base_material_wall_loss_m)
print("Strength ratio / thinning DF:",result.outputs.strength_ratio,result.outputs.thinning_damage_factor)
print("Annual failure frequency:",assessed.outputs.risk.annual_failure_frequency)
print("Annual financial risk (illustrative USD):",assessed.outputs.risk.financial_risk_per_year)
