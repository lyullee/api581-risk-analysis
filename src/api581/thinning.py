"""2016 Part 2 §4.5.7 thinning calculations; no cladding/AST auto-selection."""
import math
from typing import Literal
from pydantic import Field, model_validator
from .core import Model, Positive, NonNegative, Fraction, calculation

PRIORS = {"low": (.5, .3, .2), "medium": (.7, .2, .1), "high": (.8, .15, .05)}
LIKELIHOODS = {"a": (.9, .09, .01), "b": (.7, .2, .1), "c": (.5, .3, .2), "d": (.4, .33, .27)}


class WallLoss(Model):
    starting_thickness_m: Positive
    corrosion_rate_m_year: NonNegative
    elapsed_years: NonNegative


@calculation("damage/thinning-wall-loss", "Unclad fractional wall loss", WallLoss,
             ["Part 2 eq (2.13)"], limitations=["No cladding/weld overlay; not AST-bottom equation (2.12)."])
def wall_loss(x):
    return {"wall_loss_fraction": x.corrosion_rate_m_year * x.elapsed_years / x.starting_thickness_m}


class FlowStress(Model):
    yield_strength_pa: Positive
    tensile_strength_pa: Positive
    weld_efficiency: Fraction = Field(gt=0)


@calculation("damage/flow-stress", "Thinning flow stress", FlowStress,
             ["Part 2 eq (2.16)"])
def flow_stress(x):
    return {"flow_stress_pa": (x.yield_strength_pa + x.tensile_strength_pa) / 2 * x.weld_efficiency * 1.1}


class StrengthRatio(Model):
    differential_pressure_pa: NonNegative
    diameter_m: Positive
    flow_stress_pa: Positive
    starting_thickness_m: Positive
    shape: Literal["cylinder", "sphere", "head"]


@calculation("damage/thinning-strength-ratio", "Internal-pressure thinning strength ratio", StrengthRatio,
             ["Part 2 eq (2.18); PDF p154"],
             limitations=["Internal hoop pressure only; not suitable when external pressure or structural loads govern."])
def strength_ratio(x):
    alpha = {"cylinder": 2, "sphere": 4, "head": 1.13}[x.shape]
    return {"strength_ratio": x.differential_pressure_pa * x.diameter_m / (alpha * x.flow_stress_pa * x.starting_thickness_m)}


class PriorSelection(Model):
    confidence: Literal['low','medium','high'] | None = None
    custom_prior_probabilities: list[Fraction] | None = Field(default=None,min_length=3,max_length=3)
    custom_prior_basis: str | None = Field(default=None,min_length=1)

    @model_validator(mode='after')
    def qualified_prior_choice(self):
        custom=self.custom_prior_probabilities is not None
        if (self.confidence is not None)==custom:
            raise ValueError('Select exactly one confidence table row or custom prior probabilities')
        if custom:
            if self.custom_prior_basis is None or not self.custom_prior_basis.strip():
                raise ValueError('Custom prior probabilities require an experience/measurement qualification basis')
            if not math.isclose(math.fsum(self.custom_prior_probabilities),1.,rel_tol=0.,abs_tol=1e-9):
                raise ValueError('Custom prior probabilities must sum to1')
        elif self.custom_prior_basis is not None:
            raise ValueError('Custom prior basis is unused with a confidence table row')
        return self


@calculation('damage/thinning-prior-selection','Table4.5 or qualified customized thinning damage-state prior',PriorSelection,
    ['Part2 §4.5.3; Table4.5; PDF pp150-151,163'],limitations=[
        'Exactly one low/medium/high table row or three owner-qualified prior probabilities for damage states1/2/3 (rate factors1/2/4). Source permits customization from actual experience and confidence in thickness measurements; no automatic calibration or general-to-local applicability inference. Custom sum tolerance1e-9 removes only rounding by normalization. A zero prior cannot be revived by subsequent positive-likelihood inspections; no probability floor is invented.'])
def prior_selection(x):
    values=list(PRIORS[x.confidence]) if x.custom_prior_probabilities is None else list(x.custom_prior_probabilities)
    total=math.fsum(values)
    return {'prior_probabilities':[p/total for p in values],
        'prior_source':'table4_5' if x.custom_prior_probabilities is None else 'qualified_custom',
        'confidence':x.confidence,'zero_prior_state_indices':[i+1 for i,p in enumerate(values) if p==0.]}


class Posterior(PriorSelection):
    inspections_a: int = Field(default=0, ge=0, le=100000)
    inspections_b: int = Field(default=0, ge=0, le=100000)
    inspections_c: int = Field(default=0, ge=0, le=100000)
    inspections_d: int = Field(default=0, ge=0, le=100000)


@calculation("damage/thinning-posterior", "Bayesian thinning damage-state probabilities", Posterior,
             ["Part 2 eqs (2.19)-(2.20), Tables 4.5-4.6; PDF pp154,163"],
             limitations=["Counts must include only inspections eligible in the assessed period; no equivalent-count conversion. Prior is exactly one confidence table row or qualified customized three-state probabilities per section4.5.3. Zero custom prior remains zero; no floor or automatic calibration."])
def posterior(x):
    prior=prior_selection(PriorSelection(**x.model_dump(include=set(PriorSelection.model_fields))))['prior_probabilities']
    logs = [math.log(p) if p>0 else -math.inf for p in prior]
    for grade in "abcd":
        for i in range(3):
            logs[i] += getattr(x, "inspections_" + grade) * math.log(LIKELIHOODS[grade][i])
    offset = max(logs)
    weights = [math.exp(v - offset) for v in logs]
    total = math.fsum(weights)
    return {"posterior_probabilities": [v / total for v in weights]}


class ThinningBase(Model):
    wall_loss_fraction: NonNegative
    strength_ratio: NonNegative
    posterior: list[Fraction] = Field(min_length=3, max_length=3)
    cov_wall_loss: Positive = .2
    cov_strength: Positive = .2
    cov_pressure: Positive = .05


@calculation("damage/thinning-base", "Thinning reliability indices and base damage factor", ThinningBase,
             ["Part 2 eqs (2.21)-(2.22); PDF p155"], limitations=["Excludes AST bottoms; final adjustment factors applied separately."])
def thinning_base(x):
    from .core import ensure
    ensure(math.isclose(math.fsum(x.posterior), 1, abs_tol=1e-9), "Posterior probabilities must sum to 1")
    betas = []
    failures = []
    for scale in (1, 2, 4):
        loss = scale * x.wall_loss_fraction
        variance = loss ** 2 * x.cov_wall_loss ** 2 + (1 - loss) ** 2 * x.cov_strength ** 2 + x.strength_ratio ** 2 * x.cov_pressure ** 2
        beta = (1 - loss - x.strength_ratio) / math.sqrt(variance)
        betas.append(beta)
        failures.append(.5 * math.erfc(beta / math.sqrt(2)))
    probability = math.fsum(p * f for p, f in zip(x.posterior, failures))
    return {"reliability_indices": betas, "damage_state_failure_probabilities": failures,
            "weighted_failure_probability": probability, "base_damage_factor": probability / 1.56e-4}


class ThinningAdjustment(Model):
    base_damage_factor: NonNegative
    injection_point_factor: Positive
    deadleg_factor: Positive
    welded_construction_factor: Positive
    maintenance_factor: Positive
    settlement_factor: Positive
    online_monitoring_factor: Positive


@calculation("damage/thinning-adjust", "Apply thinning damage factor adjustments", ThinningAdjustment,
             ["Part 2 eq (2.23); PDF pp155-156"], limitations=["Caller supplies applicable factors; does not determine AST eligibility or monitoring category."])
def thinning_adjust(x):
    value = x.base_damage_factor * x.injection_point_factor * x.deadleg_factor * x.welded_construction_factor * x.maintenance_factor * x.settlement_factor / x.online_monitoring_factor
    return {"thinning_damage_factor": max(value, .1)}


class UncladThinning(Model):
    wall: WallLoss
    strength: StrengthRatio
    inspections: Posterior
    injection_point_factor: Positive
    deadleg_factor: Positive
    online_monitoring_factor: Positive


@calculation("damage/thinning-unclad", "Compose unclad non-AST thinning damage calculation", UncladThinning,
             ["Part 2 §4.5.7 eqs (2.13), (2.18)-(2.23)"],
             limitations=["Non-AST, unclad, internal-pressure-governed components only. Flow stress and corrosion rate are caller-supplied. Automatic corrosion mechanism/monitoring selection is not included."])
def unclad(x):
    from .core import ensure
    ensure(x.wall.starting_thickness_m == x.strength.starting_thickness_m, "Wall and strength thickness must match")
    loss = wall_loss(x.wall)
    sr = strength_ratio(x.strength)
    post = posterior(x.inspections)
    base = thinning_base(ThinningBase(wall_loss_fraction=loss["wall_loss_fraction"], strength_ratio=sr["strength_ratio"],
                                     posterior=post["posterior_probabilities"]))
    final = thinning_adjust(ThinningAdjustment(base_damage_factor=base["base_damage_factor"],
                            injection_point_factor=x.injection_point_factor, deadleg_factor=x.deadleg_factor,
                            online_monitoring_factor=x.online_monitoring_factor, welded_construction_factor=1,
                            maintenance_factor=1, settlement_factor=1))
    return {**loss, **sr, **post, **base, **final}
