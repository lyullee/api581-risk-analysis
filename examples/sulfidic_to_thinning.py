"""Hydrogen-free sulfidic/naphthenic table x high velocity once -> thinning."""
from api581 import Context
from api581.api import damage

corrosion=dict(sulfidic_service_present=True, applicability_basis="Illustrative qualified hydrogen-free sulfidic service",
    service_model=dict(table=dict(material="cr5_0p5mo", unit_basis="printed_si", sulfur_mass_fraction=.015,
        tan_mg_koh_g=1.75, maximum_temperature_k=371+273.15, lookup_policy="exact_nodes_only",
        temperature_edge_policy="reject_edge_bins_and_first_gap", low_tan_policy="reject_below_first_tan"),
        velocity=dict(velocity_m_s=31., boundary_interpretation="body_strictly_above_100ft_s",
            qualification_basis="Illustrative maximum stream/nozzle velocity and boundary policy"),
        liquid_phase_present=True, hydrogen_free_sulfidation_and_tan_basis_qualified=True,
        qualification_basis="Illustrative actual liquid-phase TAN, stream sulfur, material and environment"))
result=damage.sulfidic_thinning_assessment(damage.SulfidicThinningAssessmentInput(
    corrosion=corrosion, assessment_distribution="local",
    distribution_qualification_basis="Illustrative actual local distribution and inspection coverage",
    starting_thickness_m=.05, elapsed_years=1.,
    strength=dict(method="internal_pressure_eq2_18", differential_pressure_pa=2e6, diameter_m=.5,
        flow_stress_pa=250e6, starting_thickness_m=.05, shape="cylinder"),
    inspections=dict(confidence="high", inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="high_temperature_sulfidic_naphthenic"), methods=[], organized_monitoring_plan=False),
        injection=dict(component_scope="piping", injection_or_mix_point_present=False, highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping", deadleg_present=False, highly_effective_targeted_inspection=False)),
    qualification_basis="Illustrative common non-AST unclad baseline"),
    context=Context(asset_id="DEMO-SULFIDIC-001", source_revision="sulfidic-fixture-v1"))
o=result.outputs
assert abs(o.base_corrosion_rate_m_year-.00089)<1e-12
assert o.velocity_factor==5. and abs(o.corrosion_rate_m_year-.00445)<1e-12
assert abs(o.wall_loss_fraction-.089)<1e-12
print("Table / source distribution:",o.source_table_id,o.source_thinning_type)
print("Base / velocity factor / final rate:",o.base_corrosion_rate_m_year,o.velocity_factor,o.corrosion_rate_m_year)
print("Wall loss / thinning DF:",o.wall_loss_fraction,o.thinning_damage_factor)
