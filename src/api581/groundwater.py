"""Annex2.B §11.3.3 groundwater guidance; no invented TKS/rate correlation."""
import math
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure
from .thinning import WallLoss, Posterior
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad


Units=Literal['printed_si','printed_us_converted']


class GroundwaterChemistry(Model):
    chloride_mg_l: NonNegative
    sulfate_mg_l: NonNegative
    dissolved_co2_mg_l: NonNegative
    bicarbonate_mg_l: NonNegative
    carbonate_mg_l: NonNegative
    sulfide_mg_l: NonNegative
    ammonia_mg_l: NonNegative
    concentration_basis: str = Field(min_length=1)


@calculation('damage/groundwater-tks','Groundwater Total Key Species on a qualified common concentration basis',GroundwaterChemistry,
    ['Part2 Annex2.B §11.3.3; PDF p405'],limitations=[
        'Sum of seven explicitly supplied species concentrations, public mg/L on a qualified common analytical basis. No missing species assumed zero, molar/mass conversion, speciation or charge balance. Inputs must not double-count total inorganic carbon or report nitrogen/sulfur equivalents without conversion qualification. Source supplies no TKS thresholds or TKS-to-corrosion-rate equation; no automatic corrosivity or corrosion rate inferred.'])
def groundwater_tks(x):
    ensure(bool(x.concentration_basis.strip()),'Consistent analytical species concentration basis required')
    values=[getattr(x,name) for name in GroundwaterChemistry.model_fields if name!='concentration_basis']
    try:
        total=math.fsum(values)
    except OverflowError:
        ensure(False,'TKS sum exceeds finite numerical domain','numerical_failure')
    return {'total_key_species_mg_l':total}


class GroundwaterRate(Model):
    corrosion_rate_m_year: NonNegative
    unit_basis: Units
    shared_boundary_policy: Literal['lower_severity','higher_severity'] | None = None


@calculation('damage/groundwater-rate-classification','Groundwater steel corrosivity category from supplied corrosion rate',GroundwaterRate,
    ['Part2 Annex2.B §11.3.3(a)-(d); PDF p405'],limitations=[
        'Classifies a supplied steel corrosion rate, not TKS. Printed SI limits.03/.25/1.27mm/year differ from1/10/50mpy converted exactly. Explicit unit basis required. The medium/high shared.25mm/year or10mpy endpoint needs explicit lower/higher severity policy. Low is strictly below first threshold; very high strictly above last. No material-specific rate prediction, treatment credit or degradation immunity.'])
def groundwater_rate_classification(x):
    first,middle,last=(.00003,.00025,.00127) if x.unit_basis=='printed_si' else (.0000254,.000254,.00127)
    rate=x.corrosion_rate_m_year
    shared=rate==middle
    ensure((x.shared_boundary_policy is not None)==shared,
        'Medium/high shared endpoint requires a boundary policy, unused policy must be omitted','ambiguous_groundwater_boundary')
    category=('low' if rate<first else 'medium' if rate<middle else
        ('medium' if x.shared_boundary_policy=='lower_severity' else 'high') if shared else
        'high' if rate<=last else 'very_high')
    bounds={'low':(0.,first,'inclusive','exclusive'),'medium':(first,middle,'inclusive','inclusive'),
        'high':(middle,last,'inclusive','inclusive'),'very_high':(last,None,'exclusive','unbounded')}
    lower,upper,lower_relation,upper_relation=bounds[category]
    return dict(corrosion_rate_m_year=rate,corrosivity_category=category,selected_unit_basis=x.unit_basis,
        category_lower_bound_m_year=lower,category_upper_bound_m_year=upper,
        lower_bound_relation=lower_relation,upper_bound_relation=upper_relation,shared_boundary_encountered=shared)


class GroundwaterAssessment(Model):
    chemistry: GroundwaterChemistry
    qualified_rate: GroundwaterRate
    steel_applicability_basis: str = Field(min_length=1)
    specialist_rate_basis: str = Field(min_length=1)


@calculation('damage/groundwater-assessment','Qualified groundwater chemistry and externally established steel corrosion rate',GroundwaterAssessment,
    ['Part2 Annex2.B §11.3.3; PDF p405'],origin='source_guidance_with_qualified_external_rate',limitations=[
        'Competent water-corrosivity specialist must establish the steel corrosion rate independently. TKS is reported alongside that rate, never used to invent source cutoffs or a rate regression. No groundwater-specific quantitative rate equation is provided by the standard. Chemistry, material and specialist qualifications are supplied, not independently verified.'])
def groundwater_assessment(x):
    ensure(bool(x.steel_applicability_basis.strip()) and bool(x.specialist_rate_basis.strip()),
        'Steel applicability and competent-specialist rate bases required')
    return {**groundwater_tks(x.chemistry),**groundwater_rate_classification(x.qualified_rate),
        'rate_source':'qualified_external_groundwater_rate','tks_to_rate_model_available':False}


class GroundwaterThinning(Model):
    corrosion: GroundwaterAssessment
    assessment_distribution: Literal['general','local']
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator='method')
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation('damage/groundwater-thinning-assessment','Qualified groundwater rate through non-AST unclad thinning',GroundwaterThinning,
    ['Part2 Annex2.B §11.3.3; Part2 §4.5.7,Table4.8'],origin='qualified_external_groundwater_rate_to_thinning',limitations=[
        'Same externally qualified groundwater rate drives loss and non-AST unclad thinning; general/local inspection and steel applicability require explicit basis. No automatic pitting multiplier, TKS-derived rate, MIC/deposit exclusions or treatment credit. Monitoring row must be other; no borrowed acid/sour-water credits. Qualified experience replacement remains separately available under Table4.8. No cladding, AST, FFS or all-mechanism assessment.'])
def groundwater_thinning(x):
    ensure(x.conditions.monitoring.row.mechanism=='other','Groundwater must use other-mechanism monitoring row')
    corrosion=groundwater_assessment(x.corrosion)
    result=qualified_unclad(QualifiedUnclad(assessment_scope='non_ast_unclad',qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion['corrosion_rate_m_year'],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,'assessment_distribution':x.assessment_distribution}
