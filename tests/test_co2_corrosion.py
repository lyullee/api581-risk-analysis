"""CO2 source equation/table anchors and qualified wet/dry composition."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage

PSI=6894.757293168


def wet(**changes):
    return dict(ph=dict(method="supplied",ph=5.,qualification_basis="Qualified water pH fixture"),
        flow=dict(method="supplied",shear_stress_pa=19.,qualification_basis="Qualified wall shear fixture"),
        lookup_policy="exact_nodes_only",jump_policy="reject_cross_80_90",temperature_denominator_basis="printed_celsius_plus_273",
        simple_upstream_mixture_and_wetting_basis="Qualified upstream water/crude/natural-gas wetted steel fixture",
        glycol=dict(composition_percent=50.,composition_basis="equation_g_percent"),inhibitor_factor=.2,
        inhibitor_effectiveness_basis="Independently determined inhibitor reduction fixture")|changes


def request(**changes):
    return damage.Co2CorrosionAssessmentInput(**(dict(material="carbon_steel",temperature_k=333.15,co2_partial_pressure_pa_abs=1e5,
        free_liquid_water_present=True,applicability_basis="Qualified wetted upstream carbon-steel CO2 fixture",wet_model=wet())|changes))


@pytest.mark.parametrize("c,row",[(20,[6,5.45,4.9,3.72,2.55,1.55,.72]),(30,[8.52,7.77,7.02,5.16,3.4,2,.91]),
    (40,[10.98,10.06,9.13,6.49,4.08,2.3,1.02]),(50,[11.92,10.96,10.01,6.86,4.1,2.2,.94]),
    (60,[12.83,11.86,10.89,7.18,4.05,2.03,.84]),(70,[13.42,12.01,10.6,6.58,3.61,1.86,.87]),
    (80,[13.93,12.12,10.31,6.01,3.2,1.7,.9]),(90,[9.37,7.91,6.45,2.44,.82,.49,.32]),
    (100,[9.23,8.04,6.38,2.19,.94,.62,.42]),(110,[8.96,8.09,6.22,1.87,1.07,.77,.53]),
    (120,[8.55,8.06,5.98,1.48,1.2,.92,.65]),(130,[7.38,6.39,3.98,.96,.8,.63,.47]),
    (140,[6.26,4.91,2.31,.53,.46,.39,.32]),(150,[5.2,3.62,.98,.19,.19,.19,.19])])
def test_all_98_temperature_ph_cells(c,row):
    for ph,value in zip([3.5,4,4.5,5,5.5,6,6.5],row):
        r=damage.co2_temperature_ph_factor(damage.Co2TemperaturePhFactorInput(temperature_k=c+273.15,ph=ph,lookup_policy="exact_nodes_only",jump_policy="reject_cross_80_90")).outputs
        assert r.temperature_ph_factor==value and not r.sharp_temperature_interval_interpolated


def test_bilinear_numerical_policy_and_sharp_interval_gate():
    r=damage.co2_temperature_ph_factor(damage.Co2TemperaturePhFactorInput(temperature_k=298.15,ph=5.25,lookup_policy="bilinear",jump_policy="reject_cross_80_90")).outputs
    assert r.temperature_ph_factor==pytest.approx((3.72+2.55+5.16+3.4)/4)
    with pytest.raises(DomainError):
        damage.co2_temperature_ph_factor(damage.Co2TemperaturePhFactorInput(temperature_k=358.15,ph=5.,lookup_policy="bilinear",jump_policy="reject_cross_80_90"))
    r=damage.co2_temperature_ph_factor(damage.Co2TemperaturePhFactorInput(temperature_k=358.15,ph=5.,lookup_policy="bilinear",
        jump_policy="qualified_linear_across_jump",jump_qualification_basis="Owner qualified linear interval assumption")).outputs
    assert r.temperature_ph_factor==pytest.approx((6.01+2.44)/2) and r.sharp_temperature_interval_interpolated


@pytest.mark.parametrize("c",[19.99,150.01])
def test_table_no_temperature_extrapolation(c):
    with pytest.raises(DomainError):
        damage.co2_temperature_ph_factor(damage.Co2TemperaturePhFactorInput(temperature_k=c+273.15,ph=5.,lookup_policy="bilinear",jump_policy="reject_cross_80_90"))


def test_source_rh_above_one_not_clamped_and_zero_water():
    for mass_fraction in [0.,.01,.1]:
        r=damage.co2_relative_humidity(damage.Co2RelativeHumidityInput(water_mass_fraction=mass_fraction,total_pressure_pa_abs=1e6,water_saturation_pressure_pa_abs=1e4)).outputs
        ratio=mass_fraction/(1-mass_fraction)
        assert r.relative_humidity_fraction==pytest.approx(ratio/(.622+ratio)*100)
    assert r.relative_humidity_fraction > 1 and r.supersaturated


def test_dew_point_fahrenheit_pressure_conversion_and_zero_rejection():
    r=damage.co2_dew_point(damage.Co2DewPointInput(water_mass_fraction=.1,total_pressure_pa_abs=100*PSI)).outputs
    expected_f=10**(2.0866+.2088*math.log10(.1)+.2242*math.log10(100))
    assert r.dew_point_temperature_k==pytest.approx((expected_f-32)*5/9+273.15)
    for value in [0.,.301]:
        with pytest.raises(ValidationError):
            damage.Co2DewPointInput(water_mass_fraction=value,total_pressure_pa_abs=100*PSI)


@pytest.mark.parametrize("case,a,b,c",[("condensate",2.8686,.7931,.57),("ferrous_saturated",2.5907,.8668,.49),("salinity_46_g_l",2.7137,.8002,.57)])
def test_three_ph_approximation_unit_anchors(case,a,b,c):
    r=damage.co2_ph_estimate(damage.Co2PhEstimateInput(temperature_k=(100-32)*5/9+273.15,co2_partial_pressure_pa_abs=10*PSI,
        water_case=case,approximation_basis="Qualified water chemistry approximation fixture")).outputs
    assert r.estimated_ph==pytest.approx(a+b*2-c)


def test_fugacity_uses_partial_bar_and_explicit_273_denominator():
    values=[]
    for basis,denominator in [("printed_celsius_plus_273",333.),("kelvin_exact",333.15)]:
        r=damage.co2_fugacity(damage.Co2FugacityInput(temperature_k=333.15,co2_partial_pressure_pa_abs=1e6,temperature_denominator_basis=basis)).outputs
        alpha=10**(10*(.0031-1.4/denominator))
        assert r.fugacity_coefficient==pytest.approx(alpha) and r.fugacity_pa==pytest.approx(1e6*alpha)
        values.append(r.fugacity_pa)
    assert values[0]!=values[1]
    r=damage.co2_fugacity(damage.Co2FugacityInput(temperature_k=333.15,co2_partial_pressure_pa_abs=300e5,temperature_denominator_basis="printed_celsius_plus_273")).outputs
    assert r.fugacity_coefficient==pytest.approx(10**(250*(.0031-1.4/333)))


def test_turbulent_flow_primitives_no_darcy_conversion_or_cuberoot_substitution():
    re=damage.co2_reynolds(damage.Co2ReynoldsInput(diameter_m=.1,mixture_density_kg_m3=800.,mixture_velocity_m_s=2.,mixture_viscosity_pa_s=.001)).outputs.reynolds_number
    assert re==pytest.approx(160000)
    f=damage.co2_friction_factor(damage.Co2FrictionFactorInput(reynolds_number=re,relative_roughness=.0001)).outputs.friction_factor
    assert f==pytest.approx(.001375*(1+(2+1e6/re)**.33))
    s=damage.co2_shear_stress(damage.Co2ShearStressInput(friction_factor=f,mixture_density_kg_m3=800.,mixture_velocity_m_s=2.)).outputs.shear_stress_pa
    assert s==pytest.approx(f*800*4/2)
    with pytest.raises(DomainError):
        damage.co2_friction_factor(damage.Co2FrictionFactorInput(reynolds_number=2300.,relative_roughness=.0001))


@pytest.mark.parametrize("stress",[0.,19.,150.,1000.])
def test_base_rate_literal_exponent_and_shear_cap(stress):
    r=damage.co2_base_rate(damage.Co2BaseRateInput(temperature_ph_factor=7.18,fugacity_pa=2e5,shear_stress_pa=stress)).outputs
    expected=7.18*2**.62*(min(stress,150)/19)**(.146+.0324*2)/1000
    assert r.base_corrosion_rate_m_year==pytest.approx(expected)
    assert r.applied_shear_stress_pa==min(stress,150) and r.shear_cap_applied==(stress>150)


@pytest.mark.parametrize("g,floor",[(0,False),(50,False),(99,True),(100,True)])
def test_glycol_composition_bases_floor_and_endpoint(g,floor):
    for value,basis in [(g,"equation_g_percent"),(100-g,"table_water_weight_percent")]:
        r=damage.co2_glycol_factor(damage.Co2GlycolFactorInput(composition_percent=value,composition_basis=basis)).outputs
        assert r.glycol_factor==pytest.approx(max(.008,((100-g)/100)**1.6)) and r.glycol_floor_applied==floor


def test_reduction_minimum_not_product_and_inhibitor_independent_of_glycol_floor():
    r=damage.co2_rate_adjustment(damage.Co2RateAdjustmentInput(base_corrosion_rate_m_year=.01,
        glycol=dict(composition_percent=50.,composition_basis="equation_g_percent"),inhibitor_factor=.2,inhibitor_effectiveness_basis="Independent inhibitor efficacy fixture")).outputs
    assert r.applied_reduction_factor==.2 and r.corrosion_rate_m_year==.002
    r=damage.co2_rate_adjustment(damage.Co2RateAdjustmentInput(base_corrosion_rate_m_year=.01,inhibitor_factor=0.,inhibitor_effectiveness_basis="Explicit independently qualified zero factor fixture")).outputs
    assert r.corrosion_rate_m_year==0
    with pytest.raises(DomainError):
        damage.co2_rate_adjustment(damage.Co2RateAdjustmentInput(base_corrosion_rate_m_year=.01,inhibitor_factor=.2))


def test_wet_assessment_matches_independent_equation_chain():
    r=damage.co2_corrosion_assessment(request()).outputs
    f=10**(.0031-1.4/333)
    expected=7.18*f**.62*.2/1000
    assert r.corrosion_rate_m_year==pytest.approx(expected)
    assert r.model_ph==5 and r.applied_reduction_factor==.2 and r.calculation_branch=="wet_carbonic_acid_model"


def test_estimated_ph_and_turbulent_shear_composition():
    model=wet(ph=dict(method="condensate",qualification_basis="Qualified unbuffered condensate approximation"),lookup_policy="bilinear",
        flow=dict(method="turbulent_flow",diameter_m=.1,mixture_density_kg_m3=800.,mixture_velocity_m_s=2.,mixture_viscosity_pa_s=.001,
            relative_roughness=.0001,qualification_basis="Qualified effective mixture properties and turbulent wall-flow fixture"))
    r=damage.co2_corrosion_assessment(request(wet_model=model)).outputs
    p=damage.co2_ph_estimate(damage.Co2PhEstimateInput(temperature_k=333.15,co2_partial_pressure_pa_abs=1e5,water_case="condensate",approximation_basis="same fixture")).outputs.estimated_ph
    assert r.model_ph==p and r.requested_shear_stress_pa > 0 and r.corrosion_rate_m_year > 0


@pytest.mark.parametrize("changes,branch",[(dict(free_liquid_water_present=False,wet_model=None),"no_free_water"),
    (dict(co2_partial_pressure_pa_abs=0.,wet_model=None),"no_co2")])
def test_qualified_dry_or_no_co2_is_specific_zero_with_no_fabricated_model_diagnostics(changes,branch):
    r=damage.co2_corrosion_assessment(request(**changes)).outputs
    assert r.corrosion_rate_m_year==0 and r.calculation_branch==branch and r.model_ph is None and r.fugacity_pa is None


@pytest.mark.parametrize("changes",[dict(free_liquid_water_present=False),dict(wet_model=None),dict(temperature_k=423.15),
    dict(co2_partial_pressure_pa_abs=4e6+1),dict(applicability_basis=" "),dict(wet_model=wet(simple_upstream_mixture_and_wetting_basis=" "))])
def test_integrated_scope_and_baseline_qualification(changes):
    with pytest.raises(DomainError):
        damage.co2_corrosion_assessment(request(**changes))


@pytest.mark.parametrize("dry",[False,True])
def test_rate_to_thinning_matches_independent_qualified_kernel(dry):
    strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.02,shape="cylinder")
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    corrosion=request(free_liquid_water_present=False,wet_model=None) if dry else request()
    r=damage.co2_thinning_assessment(damage.Co2ThinningAssessmentInput(corrosion=corrosion,starting_thickness_m=.02,elapsed_years=1.,
        strength=strength,inspections=dict(confidence="high",inspections_a=1),conditions=conditions,qualification_basis="Qualified non-AST inspection and common baseline fixture")).outputs
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope="non_ast_unclad",qualification_basis="same fixture",
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=r.corrosion_rate_m_year,elapsed_years=1.),strength=strength,
        inspections=dict(confidence="high",inspections_a=1),conditions=conditions)).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    if dry:
        assert r.corrosion_rate_m_year==0 and r.thinning_damage_factor >= .1


@pytest.mark.parametrize("changes",[dict(material="stainless_steel"),dict(co2_partial_pressure_pa_abs=-1),dict(co2_partial_pressure_pa_abs=True),
    dict(wet_model=wet(inhibitor_factor=1.1)),dict(temperature_k=float("nan"))])
def test_invalid_material_and_numeric_contracts(changes):
    with pytest.raises(ValidationError):
        request(**changes)
