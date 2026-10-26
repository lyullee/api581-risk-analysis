"""Cooling-water source anchors, source-policy gates and rate-to-DF composition."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def temperature(**changes):
    return dict(metal_temperature_k=333.15,system="open",temperature_basis="printed_si",argument_policy="table_operating_temperature",
        duplicate_row_policy="reject_unresolved_row",lookup_policy="exact_rows_only")|changes


def fresh(**changes):
    return dict(material="carbon_steel",applicability_basis="Qualified untreated cooling carbon-steel fixture",actual_ph=8.,saturation_ph=7.,
        saturation_ph_basis="Qualified water saturation-pH fixture",chloride_ppm=100.,velocity_m_s=1.5,system="open_recirculating",
        effective_microbiological_control=True,no_deposits_or_local_low_flow=True,no_corrosion_inhibitor_model_credit=True,
        condition_interpretation="body_rsi6_velocity2_44",rate_unit_basis="printed_si",velocity_equation_basis="printed_si",
        temperature=temperature(),chloride_lookup_policy="exact_rows_only")|changes


def coeff(**changes):
    return dict(total_dissolved_solids_mg_l=400.,water_temperature_k=297.15,temperature_basis="printed_si",
        calcium_hardness_mg_caco3_l=99.,methyl_orange_alkalinity_mg_caco3_l=99.5,
        lookup_policy="exact_rows_only",c4_source_policy="reject_ambiguous_cells")|changes


def test_coefficient_anchor_and_saturation_indices():
    c=damage.cooling_water_ph_coefficients(damage.CoolingWaterPhCoefficientsInput(**coeff())).outputs
    assert (c.c1,c.c2,c.c3,c.c4)==pytest.approx((.1,2.,1.6,2.))
    p=damage.cooling_water_saturation_ph(damage.CoolingWaterSaturationPhInput(c1=c.c1,c2=c.c2,c3=c.c3,c4=c.c4)).outputs.saturation_ph
    assert p==pytest.approx(7.8)
    i=damage.cooling_water_stability_indices(damage.CoolingWaterStabilityIndicesInput(actual_ph=8.,saturation_ph=p)).outputs
    assert i.langelier_saturation_index==pytest.approx(.2) and i.ryznar_stability_index==pytest.approx(7.6)


@pytest.mark.parametrize("tds,c1",[(50,.1),(400,.1),(400.01,.2),(1000,.2)])
def test_tds_boundaries(tds,c1):
    assert damage.cooling_water_ph_coefficients(damage.CoolingWaterPhCoefficientsInput(**coeff(total_dissolved_solids_mg_l=tds))).outputs.c1==c1


@pytest.mark.parametrize("changes",[dict(total_dissolved_solids_mg_l=49.),dict(total_dissolved_solids_mg_l=1001.),
    dict(calcium_hardness_mg_caco3_l=20.),dict(calcium_hardness_mg_caco3_l=21.,lookup_policy="linear_between_rows"),
    dict(methyl_orange_alkalinity_mg_caco3_l=31.),dict(methyl_orange_alkalinity_mg_caco3_l=35.,lookup_policy="linear_between_rows"),
    dict(methyl_orange_alkalinity_mg_caco3_l=10.5)])
def test_missing_and_anomalous_ph_cells_not_invented(changes):
    with pytest.raises(DomainError):
        damage.cooling_water_ph_coefficients(damage.CoolingWaterPhCoefficientsInput(**coeff(**changes)))


def test_printed_literal_c4_requires_qualification_and_preserves_unphysical_raw_ph():
    with pytest.raises(DomainError):
        damage.cooling_water_ph_coefficients(damage.CoolingWaterPhCoefficientsInput(**coeff(c4_source_policy="qualified_printed_literal")))
    c=damage.cooling_water_ph_coefficients(damage.CoolingWaterPhCoefficientsInput(**coeff(methyl_orange_alkalinity_mg_caco3_l=12.5,
        c4_source_policy="qualified_printed_literal",c4_literal_basis="Owner requests literal disputed printed value"))).outputs
    assert c.c4==12.5 and c.c4_printed_literal_used
    p=damage.cooling_water_saturation_ph(damage.CoolingWaterSaturationPhInput(c1=c.c1,c2=c.c2,c3=c.c3,c4=c.c4)).outputs
    assert p.saturation_ph < 0


@pytest.mark.parametrize("chloride,si_high,si_low,us_high,us_low",[(5,.03,.01,1,.3),(10,.05,.02,2,.6),(50,.1,.04,4,1.4),
    (100,.15,.05,6,2),(250,.23,.08,9,3),(500,.33,.11,13,4.3),(750,.38,.13,15,5),(1000,.43,.14,17,5.7),
    (2000,.43,.14,17,5.6),(3000,.41,.14,16,5.4),(5000,.38,.12,15,4.9),(10000,.33,.11,13,4.3)])
def test_all_48_base_rate_cells(chloride,si_high,si_low,us_high,us_low):
    for rsi,si,us in [(7,si_high,us_high),(6,si_low,us_low)]:
        for basis,value,conversion in [("printed_si",si,.001),("printed_us_converted",us,.0000254)]:
            r=damage.cooling_water_base_rate(damage.CoolingWaterBaseRateInput(chloride_ppm=chloride,ryznar_stability_index=rsi,
                velocity_m_s=1.,condition_interpretation="body_rsi6_velocity2_44",rate_unit_basis=basis,lookup_policy="exact_rows_only")).outputs
            assert r.base_corrosion_rate_m_year==pytest.approx(value*conversion)


def test_column_velocity_threshold_basis_and_declining_chloride_interpolation():
    args=dict(chloride_ppm=100.,ryznar_stability_index=6.,velocity_m_s=2.439,rate_unit_basis="printed_si",lookup_policy="exact_rows_only")
    si=damage.cooling_water_base_rate(damage.CoolingWaterBaseRateInput(**args,condition_interpretation="body_rsi6_velocity2_44")).outputs
    us=damage.cooling_water_base_rate(damage.CoolingWaterBaseRateInput(**args,condition_interpretation="us_header_rsi6_velocity8ft")).outputs
    assert si.base_column=="scaling_low" and us.base_column=="unprotected_high"
    for policy,expected in [("linear_between_rows",.000355),("maximum_bracketing_value",.00038)]:
        r=damage.cooling_water_base_rate(damage.CoolingWaterBaseRateInput(**(args|dict(chloride_ppm=7500.,ryznar_stability_index=7.,lookup_policy=policy)),
            condition_interpretation="body_rsi6_velocity2_44")).outputs
        assert r.base_corrosion_rate_m_year==pytest.approx(expected)


@pytest.mark.parametrize("c,closed,opened",[(24,.1,.1),(27,.3,.3),(29,.4,.4),(32,.6,.6),(35,.8,.8),(38,.9,.9),(43,1.2,1.2),
    (46,1.4,1.4),(49,1.6,1.6),(52,1.7,1.7),(54,1.9,1.9),(57,2.1,2.1),(60,2.2,2.2),(63,2.4,2.4),(66,2.5,2.5),
    (68,2.7,2.7),(71,2.9,2.9),(74,3,3),(77,3.2,3.2),(79,3.4,3.3),(82,3.5,3.3),(85,3.7,3.3),(88,3.8,3.3),(91,4,3.1),(93,4.2,2.9),(99,4.5,1.7)])
def test_unambiguous_temperature_rows(c,closed,opened):
    for system,value in [("closed",closed),("open",opened)]:
        r=damage.cooling_water_temperature_factor(damage.CoolingWaterTemperatureFactorInput(**temperature(metal_temperature_k=c+273.15,system=system))).outputs
        assert r.temperature_factor==value


@pytest.mark.parametrize("c",[41.,40.,42.,96.])
def test_duplicate_temperature_row_and_interpolation_are_gated(c):
    with pytest.raises(DomainError):
        damage.cooling_water_temperature_factor(damage.CoolingWaterTemperatureFactorInput(**temperature(metal_temperature_k=c+273.15,lookup_policy="linear_between_rows")))
    r=damage.cooling_water_temperature_factor(damage.CoolingWaterTemperatureFactorInput(**temperature(metal_temperature_k=c+273.15,lookup_policy="linear_between_rows",
        duplicate_row_policy="qualified_ignore_misordered_row",duplicate_row_basis="Owner qualified omission, no invented205F row"))).outputs
    assert r.misordered_row_ignored


def test_temperature_argument_policy_not_hidden_delta_or_absolute():
    absolute=damage.cooling_water_temperature_factor(damage.CoolingWaterTemperatureFactorInput(**temperature(metal_temperature_k=333.15))).outputs
    delta=damage.cooling_water_temperature_factor(damage.CoolingWaterTemperatureFactorInput(**temperature(metal_temperature_k=333.15,
        argument_policy="text_delta_from_reference",lookup_policy="linear_between_rows"))).outputs
    assert absolute.temperature_factor==2.2
    assert delta.temperature_table_argument==36 and delta.temperature_factor==pytest.approx(.8+(.9-.8)/3)


@pytest.mark.parametrize("fahrenheit,factor",[(75,.1),(140,2.2),(210,1.7)])
def test_us_temperature_grid_kelvin_roundtrip(fahrenheit,factor):
    kelvin=(fahrenheit-32)*5/9+273.15
    r=damage.cooling_water_temperature_factor(damage.CoolingWaterTemperatureFactorInput(**temperature(metal_temperature_k=kelvin,
        temperature_basis="printed_us_converted"))).outputs
    assert r.temperature_factor==factor


def test_c2_us_temperature_grid_and_raw_policy_marker():
    c=damage.cooling_water_ph_coefficients(damage.CoolingWaterPhCoefficientsInput(**coeff(water_temperature_k=(76-32)*5/9+273.15,
        temperature_basis="printed_us_converted"))).outputs
    assert c.c2==pytest.approx(2.)
    r=damage.cooling_water_temperature_factor(damage.CoolingWaterTemperatureFactorInput(**temperature(metal_temperature_k=314.15,
        duplicate_row_policy="qualified_ignore_misordered_row",duplicate_row_basis="Qualified use of normally ordered41C row"))).outputs
    assert r.temperature_factor==1.1 and r.misordered_row_ignored


@pytest.mark.parametrize("basis,v,f",[("printed_si",0,1+1.64*.914),("printed_si",.914,1),("printed_si",2.44,1),
    ("printed_si",3.44,1.82),("printed_us_converted",3*.3048,1),("printed_us_converted",8*.3048,1),("printed_us_converted",10*.3048,1.5)])
def test_velocity_equation_anchors(basis,v,f):
    assert damage.cooling_water_velocity_factor(damage.CoolingWaterVelocityFactorInput(velocity_m_s=v,equation_basis=basis)).outputs.velocity_factor==pytest.approx(f)


@pytest.mark.parametrize("basis",["printed_si","printed_us_converted"])
def test_seawater_polynomial_static_and_flow(basis):
    for velocity in [0.,1.,3.,6.1]:
        r=damage.cooling_water_seawater_rate(damage.CoolingWaterSeawaterRateInput(material="carbon_steel",velocity_m_s=velocity,equation_basis=basis,applicability_basis="Qualified21C oxygen6-8ppm seawater fixture")).outputs
        v=velocity if basis=="printed_si" else velocity/.3048
        expected=(.1318+.3108*v-.0579*v**2+.01208*v**2.5)*.001 if basis=="printed_si" else (5.1885+3.7293*v-.21181*v**2+.02439*v**2.5)*.0000254
        assert r.corrosion_rate_m_year==pytest.approx(expected)
    with pytest.raises(DomainError):
        damage.cooling_water_seawater_rate(damage.CoolingWaterSeawaterRateInput(material="carbon_steel",velocity_m_s=6.2,equation_basis=basis,applicability_basis="fixture"))


def test_coupon_rule_explicit_multiplier_not_automatic_model_multiplier():
    for multiplier in [5.,7.,10.]:
        r=damage.cooling_water_coupon_pitting_rate(damage.CoolingWaterCouponPittingRateInput(coupon_general_corrosion_rate_m_year=.00002,
            pitting_multiplier=multiplier,representativeness_basis="Qualified representative weight-loss coupon fixture")).outputs
        assert r.pitting_corrosion_rate_m_year==pytest.approx(.00002*multiplier)
    with pytest.raises(ValidationError):
        damage.CoolingWaterCouponPittingRateInput(coupon_general_corrosion_rate_m_year=.00002,pitting_multiplier=11.,representativeness_basis="fixture")


def test_fresh_model_equation_independent_anchor():
    r=damage.cooling_water_fresh_assessment(damage.CoolingWaterFreshAssessmentInput(**fresh())).outputs
    assert r.ryznar_stability_index==6 and r.langelier_saturation_index==1
    assert r.base_corrosion_rate_m_year==.00005 and r.velocity_factor==1 and r.temperature_factor==2.2
    assert r.corrosion_rate_m_year==pytest.approx(.00011)


@pytest.mark.parametrize("changes",[dict(effective_microbiological_control=False),dict(no_deposits_or_local_low_flow=False),dict(applicability_basis=" "),
    dict(saturation_ph_basis=" "),dict(system="closed_recirculating"),dict(system="once_through_fresh",chloride_ppm=1000.),dict(saturation_ph=1.)])
def test_fresh_source_assumption_gates(changes):
    with pytest.raises(DomainError):
        damage.cooling_water_fresh_assessment(damage.CoolingWaterFreshAssessmentInput(**fresh(**changes)))


def test_cooling_rate_to_qualified_thinning_matches_independent_api():
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder")
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    r=damage.cooling_water_thinning_assessment(damage.CoolingWaterThinningAssessmentInput(cooling=fresh(),starting_thickness_m=.01,elapsed_years=10.,
        strength=strength,inspections=dict(confidence="high",inspections_a=1),conditions=conditions,thinning_type="local",qualification_basis="Qualified localized inspection and non-AST baseline fixture")).outputs
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope="non_ast_unclad",qualification_basis="same fixture",wall=dict(starting_thickness_m=.01,elapsed_years=10.,corrosion_rate_m_year=.00011),
        strength=strength,inspections=dict(confidence="high",inspections_a=1),conditions=conditions)).outputs
    assert r.wall_loss_fraction==pytest.approx(.11) and r.thinning_damage_factor==pytest.approx(direct.thinning_damage_factor)
    assert r.base_velocity_threshold_m_s==2.44 and r.velocity_threshold_m_s is None


def test_numeric_validation_and_equation_overflow():
    for changes in [dict(material="stainless_steel"),dict(actual_ph=6.),dict(velocity_m_s=-1.),dict(velocity_m_s=True),dict(no_corrosion_inhibitor_model_credit=False)]:
        with pytest.raises(ValidationError):
            damage.CoolingWaterFreshAssessmentInput(**fresh(**changes))
    with pytest.raises(DomainError):
        damage.cooling_water_rate_equation(damage.CoolingWaterRateEquationInput(base_corrosion_rate_m_year=1e308,temperature_factor=2.,velocity_factor=2.))


def test_qualitative_rate_factors_do_not_invent_numeric_credit():
    result = damage.cooling_water_rate_factors(damage.CoolingWaterRateFactorsInput(
        process_temperature_k=333.16, impurities_in_makeup_water=True,
        corrosion_products_present=True, biomass_present=True,
        hydrocarbon_process_leak=True, low_flow_or_stagnant_area=True)).outputs
    assert result.scale_potential and result.deposit_risk
    assert result.biological_or_mic_risk and result.underdeposit_risk
    assert 'scale_potential_above_60C' in result.factor_flags
    assert 'hydrocarbon_leak_biomass_acceleration' in result.factor_flags
