"""Cooling-water coefficients -> saturation/RSI -> rate -> non-AST thinning DF.

Demonstration only: actual water chemistry, MIC and inspection scope need qualification.
"""
from api581 import Context
from api581.api import damage

c = damage.cooling_water_ph_coefficients(damage.CoolingWaterPhCoefficientsInput(
    total_dissolved_solids_mg_l=400.,water_temperature_k=297.15,temperature_basis="printed_si",
    calcium_hardness_mg_caco3_l=99.,methyl_orange_alkalinity_mg_caco3_l=99.5,
    lookup_policy="exact_rows_only",c4_source_policy="reject_ambiguous_cells")).outputs
phs = damage.cooling_water_saturation_ph(damage.CoolingWaterSaturationPhInput(c1=c.c1,c2=c.c2,c3=c.c3,c4=c.c4)).outputs.saturation_ph
cooling = dict(material="carbon_steel",applicability_basis="Illustrative untreated open cooling-water fixture",
    actual_ph=8.,saturation_ph=phs,saturation_ph_basis="Same-example coefficient table and eq2.B.11",
    chloride_ppm=100.,velocity_m_s=1.5,system="open_recirculating",effective_microbiological_control=True,
    no_deposits_or_local_low_flow=True,no_corrosion_inhibitor_model_credit=True,
    condition_interpretation="body_rsi6_velocity2_44",rate_unit_basis="printed_si",velocity_equation_basis="printed_si",
    temperature=dict(metal_temperature_k=333.15,system="open",temperature_basis="printed_si",
        argument_policy="table_operating_temperature",duplicate_row_policy="reject_unresolved_row",lookup_policy="exact_rows_only"),
    chloride_lookup_policy="exact_rows_only")
result = damage.cooling_water_thinning_assessment(damage.CoolingWaterThinningAssessmentInput(
    cooling=cooling,starting_thickness_m=.01,elapsed_years=5.,
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,
        flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder"),
    inspections=dict(confidence="high",inspections_a=1),
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False)),
    thinning_type="local",qualification_basis="Illustrative qualified localized inspection and common baseline, non-AST scope"),
    context=Context(asset_id="DEMO-COOLING-PIPE-001",source_revision="cooling-water-fixture-v1"))
o = result.outputs
assert abs(o.corrosion_rate_m_year-.00033)<1e-12
assert abs(o.wall_loss_fraction-.165)<1e-12
print("Saturation pH / RSI:",phs,o.ryznar_stability_index)
print("Base rate / FT / FV:",o.base_corrosion_rate_m_year,o.temperature_factor,o.velocity_factor)
print("Representative corrosion (m/year) / thinning DF:",o.corrosion_rate_m_year,o.thinning_damage_factor)

sea = damage.cooling_water_seawater_rate(damage.CoolingWaterSeawaterRateInput(material="carbon_steel",
    velocity_m_s=1.,equation_basis="printed_si",applicability_basis="Illustrative seawater21C,oxygen6-8ppm,qualified deposit/MIC exclusions"))
print("Separate seawater correlation (m/year):",sea.outputs.corrosion_rate_m_year)
