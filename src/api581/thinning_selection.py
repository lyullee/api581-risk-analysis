"""Source-wide measured-rate precedence and multi-mechanism thinning selection."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure
from .thinning import WallLoss, Posterior
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad


class MeasuredThinningRate(Model):
    corrosion_rate_m_year: NonNegative
    representative_for_current_period: bool
    measurement_basis: str = Field(min_length=1)


class FallbackThinningRate(Model):
    corrosion_rate_m_year: NonNegative
    method: Literal['calculated','estimated']
    rate_basis: str = Field(min_length=1)


class MechanismThinningRate(Model):
    mechanism_id: str = Field(min_length=1,max_length=100)
    thinning_type: Literal['general','local']
    measured: MeasuredThinningRate | None = None
    fallback: FallbackThinningRate | None = None


class ThinningRateSelection(Model):
    mechanisms: list[MechanismThinningRate] = Field(min_length=1,max_length=100)
    applicability_and_period_basis: str = Field(min_length=1)


@calculation('damage/thinning-rate-selection','Measured-first and maximum-mechanism rate with governing thinning type',ThinningRateSelection,
    ['Part2 §§4.5.2,4.5.4; PDF pp150-151'],limitations=[
        'Caller supplies all applicable mechanisms for one component, assessed surface and common current-process plan period. Representative measured CML/history rate wins within each mechanism, including explicit zero. Otherwise exactly the supplied calculated/estimated fallback is used; no invented priority between estimated and calculated rates. Rate is maximum across mechanisms, not sum. Local inspection type governs if any applicable mechanism is local, even when its rate is lower. No missing mechanism assumed absent, automatic mechanism screening, CML regression, rate confidence inference or forecast. Long-term current-process representativeness and rate/type provenance require qualification.'])
def thinning_rate_selection(x):
    ensure(bool(x.applicability_and_period_basis.strip()),'Applicable mechanisms and common assessed period qualification required')
    ids=[m.mechanism_id for m in x.mechanisms]
    ensure(all(s.strip() for s in ids) and len(set(ids))==len(ids),'Mechanism IDs must be nonblank and unique')
    rates,sources,ignored={},{},{}
    for item in x.mechanisms:
        ensure(item.measured is not None or item.fallback is not None,'Every mechanism requires a measured rate or explicit fallback')
        if item.measured is not None:
            ensure(item.measured.representative_for_current_period and bool(item.measured.measurement_basis.strip()),
                'Measured rate requires qualified current-process/period representativeness')
            rates[item.mechanism_id]=item.measured.corrosion_rate_m_year
            sources[item.mechanism_id]='measured'
        else:
            ensure(bool(item.fallback.rate_basis.strip()),'Fallback calculated/estimated rate basis required')
            rates[item.mechanism_id]=item.fallback.corrosion_rate_m_year
            sources[item.mechanism_id]=item.fallback.method
        ignored[item.mechanism_id]=item.measured is not None and item.fallback is not None
    maximum=max(rates.values())
    distribution='local' if any(m.thinning_type=='local' for m in x.mechanisms) else 'general'
    return dict(corrosion_rate_m_year=maximum,assessment_distribution=distribution,
        governing_rate_mechanism_ids=sorted(k for k,v in rates.items() if v==maximum),
        governing_type_mechanism_ids=sorted(m.mechanism_id for m in x.mechanisms if m.thinning_type==distribution),
        rate_by_mechanism_m_year=rates,selection_source_by_mechanism=sources,fallback_ignored_by_mechanism=ignored)


class SelectedMechanismThinning(Model):
    selection: ThinningRateSelection
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator='method')
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation('damage/thinning-selected-mechanisms','Selected multi-mechanism rate through qualified non-AST thinning',SelectedMechanismThinning,
    ['Part2 §§4.5.2,4.5.4,4.5.7; Table4.8'],origin='qualified_multi_mechanism_rate_to_thinning',limitations=[
        'Maximum selected rate drives one common wall/strength baseline; most localized assigned mechanism governs inspection scope. Caller must qualify inspections for that governing type and all applicable loss locations. Generic composition uses other monitoring row with table factor1; mechanism-specific credits cannot be borrowed across mechanisms. Qualified Table4.8 experience replacement is explicit. Custom priors remain supported. No rate summation, multiple-surface loss, all-mechanism DF, AST, cladding, CML history interpretation or whole-asset risk.'])
def selected_mechanism_thinning(x):
    ensure(x.conditions.monitoring.row.mechanism=='other','Generic multi-mechanism composition requires other monitoring row')
    selection=thinning_rate_selection(x.selection)
    result=qualified_unclad(QualifiedUnclad(assessment_scope='non_ast_unclad',qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=selection['corrosion_rate_m_year'],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**selection,**result}
