"""HF carbon table -> qualified source class and local thinning; no free-water shortcut."""
from api581 import Context
from api581.api import damage

carbon = dict(method="carbon_steel_table", hf_mass_fraction=.81,
    concentrated_extension_policy="reject_above_81wt_percent",
    maximum_temperature_k=60+273.15, velocity_m_s=1., velocity_basis="printed_si",
    residual_category="high", residual_qualification_basis="Illustrative qualified high residual category",
    unit_basis="printed_si", lookup_policy="exact_nodes_only",
    established_scale_and_stable_operation_qualified=True, material_residual_content_qualified=True,
    qualification_basis="Illustrative established fluoride scale, stable operation and residual metallurgy")
corrosion = dict(hf_exposure_present=True, applicability_basis="Illustrative qualified HF exposure/service",
    rate_model=carbon, galvanic_coupling_present=False, thinning_classification_policy="overview_local",
    classification_qualification_basis="Illustrative overview-local policy and localized inspection review")
result = damage.hf_thinning_assessment(damage.HfThinningAssessmentInput(
    corrosion=corrosion, assessment_distribution="local",
    distribution_qualification_basis="Illustrative qualified actual local distribution and inspection coverage",
    starting_thickness_m=.02, elapsed_years=2.,
    strength=dict(method="internal_pressure_eq2_18", differential_pressure_pa=2e6, diameter_m=.5,
        flow_stress_pa=250e6, starting_thickness_m=.02, shape="cylinder"),
    inspections=dict(confidence="high", inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="hydrofluoric_acid"), methods=[], organized_monitoring_plan=False),
        injection=dict(component_scope="piping", injection_or_mix_point_present=False, highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping", deadleg_present=False, highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative non-AST unclad common baseline"),
    context=Context(asset_id="DEMO-HF-001", source_revision="hf-fixture-v1"))
o = result.outputs
assert abs(o.corrosion_rate_m_year-.00076) < 1e-12
assert abs(o.wall_loss_fraction-.076) < 1e-12
assert o.source_table_id == "2.B.6.2M" and o.residual_column_used == "high"
print("Table / velocity / residual:", o.source_table_id, o.velocity_band, o.residual_column_used)
print("HF rate / wall-loss fraction / DF:", o.corrosion_rate_m_year, o.wall_loss_fraction, o.thinning_damage_factor)

# Above81wt% is a declared engineering extension, not an unlabeled table prediction.
concentrated = corrosion | dict(rate_model=carbon | dict(hf_mass_fraction=.98,
    concentrated_extension_policy="qualified_81wt_percent_node",
    concentrated_extension_qualification_basis="Illustrative explicit concentrated-HF applicability review"))
extended = damage.hf_assessment(damage.HfAssessmentInput(**concentrated)).outputs
assert extended.concentrated_81_node_extension_used
print("Concentrated extension / lookup fraction:", extended.concentrated_81_node_extension_used, extended.hf_mass_fraction_for_lookup)
