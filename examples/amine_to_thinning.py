"""Active-amine loading -> corrosion base x strength once -> local thinning DF."""
from api581 import Context
from api581.api import damage

gas = damage.amine_acid_gas_loading(damage.AmineAcidGasLoadingInput(h2s_amount_mol=20.,
    co2_amount_mol=15., active_amine_amount_mol=100., common_sample_basis="Illustrative same sample active-amine analysis")).outputs
service = dict(method="carbon_table", material="carbon_steel",
    solution=dict(amine_type="mea", amine_mass_fraction=.25),
    contaminants=dict(amine_type="mea", contaminant_mass_fraction=.03, mdea_scale_policy="not_mdea"),
    loading=dict(acid_gas_loading_mol_mol=gas.acid_gas_loading_mol_mol, loading_gap_policy="reject_unassigned_0p10_to_0p15"),
    maximum_temperature_k=116+273.15, velocity_m_s=2., unit_basis="printed_si", lookup_policy="exact_nodes_only",
    classification_qualification_basis="Illustrative rate-table velocity columns and actual local distribution review",
    qualification_basis="Illustrative local amine concentration, metal temperature and chemical applicability")
result = damage.amine_thinning_assessment(damage.AmineThinningAssessmentInput(
    corrosion=dict(amine_service_present=True, applicability_basis="Illustrative qualified chemical treating amine service", rate_model=service),
    assessment_distribution="local", distribution_qualification_basis="Illustrative local inspection coverage",
    starting_thickness_m=.02, elapsed_years=2.,
    strength=dict(method="internal_pressure_eq2_18", differential_pressure_pa=2e6, diameter_m=.5,
        flow_stress_pa=250e6, starting_thickness_m=.02, shape="cylinder"),
    inspections=dict(confidence="high", inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="amine", amine_velocity_regime="high",
        amine_regime_basis="Illustrative same rich rate-table high-velocity band"), methods=[], organized_monitoring_plan=False),
        injection=dict(component_scope="piping", injection_or_mix_point_present=False, highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping", deadleg_present=False, highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative non-AST unclad common baseline"),
    context=Context(asset_id="DEMO-AMINE-001", source_revision="amine-fixture-v1"))
o = result.outputs
assert abs(o.base_corrosion_rate_m_year-.00152)<1e-12
assert o.amine_strength_factor == 1.5
assert abs(o.corrosion_rate_m_year-.00228)<1e-12
assert abs(o.wall_loss_fraction-.228)<1e-12
print("Loading / contamination / velocity:", gas.acid_gas_loading_mol_mol, o.contaminant_row, o.velocity_band)
print("Base / strength / final rate:", o.base_corrosion_rate_m_year, o.amine_strength_factor, o.corrosion_rate_m_year)
print("Loss fraction / thinning DF:", o.wall_loss_fraction, o.thinning_damage_factor)
