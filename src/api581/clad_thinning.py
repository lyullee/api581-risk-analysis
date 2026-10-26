"""Cladding/overlay depletion and code-thickness thinning strength ratio, 2016."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, Positive, NonNegative, Fraction, calculation, ensure, finite_tree
from .thinning import (WallLoss, wall_loss, StrengthRatio, strength_ratio, Posterior, posterior,
    ThinningBase, thinning_base, ThinningAdjustment, thinning_adjust)


class CladdingLife(Model):
    starting_total_thickness_m: Positive
    original_base_material_thickness_m: Positive
    cladding_corrosion_rate_m_year: NonNegative


@calculation("damage/cladding-remaining-life", "Cladding or weld overlay depletion time from thickness baseline", CladdingLife,
    ["Part2 §4.5.7 STEP4,eq(2.11); PDF p152"],origin="api581_equation_with_explicit_zero_rate_extension",limitations=[
        "Remaining cladding=max(starting total thickness-original base thickness,0); depletion age divides this by cladding corrosion rate. Base reference thickness is owner-qualified, not auto-inferred from a measured total. No coating/lining equivalence. Zero-rate extension: intact noncorroding cladding has null depletion age, already-depleted cladding has age0; no numeric infinity or division by zero."])
def cladding_life(x):
    remaining = max(x.starting_total_thickness_m-x.original_base_material_thickness_m,0.)
    if remaining == 0:
        age, state = 0., "already_depleted"
    elif x.cladding_corrosion_rate_m_year == 0:
        age, state = None, "noncorroding_present"
    else:
        age, state = remaining/x.cladding_corrosion_rate_m_year, "finite_depletion"
        ensure(math.isfinite(age) and age > 0,"Cladding depletion age outside finite positive range","numerical_failure")
    return {"remaining_cladding_at_baseline_m":remaining,"cladding_depletion_age_years":age,"cladding_baseline_state":state}


class CladWall(CladdingLife):
    base_corrosion_rate_m_year: NonNegative
    elapsed_years: NonNegative


@calculation("damage/thinning-clad-wall-loss", "Sequential cladding and base-material fractional wall loss", CladWall,
    ["Part2 §4.5.7 STEP6(2)-(4),eqs(2.13)-(2.15); PDF pp152-153"],origin="api581_equations_with_explicit_zero_rate_extension",limitations=[
        "Cladding/overlay is assumed to corrode before base material, as source procedure states. Before depletion: cladding rate*elapsed. At/after depletion: cladding rate*depletion age+base rate*(elapsed-depletion age). Already depleted uses base-only eq2.13. Divide by starting TOTAL thickness. Constant rates from same qualified baseline; no simultaneous backside/external corrosion, debonding, coating life or variable process history. Noncorroding intact cladding uses explicit zero-rate analytic extension. Predicted penetration is diagnostic, not FFS acceptance."])
def clad_wall_loss(x):
    life = cladding_life(x)
    age = life["cladding_depletion_age_years"]
    if age == 0:
        clad_loss, base_age, branch = 0., x.elapsed_years, "base_only_eq2_13"
    elif age is None:
        clad_loss, base_age, branch = 0., 0., "noncorroding_cladding_extension"
    elif x.elapsed_years < age:
        clad_loss, base_age, branch = x.cladding_corrosion_rate_m_year*x.elapsed_years, 0., "cladding_only_eq2_14"
    else:
        # Numerically exact boundary amount from eq2.11 avoids multiplying a rounded age back by rate.
        clad_loss, base_age, branch = life["remaining_cladding_at_baseline_m"], x.elapsed_years-age, "cladding_then_base_eq2_15"
    base_loss = x.base_corrosion_rate_m_year*base_age
    loss = clad_loss+base_loss
    remaining = x.starting_total_thickness_m-loss
    fraction = loss/x.starting_total_thickness_m
    finite_tree([clad_loss,base_age,base_loss,loss,remaining,fraction])
    return {**life,"wall_loss_fraction":fraction,"cladding_wall_loss_m":clad_loss,"base_material_wall_loss_m":base_loss,
        "base_material_exposure_years":base_age,"predicted_remaining_thickness_m":remaining,
        "predicted_penetration":remaining <= 0,"wall_loss_branch":branch}


class DesignStrengthRatio(Model):
    allowable_stress_pa: Positive
    weld_efficiency: Fraction = Field(gt=0)
    flow_stress_pa: Positive
    starting_thickness_m: Positive
    minimum_required_thickness_m: NonNegative
    minimum_structural_thickness_m: NonNegative
    design_thickness_basis: str = Field(min_length=1)


@calculation("damage/thinning-design-strength-ratio", "Thinning strength ratio from required and structural thickness", DesignStrengthRatio,
    ["Part2 §4.5.7 STEP5,STEP8,eq(2.17); PDF pp152-154"],limitations=[
        "SR=(allowable stress*weld efficiency/flow stress)*max(code minimum,structural minimum)/starting thickness. Owner supplies qualified code/design thickness including governing internal/external pressure and structural loads. This API does not calculate those code minima or certify buckling strength. Zero explicitly denotes a non-governing term; both minima cannot be zero. Flow stress, allowable stress and efficiency must have consistent design-temperature/material basis; no automatic cladding structural-strength credit."])
def design_strength_ratio(x):
    ensure(bool(x.design_thickness_basis.strip()),"Code/design thickness basis must not be blank")
    governing = max(x.minimum_required_thickness_m,x.minimum_structural_thickness_m)
    ensure(governing > 0,"At least one qualified minimum thickness must be positive")
    ratio = x.allowable_stress_pa/x.flow_stress_pa*x.weld_efficiency*(governing/x.starting_thickness_m)
    ensure(math.isfinite(ratio) and ratio > 0,"Design strength ratio outside finite positive range","numerical_failure")
    return {"strength_ratio":ratio,"governing_minimum_thickness_m":governing,
        "governing_thickness_source":"equal_minima" if x.minimum_required_thickness_m == x.minimum_structural_thickness_m else
        "structural_minimum" if x.minimum_structural_thickness_m > x.minimum_required_thickness_m else "required_minimum"}


class PressureStrength(StrengthRatio):
    method: Literal["internal_pressure_eq2_18"]


class CodeStrength(DesignStrengthRatio):
    method: Literal["design_thickness_eq2_17"]


class CladThinning(Model):
    assessment_scope: Literal["non_ast_pressure_vessel_sequential_cladding"]
    qualification_basis: str = Field(min_length=1)
    wall: CladWall
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    injection_point_factor: Positive
    deadleg_factor: Positive
    online_monitoring_factor: Positive


@calculation("damage/thinning-clad", "Compose clad non-AST thinning with selected strength-ratio method", CladThinning,
    ["Part2 §4.5.7,eqs(2.11),(2.13)-(2.23); PDF pp152-156"],origin="api581_composition_with_explicit_zero_rate_extension",limitations=[
        "Explicit non-AST pressure-vessel sequential-cladding scope; owner qualifies baseline, reference base thickness, corrosion rates, inspection eligibility, monitoring and applicability. Select internal-hoop-pressure eq2.18 only when governing; structural/external-pressure cases require qualified code-minimum eq2.17. Same total starting thickness must drive wall-loss and strength equations. Standard three damage states and conservative default COVs are reused. AST welded/maintenance/settlement factors1; not AST-bottom table, lining protection, simultaneous corrosion or all-mechanism DF. Grade counts must be eligible since same baseline. Zero-rate intact cladding extension is explicit in branch output."])
def clad_thinning(x):
    ensure(bool(x.qualification_basis.strip()),"Cladding/baseline applicability basis must not be blank")
    ensure(x.wall.starting_total_thickness_m == x.strength.starting_thickness_m,"Wall-loss and strength total starting thickness must agree")
    wall = clad_wall_loss(x.wall)
    strength = design_strength_ratio(x.strength) if x.strength.method == "design_thickness_eq2_17" else strength_ratio(x.strength)
    finite_tree(strength)
    post = posterior(x.inspections)
    base = thinning_base(ThinningBase(wall_loss_fraction=wall["wall_loss_fraction"],strength_ratio=strength["strength_ratio"],posterior=post["posterior_probabilities"]))
    final = thinning_adjust(ThinningAdjustment(base_damage_factor=base["base_damage_factor"],injection_point_factor=x.injection_point_factor,
        deadleg_factor=x.deadleg_factor,online_monitoring_factor=x.online_monitoring_factor,welded_construction_factor=1.,maintenance_factor=1.,settlement_factor=1.))
    finite_tree(final)
    return {**wall,"strength_ratio":strength["strength_ratio"],"strength_method":x.strength.method,**post,**base,**final}


class UncladDesignThinning(Model):
    assessment_scope: Literal["non_ast_unclad_design_thickness_governed"]
    qualification_basis: str = Field(min_length=1)
    wall: WallLoss
    strength: DesignStrengthRatio
    inspections: Posterior
    injection_point_factor: Positive
    deadleg_factor: Positive
    online_monitoring_factor: Positive


@calculation("damage/thinning-unclad-design", "Compose unclad thinning with code and structural minimum strength ratio", UncladDesignThinning,
    ["Part2 §4.5.7,eqs(2.13),(2.17),(2.19)-(2.23); PDF pp153-156"],origin="api581_composition",limitations=[
        "Non-AST unclad component with owner-qualified governing code/structural minima. Eq2.17 replaces internal-hoop-only eq2.18; source code minima and load applicability are external inputs, not computed FFS. Starting thickness must agree. No AST construction factors, cladding/lining credit, automatic corrosion-rate selection or all-mechanism DF. Inspection counts and monitoring factors require same baseline and applicable mechanism qualification."])
def unclad_design(x):
    ensure(bool(x.qualification_basis.strip()),"Applicability qualification basis must not be blank")
    ensure(x.wall.starting_thickness_m == x.strength.starting_thickness_m,"Wall-loss and strength starting thickness must agree")
    wall = wall_loss(x.wall)
    finite_tree(wall)
    strength = design_strength_ratio(x.strength)
    post = posterior(x.inspections)
    base = thinning_base(ThinningBase(wall_loss_fraction=wall["wall_loss_fraction"],strength_ratio=strength["strength_ratio"],posterior=post["posterior_probabilities"]))
    final = thinning_adjust(ThinningAdjustment(base_damage_factor=base["base_damage_factor"],injection_point_factor=x.injection_point_factor,
        deadleg_factor=x.deadleg_factor,online_monitoring_factor=x.online_monitoring_factor,welded_construction_factor=1.,maintenance_factor=1.,settlement_factor=1.))
    finite_tree(final)
    return {**wall,**strength,**post,**base,**final}
