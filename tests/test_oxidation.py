"""Oxidation source rows incl. dash cells and qualified rate-to-DF composition."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def lookup(**changes):
    return dict(material="carbon_steel",unit_basis="printed_si",maximum_metal_temperature_k=635+273.15,
        lookup_policy="exact_nodes_only",below_table_policy="reject_below_table")|changes


def assessment(**changes):
    return dict(oxidation=lookup(),oxygen_present=True,screening_threshold_basis="printed_si",applicability_basis="Qualified oxidation maximum exposed metal temperature/material fixture")|changes


@pytest.mark.parametrize("material,us,si",[
    ("carbon_steel",[2,4,6,9,14,22,33,48],[.05,.1,.15,.23,.36,.56,.84,1.22]),
    ("cr_1_25",[2,3,4,7,12,18,30,46],[.05,.08,.1,.18,.3,.46,.76,1.17]),
    ("cr_2_25",[1,1,2,4,9,14,24,41],[.03,.03,.05,.1,.23,.36,.61,1.04]),
    ("cr_5",[1,1,1,2,4,6,15,35,65],[.03,.03,.03,.05,.1,.15,.38,.89,1.65]),
    ("cr_7",[1,1,1,1,1,2,3,6,17,37,60],[.03,.03,.03,.03,.03,.05,.08,.15,.43,.94,1.52]),
    ("cr_9",[1,1,1,1,1,1,1,2,5,11,23,40,60],[.03,.03,.03,.03,.03,.03,.03,.05,.13,.28,.58,1.02,1.52]),
    ("cr_12",[1,1,1,1,1,1,1,1,3,8,15,30,50],[.03,.03,.03,.03,.03,.03,.03,.03,.08,.2,.38,.76,1.27]),
    ("ss_304",[1,1,1,1,1,1,1,1,1,2,3,4,6,9,13,18,25,35,48],[.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.15,.23,.33,.46,.64,.89,1.22]),
    ("ss_309",[1,1,1,1,1,1,1,1,1,1,2,3,4,6,8,10,13,16,20,30,40,50],[.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.15,.2,.25,.33,.41,.51,.76,1.02,1.27]),
    ("ss_310_hk",[1,1,1,1,1,1,1,1,1,1,1,2,3,4,5,7,8,10,13,15,19,23,27,31],[.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.13,.18,.2,.25,.33,.38,.48,.58,.69,.79]),
    ("alloy_800h_hp",[1,1,1,1,1,1,1,1,1,1,1,2,3,4,6,8,10,13,17,21,27,33,41,50],[.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.03,.05,.08,.1,.15,.2,.25,.33,.43,.53,.69,.84,1.04,1.27])])
def test_all_528_positions_318_numeric_cells_210_unavailable(material,us,si):
    c=[496,524,552,579,607,635,663,691,718,746,774,802,829,857,885,913,941,968,996,1024,1052,1079,1107,1135]
    for basis,values,nodes,conversion in [("printed_si",si,[v+273.15 for v in c],.001),
        ("printed_us_converted",us,[(f-32)*5/9+273.15 for f in range(925,2076,50)],.0000254)]:
        row=damage.oxidation_table_row(damage.OxidationTableRowInput(material=material,unit_basis=basis)).outputs
        assert row.temperature_nodes_k==nodes and len(row.native_rates)==len(row.corrosion_rates_m_year)==24
        for i,t in enumerate(nodes):
            args=damage.OxidationRateInput(**lookup(material=material,unit_basis=basis,maximum_metal_temperature_k=t))
            if i < len(values):
                assert row.native_rates[i]==values[i]
                assert row.corrosion_rates_m_year[i]==pytest.approx(values[i]*conversion)
                r=damage.oxidation_rate(args).outputs
                assert r.corrosion_rate_m_year==pytest.approx(values[i]*conversion)
            else:
                assert row.native_rates[i] is None and row.corrosion_rates_m_year[i] is None
                with pytest.raises(DomainError) as error:
                    damage.oxidation_rate(args)
                assert error.value.code=="oxidation_rate_unavailable"


@pytest.mark.parametrize("basis,threshold",[("printed_si",755.15),("printed_us_converted",(900-32)*5/9+273.15)])
def test_screen_threshold_exact_and_neighbor(basis,threshold):
    for t,met in [(math.nextafter(threshold,0),False),(threshold,True),(math.nextafter(threshold,math.inf),True)]:
        r=damage.oxidation_screen(damage.OxidationScreenInput(maximum_metal_temperature_k=t,oxygen_present=True,threshold_basis=basis)).outputs
        assert r.temperature_screen_met==met and r.evaluate_high_temperature_oxidation==met
    r=damage.oxidation_screen(damage.OxidationScreenInput(maximum_metal_temperature_k=threshold+100,oxygen_present=False,threshold_basis=basis)).outputs
    assert r.temperature_screen_met and not r.evaluate_high_temperature_oxidation


@pytest.mark.parametrize("policy,value",[("linear_between_nodes",.0007),("upper_temperature_node",.00084)])
def test_explicit_temperature_interpolation(policy,value):
    r=damage.oxidation_rate(damage.OxidationRateInput(**lookup(maximum_metal_temperature_k=649+273.15,lookup_policy=policy))).outputs
    assert r.corrosion_rate_m_year==pytest.approx(value) and r.interpolation_weight==.5
    with pytest.raises(DomainError):
        damage.oxidation_rate(damage.OxidationRateInput(**lookup(maximum_metal_temperature_k=649+273.15)))


def test_joined_table_interval_only_when_both_cells_exist():
    r=damage.oxidation_rate(damage.OxidationRateInput(**lookup(material="cr_9",maximum_metal_temperature_k=(802+829)/2+273.15,lookup_policy="linear_between_nodes"))).outputs
    assert r.corrosion_rate_m_year==pytest.approx((1.02+1.52)/2/1000)
    for policy in ["linear_between_nodes","upper_temperature_node"]:
        with pytest.raises(DomainError):
            damage.oxidation_rate(damage.OxidationRateInput(**lookup(maximum_metal_temperature_k=700+273.15,lookup_policy=policy)))


def test_below_first_node_is_not_automatically_zero_or_a_table_row():
    with pytest.raises(DomainError):
        damage.oxidation_rate(damage.OxidationRateInput(**lookup(maximum_metal_temperature_k=490+273.15)))
    r=damage.oxidation_rate(damage.OxidationRateInput(**lookup(maximum_metal_temperature_k=490+273.15,
        below_table_policy="qualified_first_node_value",first_node_qualification_basis="Owner qualified first-row estimate for source gap"))).outputs
    assert r.corrosion_rate_m_year==.00005 and r.first_node_value_used and r.rate_calculation_basis=="qualified_first_node"


@pytest.mark.parametrize("changes",[dict(below_table_policy="qualified_first_node_value"),
    dict(below_table_policy="qualified_first_node_value",first_node_qualification_basis=" "),dict(first_node_qualification_basis="unused")])
def test_gap_qualification_consistency(changes):
    with pytest.raises(DomainError):
        damage.oxidation_rate(damage.OxidationRateInput(**lookup(**changes)))


def test_after_last_global_node_no_extrapolation():
    with pytest.raises(DomainError) as error:
        damage.oxidation_rate(damage.OxidationRateInput(**lookup(material="ss_310_hk",maximum_metal_temperature_k=1136+273.15,lookup_policy="upper_temperature_node")))
    assert error.value.code=="oxidation_table_range"


@pytest.mark.parametrize("changes",[dict(oxygen_present=False),dict(applicability_basis=" "),dict(oxidation=lookup(maximum_metal_temperature_k=400+273.15,
    below_table_policy="qualified_first_node_value",first_node_qualification_basis="not an onset qualification"))])
def test_failed_screen_is_error_not_invented_zero_rate(changes):
    with pytest.raises(DomainError):
        damage.oxidation_assessment(damage.OxidationAssessmentInput(**assessment(**changes)))


def test_qualified_oxidation_assessment():
    r=damage.oxidation_assessment(damage.OxidationAssessmentInput(**assessment())).outputs
    assert r.thinning_type=="general" and r.corrosion_rate_m_year==pytest.approx(.00056)


def test_rate_to_thinning_and_prohibition_on_borrowed_liquid_monitoring_credit():
    strength=dict(method="design_thickness_eq2_17",allowable_stress_pa=50e6,weld_efficiency=1.,flow_stress_pa=150e6,starting_thickness_m=.02,
        minimum_required_thickness_m=.006,minimum_structural_thickness_m=.007,design_thickness_basis="Qualified at governing high design temperature")
    conditions=dict(monitoring=dict(row=dict(mechanism="other"),methods=[],organized_monitoring_plan=False),
        injection=dict(component_scope="piping",injection_or_mix_point_present=False,highly_effective_targeted_inspection=False),
        deadleg=dict(component_scope="piping",deadleg_present=False,highly_effective_targeted_inspection=False))
    args=dict(corrosion=assessment(),starting_thickness_m=.02,elapsed_years=5.,strength=strength,inspections=dict(confidence="high",inspections_a=1),
        conditions=conditions,qualification_basis="Qualified general oxidation inspection, material strength at design temperature and common baseline")
    r=damage.oxidation_thinning_assessment(damage.OxidationThinningAssessmentInput(**args)).outputs
    direct=damage.thinning_unclad_qualified(damage.ThinningUncladQualifiedInput(assessment_scope="non_ast_unclad",qualification_basis="same fixture",
        wall=dict(starting_thickness_m=.02,corrosion_rate_m_year=.00056,elapsed_years=5.),strength=strength,inspections=args["inspections"],conditions=conditions)).outputs
    assert r.wall_loss_fraction==pytest.approx(.14) and r.thinning_damage_factor==pytest.approx(direct.thinning_damage_factor)
    wrong=conditions|dict(monitoring=dict(row=dict(mechanism="hydrochloric_acid"),methods=["key_process_variables"],organized_monitoring_plan=True,qualification_basis="HCl plan cannot qualify oxidation"))
    with pytest.raises(DomainError):
        damage.oxidation_thinning_assessment(damage.OxidationThinningAssessmentInput(**(args|dict(conditions=wrong))))


@pytest.mark.parametrize("changes",[dict(material="cr_6"),dict(unit_basis="auto"),dict(maximum_metal_temperature_k=True),dict(maximum_metal_temperature_k=float("inf"))])
def test_unsupported_material_and_numeric_contract(changes):
    with pytest.raises(ValidationError):
        damage.OxidationRateInput(**lookup(**changes))
