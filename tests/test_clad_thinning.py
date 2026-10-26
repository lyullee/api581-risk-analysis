"""Cladding depletion, source equation switches and design-strength composition."""
import math
import pytest
from pydantic import ValidationError
from api581 import DomainError
from api581.api import damage


def wall(**changes):
    return dict(starting_total_thickness_m=.012,original_base_material_thickness_m=.01,
        cladding_corrosion_rate_m_year=.0002,base_corrosion_rate_m_year=.0005,elapsed_years=15.)|changes


def design(**changes):
    return dict(allowable_stress_pa=120e6,weld_efficiency=.85,flow_stress_pa=300e6,starting_thickness_m=.012,
        minimum_required_thickness_m=.004,minimum_structural_thickness_m=.006,
        design_thickness_basis="Qualified code/load-combination minimum fixture")|changes


def clad(**changes):
    return damage.ThinningCladInput(**(dict(assessment_scope="non_ast_pressure_vessel_sequential_cladding",
        qualification_basis="Qualified constant rates and common thickness/time baseline fixture",wall=wall(),
        strength=design()|dict(method="design_thickness_eq2_17"),inspections=dict(confidence="medium",inspections_b=1),
        injection_point_factor=1.,deadleg_factor=1.,online_monitoring_factor=1.)|changes))


@pytest.mark.parametrize("start,base,rate,age,state",[(.012,.01,.0002,10.,"finite_depletion"),
    (.01,.01,.0002,0.,"already_depleted"),(.009,.01,0.,0.,"already_depleted"),
    (.012,.01,0.,None,"noncorroding_present")])
def test_depletion_and_zero_rate_states(start,base,rate,age,state):
    r=damage.cladding_remaining_life(damage.CladdingRemainingLifeInput(starting_total_thickness_m=start,
        original_base_material_thickness_m=base,cladding_corrosion_rate_m_year=rate)).outputs
    assert r.cladding_depletion_age_years == (None if age is None else pytest.approx(age))
    assert r.cladding_baseline_state==state


@pytest.mark.parametrize("elapsed,clad_loss,base_loss,branch",[(0.,0.,0.,"cladding_only_eq2_14"),
    (5.,.001,0.,"cladding_only_eq2_14"),(15.,.002,.0025,"cladding_then_base_eq2_15"),
    (40.,.002,.015,"cladding_then_base_eq2_15")])
def test_sequential_loss_anchors(elapsed,clad_loss,base_loss,branch):
    r=damage.thinning_clad_wall_loss(damage.ThinningCladWallLossInput(**wall(elapsed_years=elapsed))).outputs
    assert r.cladding_wall_loss_m==pytest.approx(clad_loss) and r.base_material_wall_loss_m==pytest.approx(base_loss)
    assert r.wall_loss_fraction==pytest.approx((clad_loss+base_loss)/.012)
    assert r.predicted_remaining_thickness_m==pytest.approx(.012-clad_loss-base_loss)
    assert r.predicted_penetration==((clad_loss+base_loss)>=.012)
    assert r.wall_loss_branch==branch


def test_exact_depletion_boundary_is_continuous_and_uses_second_branch():
    life=damage.cladding_remaining_life(damage.CladdingRemainingLifeInput(**{k:wall()[k] for k in (
        "starting_total_thickness_m","original_base_material_thickness_m","cladding_corrosion_rate_m_year")})).outputs
    age=life.cladding_depletion_age_years
    results=[damage.thinning_clad_wall_loss(damage.ThinningCladWallLossInput(**wall(elapsed_years=t))).outputs
        for t in (math.nextafter(age,-math.inf),age,math.nextafter(age,math.inf))]
    assert results[0].wall_loss_branch=="cladding_only_eq2_14"
    assert results[1].wall_loss_branch==results[2].wall_loss_branch=="cladding_then_base_eq2_15"
    assert results[1].base_material_exposure_years==0.
    assert all(r.wall_loss_fraction==pytest.approx(.002/.012) for r in results)


def test_intact_zero_rate_does_not_apply_base_rate_early():
    r=damage.thinning_clad_wall_loss(damage.ThinningCladWallLossInput(**wall(cladding_corrosion_rate_m_year=0.,elapsed_years=100.))).outputs
    assert r.wall_loss_fraction==0 and r.base_material_exposure_years==0
    assert r.cladding_depletion_age_years is None and r.wall_loss_branch=="noncorroding_cladding_extension"


@pytest.mark.parametrize("start",[.01,.009])
def test_depleted_baseline_is_base_only_with_zero_clad_rate(start):
    r=damage.thinning_clad_wall_loss(damage.ThinningCladWallLossInput(**wall(starting_total_thickness_m=start,
        cladding_corrosion_rate_m_year=0.,elapsed_years=5.))).outputs
    assert r.cladding_wall_loss_m==0 and r.base_material_wall_loss_m==.0025
    assert r.wall_loss_fraction==pytest.approx(.0025/start) and r.wall_loss_branch=="base_only_eq2_13"


@pytest.mark.parametrize("minimum,structural,value,source",[(.004,.006,.17,"structural_minimum"),
    (.006,.004,.17,"required_minimum"),(.006,.006,.17,"equal_minima"),(.004,0.,.34/3,"required_minimum")])
def test_design_equation_governing_thickness(minimum,structural,value,source):
    r=damage.thinning_design_strength_ratio(damage.ThinningDesignStrengthRatioInput(**design(
        minimum_required_thickness_m=minimum,minimum_structural_thickness_m=structural))).outputs
    assert r.strength_ratio==pytest.approx(value) and r.governing_thickness_source==source
    assert r.governing_minimum_thickness_m==max(minimum,structural)


@pytest.mark.parametrize("changes",[dict(minimum_required_thickness_m=0.,minimum_structural_thickness_m=0.),dict(design_thickness_basis=" ")])
def test_design_requires_qualified_nonzero_minimum(changes):
    with pytest.raises(DomainError):
        damage.thinning_design_strength_ratio(damage.ThinningDesignStrengthRatioInput(**design(**changes)))


def test_clad_assessment_matches_independent_primitives():
    x=clad()
    r=damage.thinning_clad(x).outputs
    w=damage.thinning_clad_wall_loss(damage.ThinningCladWallLossInput(**wall())).outputs
    s=damage.thinning_design_strength_ratio(damage.ThinningDesignStrengthRatioInput(**design())).outputs
    p=damage.thinning_posterior(damage.ThinningPosteriorInput(confidence="medium",inspections_b=1)).outputs
    b=damage.thinning_base(damage.ThinningBaseInput(wall_loss_fraction=w.wall_loss_fraction,strength_ratio=s.strength_ratio,posterior=p.posterior_probabilities)).outputs
    assert r.wall_loss_fraction==pytest.approx(.375)
    assert r.strength_ratio==pytest.approx(.17)
    assert r.reliability_indices==b.reliability_indices and r.thinning_damage_factor==max(b.base_damage_factor,.1)


def test_pressure_method_uses_same_total_thickness():
    pressure=dict(method="internal_pressure_eq2_18",differential_pressure_pa=2e6,diameter_m=1.,flow_stress_pa=300e6,
        starting_thickness_m=.012,shape="cylinder")
    r=damage.thinning_clad(clad(strength=pressure)).outputs
    assert r.strength_method=="internal_pressure_eq2_18" and r.strength_ratio==pytest.approx(2e6/(2*300e6*.012))
    with pytest.raises(DomainError):
        damage.thinning_clad(clad(strength=pressure|dict(starting_thickness_m=.01)))


def test_depleted_clad_matches_existing_unclad_kernel():
    pressure=dict(differential_pressure_pa=2e6,diameter_m=1.,flow_stress_pa=300e6,starting_thickness_m=.01,shape="cylinder")
    inspections=dict(confidence="high",inspections_a=1)
    r=damage.thinning_clad(clad(wall=wall(starting_total_thickness_m=.01,cladding_corrosion_rate_m_year=0.,elapsed_years=5.),
        strength=pressure|dict(method="internal_pressure_eq2_18"),inspections=inspections)).outputs
    direct=damage.thinning_unclad(damage.ThinningUncladInput(wall=dict(starting_thickness_m=.01,corrosion_rate_m_year=.0005,elapsed_years=5.),
        strength=pressure,inspections=inspections,injection_point_factor=1.,deadleg_factor=1.,online_monitoring_factor=1.)).outputs
    assert r.thinning_damage_factor==direct.thinning_damage_factor
    assert r.wall_loss_fraction==direct.wall_loss_fraction and r.posterior_probabilities==direct.posterior_probabilities


def test_unclad_code_minimum_matches_equivalent_pressure_case():
    # Choose S*E*tmin=P*D/2: both equations must give same SR.
    d=design(allowable_stress_pa=100e6,weld_efficiency=1.,starting_thickness_m=.01,minimum_required_thickness_m=.005,minimum_structural_thickness_m=0.)
    w=dict(starting_thickness_m=.01,corrosion_rate_m_year=.0002,elapsed_years=10.)
    inspections=dict(confidence="high",inspections_a=1)
    factors=dict(injection_point_factor=1.,deadleg_factor=1.,online_monitoring_factor=1.)
    r=damage.thinning_unclad_design(damage.ThinningUncladDesignInput(assessment_scope="non_ast_unclad_design_thickness_governed",
        qualification_basis="Qualified unclad code-minimum fixture",wall=w,strength=d,inspections=inspections,**factors)).outputs
    p=dict(starting_thickness_m=.01,differential_pressure_pa=1e6,diameter_m=1.,flow_stress_pa=300e6,shape="cylinder")
    direct=damage.thinning_unclad(damage.ThinningUncladInput(wall=w,strength=p,inspections=inspections,**factors)).outputs
    assert r.strength_ratio==pytest.approx(direct.strength_ratio)
    assert r.thinning_damage_factor==pytest.approx(direct.thinning_damage_factor)


def test_same_wall_different_structural_minimum_changes_damage():
    weak=damage.thinning_clad(clad()).outputs
    critical=damage.thinning_clad(clad(strength=design(minimum_structural_thickness_m=.01)|dict(method="design_thickness_eq2_17"))).outputs
    assert critical.strength_ratio > weak.strength_ratio and critical.thinning_damage_factor > weak.thinning_damage_factor


@pytest.mark.parametrize("changes",[dict(qualification_basis=" "),dict(strength=design(starting_thickness_m=.01)|dict(method="design_thickness_eq2_17"))])
def test_composition_basis_and_thickness_mismatch(changes):
    with pytest.raises(DomainError):
        damage.thinning_clad(clad(**changes))


@pytest.mark.parametrize("changes",[dict(assessment_scope="ast_bottom"),dict(wall=wall(base_corrosion_rate_m_year=-1)),
    dict(wall=wall(cladding_corrosion_rate_m_year=float("nan"))),dict(wall=wall(elapsed_years=True)),
    dict(strength=design(weld_efficiency=0.)|dict(method="design_thickness_eq2_17")),
    dict(strength=design()|dict(method="unknown"))])
def test_scope_and_invalid_numeric_data(changes):
    with pytest.raises(ValidationError):
        clad(**changes)


def test_finite_numeric_failures_not_false_zero_loss():
    with pytest.raises(DomainError):
        damage.cladding_remaining_life(damage.CladdingRemainingLifeInput(starting_total_thickness_m=1.,original_base_material_thickness_m=.5,
            cladding_corrosion_rate_m_year=1e-320))
    with pytest.raises(DomainError):
        damage.thinning_clad_wall_loss(damage.ThinningCladWallLossInput(**wall(starting_total_thickness_m=.01,base_corrosion_rate_m_year=1e308)))


def test_no_inspection_and_intact_cladding_still_has_nonzero_damage_floor():
    r=damage.thinning_clad(clad(wall=wall(cladding_corrosion_rate_m_year=0.),inspections=dict(confidence="low"))).outputs
    assert r.wall_loss_fraction==0 and r.thinning_damage_factor >= .1
