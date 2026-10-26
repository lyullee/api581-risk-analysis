"""Monitoring table, qualified-plan gate and localized-piping conditions."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def monitoring(**changes):
    return dict(row=dict(mechanism="hydrochloric_acid"),methods=["key_process_variables","electrical_resistance_probes"],
        organized_monitoring_plan=True,qualification_basis="Qualified mechanism/variables/specialist monitoring intervals fixture",
        key_variables_probe_conjunction_confirmed=True)|changes


def conditions(scope="piping",**changes):
    return dict(monitoring=monitoring(),injection=dict(component_scope=scope,injection_or_mix_point_present=scope=="piping",highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope=scope,deadleg_present=scope=="piping",highly_effective_targeted_inspection=False))|changes


@pytest.mark.parametrize("row,expected",[("hydrochloric_acid",[10,10,2]),("high_temperature_sulfidic_naphthenic",[10,10,2]),
    ("high_temperature_h2s_h2",[1,10,1]),("sulfuric_low_velocity",[20,10,2]),("sulfuric_high_velocity",[10,10,1]),
    ("hydrofluoric_acid",[10,1,1]),("sour_water_low_velocity",[20,10,2]),("sour_water_high_velocity",[10,2,2]),
    ("amine_low_velocity",[20,10,2]),("amine_high_velocity",[10,10,1]),("other",[1,1,1])])
def test_all_33_source_monitoring_cells(row,expected):
    for method,factor in zip(["key_process_variables","electrical_resistance_probes","corrosion_coupons"],expected):
        assert damage.thinning_monitoring_table_factor(damage.ThinningMonitoringTableFactorInput(monitoring_row=row,monitoring_method=method)).outputs.table_monitoring_factor==factor


@pytest.mark.parametrize("material,threshold",[("carbon_steel",3*.3048),("stainless_steel",5*.3048),("higher_alloy",7*.3048)])
def test_sulfuric_exact_us_velocity_thresholds(material,threshold):
    for value,band in [(math.nextafter(threshold,-math.inf),"low"),(threshold,"low"),(math.nextafter(threshold,math.inf),"high")]:
        r=damage.thinning_monitoring_row(damage.ThinningMonitoringRowInput(mechanism="sulfuric_acid",sulfuric_material_group=material,velocity_m_s=value)).outputs
        assert r.monitoring_row==f"sulfuric_{band}_velocity" and r.velocity_threshold_m_s==threshold


def test_sour_threshold_and_amine_no_invented_threshold():
    for velocity,band in [(6.096,"low"),(6.097,"high")]:
        r=damage.thinning_monitoring_row(damage.ThinningMonitoringRowInput(mechanism="sour_water",velocity_m_s=velocity)).outputs
        assert r.monitoring_row==f"sour_water_{band}_velocity"
    for band in ("low","high"):
        r=damage.thinning_monitoring_row(damage.ThinningMonitoringRowInput(mechanism="amine",amine_velocity_regime=band,amine_regime_basis="Owner qualified amine regime")).outputs
        assert r.monitoring_row==f"amine_{band}_velocity" and r.velocity_threshold_m_s is None


@pytest.mark.parametrize("values",[dict(mechanism="sulfuric_acid",velocity_m_s=1.),dict(mechanism="sour_water"),
    dict(mechanism="amine"),dict(mechanism="amine",amine_velocity_regime="low",amine_regime_basis=" "),
    dict(mechanism="other",velocity_m_s=1.),dict(mechanism="hydrochloric_acid",sulfuric_material_group="carbon_steel"),
    dict(mechanism="sour_water",velocity_m_s=1.,amine_velocity_regime="low")])
def test_row_contradictions(values):
    with pytest.raises(DomainError):
        damage.thinning_monitoring_row(damage.ThinningMonitoringRowInput(**values))


@pytest.mark.parametrize("row",["hydrochloric_acid","sulfuric_high_velocity"])
def test_only_two_joint_table_exceptions(row):
    r=damage.thinning_monitoring_table_factor(damage.ThinningMonitoringTableFactorInput(monitoring_row=row,monitoring_method="key_process_variables",key_variables_with_probes=True)).outputs
    assert r.table_monitoring_factor==20
    with pytest.raises(DomainError):
        damage.thinning_monitoring_table_factor(damage.ThinningMonitoringTableFactorInput(monitoring_row=row,monitoring_method="corrosion_coupons",key_variables_with_probes=True))


def test_monitoring_maximum_not_sum_or_product_and_conjunction_gate():
    r=damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**monitoring(key_variables_probe_conjunction_confirmed=False))).outputs
    assert r.online_monitoring_factor==10 and not r.joint_exception_applied
    joint=damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**monitoring())).outputs
    assert joint.online_monitoring_factor==20 and joint.joint_exception_applied
    assert joint.candidate_method_factors==dict(key_process_variables=20.,electrical_resistance_probes=10.)
    all_methods=damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**monitoring(methods=["key_process_variables","electrical_resistance_probes","corrosion_coupons"]))).outputs
    assert all_methods.online_monitoring_factor==20


def test_installed_unqualified_methods_do_not_earn_credit():
    r=damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**monitoring(organized_monitoring_plan=False,
        qualification_basis=None,key_variables_probe_conjunction_confirmed=False))).outputs
    assert r.online_monitoring_factor==1 and r.monitoring_credit_basis=="no_organized_plan"
    assert r.candidate_method_factors==dict(key_process_variables=10.,electrical_resistance_probes=10.)


def test_no_methods_and_owner_experience_replacement():
    empty=monitoring(methods=[],key_variables_probe_conjunction_confirmed=False,qualification_basis=None)
    r=damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**empty)).outputs
    assert r.online_monitoring_factor==1 and r.monitoring_credit_basis=="no_monitoring_methods"
    r=damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**monitoring(experience_factor=7.,experience_factor_basis="Owner experience fixture"))).outputs
    assert r.online_monitoring_factor==7 and r.monitoring_credit_basis=="qualified_experience_replacement" and not r.joint_exception_applied
    r=damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**(empty|dict(experience_factor=3.,experience_factor_basis="Qualified other method",qualification_basis="Specialist organized plan")))).outputs
    assert r.online_monitoring_factor==3


@pytest.mark.parametrize("changes",[dict(methods=["key_process_variables","key_process_variables"]),dict(qualification_basis=" "),
    dict(methods=["key_process_variables"]),dict(experience_factor=5.),dict(experience_factor_basis="unpaired"),
    dict(experience_factor=5.,experience_factor_basis=" "),dict(organized_monitoring_plan=False),
    dict(row=dict(mechanism="other")),dict(organized_monitoring_plan=False,qualification_basis=None,key_variables_probe_conjunction_confirmed=False,experience_factor=3.,experience_factor_basis="override")])
def test_invalid_credit_conditions(changes):
    with pytest.raises(DomainError):
        damage.thinning_online_monitoring_factor(damage.ThinningOnlineMonitoringFactorInput(**monitoring(**changes)))


@pytest.mark.parametrize("feature,method,input_type,output_field",[
    ("injection_or_mix_point_present",damage.thinning_injection_point_factor,damage.ThinningInjectionPointFactorInput,"injection_point_factor"),
    ("deadleg_present",damage.thinning_deadleg_factor,damage.ThinningDeadlegFactorInput,"deadleg_factor")])
def test_piping_features_and_targeted_inspection(feature,method,input_type,output_field):
    for present,inspected,expected in [(False,False,1),(True,False,3),(True,True,1)]:
        r=method(input_type(**{feature:present},component_scope="piping",highly_effective_targeted_inspection=inspected,
            inspection_basis="Qualified highly effective targeted inspection" if inspected else None)).outputs
        assert getattr(r,output_field)==expected
    for values in [dict(component_scope="non_piping",**{feature:True},highly_effective_targeted_inspection=False),
        dict(component_scope="piping",**{feature:False},highly_effective_targeted_inspection=True,inspection_basis="fixture"),
        dict(component_scope="piping",**{feature:True},highly_effective_targeted_inspection=True),
        dict(component_scope="piping",**{feature:True},highly_effective_targeted_inspection=False,inspection_basis="fixture")]:
        with pytest.raises(DomainError):
            method(input_type(**values))


def test_final_condition_adjustment_and_scope_consistency():
    r=damage.thinning_conditional_adjustment(damage.ThinningConditionalAdjustmentInput(assessment_scope="non_ast",base_damage_factor=100.,conditions=conditions())).outputs
    assert r.thinning_damage_factor==45 and r.injection_point_factor==r.deadleg_factor==3
    low=damage.thinning_conditional_adjustment(damage.ThinningConditionalAdjustmentInput(assessment_scope="non_ast",base_damage_factor=0.,conditions=conditions())).outputs
    assert low.thinning_damage_factor==.1
    mismatch=conditions(deadleg=dict(component_scope="non_piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    with pytest.raises(DomainError):
        damage.thinning_conditional_adjustment(damage.ThinningConditionalAdjustmentInput(assessment_scope="non_ast",base_damage_factor=100.,conditions=mismatch))


@pytest.mark.parametrize("method",["internal_pressure_eq2_18","design_thickness_eq2_17"])
def test_qualified_unclad_matches_independent_numeric_api(method):
    wall=dict(starting_thickness_m=.01,corrosion_rate_m_year=.0002,elapsed_years=10.)
    inspections=dict(confidence="high",inspections_a=1)
    strength=(dict(differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.01,shape="cylinder") if method=="internal_pressure_eq2_18" else
        dict(allowable_stress_pa=100e6,weld_efficiency=1.,flow_stress_pa=250e6,starting_thickness_m=.01,minimum_required_thickness_m=.005,
            minimum_structural_thickness_m=.006,design_thickness_basis="Qualified code fixture"))
    r=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope="non_ast_unclad",qualification_basis="Qualified fixture",
        wall=wall,strength=strength|dict(method=method),inspections=inspections,conditions=conditions())).outputs
    numeric=dict(wall=wall,strength=strength,inspections=inspections,injection_point_factor=3.,deadleg_factor=3.,online_monitoring_factor=20.)
    direct=(damage.thinning_unclad(damage.ThinningUncladInput(**numeric)) if method=="internal_pressure_eq2_18" else
        damage.thinning_unclad_design(damage.ThinningUncladDesignInput(**numeric,assessment_scope="non_ast_unclad_design_thickness_governed",qualification_basis="fixture"))).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor and r.strength_method==method
    assert r.online_monitoring_factor==20


def test_qualified_clad_matches_independent_numeric_api():
    args=dict(qualification_basis="Qualified pressure vessel fixture",
        wall=dict(starting_total_thickness_m=.012,original_base_material_thickness_m=.01,cladding_corrosion_rate_m_year=.0002,base_corrosion_rate_m_year=.0005,elapsed_years=15.),
        strength=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=.5,flow_stress_pa=250e6,starting_thickness_m=.012,shape="cylinder"),
        inspections=dict(confidence="medium",inspections_b=1))
    r=damage.thinning_clad_qualified(damage.ThinningCladQualifiedInput(**args,assessment_scope="non_ast_pressure_vessel_sequential_cladding",conditions=conditions("non_piping"))).outputs
    direct=damage.thinning_clad(damage.ThinningCladInput(**args,assessment_scope="non_ast_pressure_vessel_sequential_cladding",injection_point_factor=1.,deadleg_factor=1.,online_monitoring_factor=20.)).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor and r.wall_loss_branch==direct.wall_loss_branch
    with pytest.raises(DomainError):
        damage.thinning_clad_qualified(damage.ThinningCladQualifiedInput(**args,assessment_scope="non_ast_pressure_vessel_sequential_cladding",conditions=conditions()))


@pytest.mark.parametrize("values",[dict(experience_factor=0.,experience_factor_basis="fixture"),dict(experience_factor=float("nan"),experience_factor_basis="fixture"),
    dict(methods=["hydrogen_flux"]),dict(row=dict(mechanism="sour_water",velocity_m_s=-1.))])
def test_numeric_and_unknown_method_validation(values):
    with pytest.raises(ValidationError):
        damage.ThinningOnlineMonitoringFactorInput(**monitoring(**values))
