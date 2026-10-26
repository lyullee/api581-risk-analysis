"""2016 Annex2.B section7 NH4HS sour-water corrosion and sour-water routing."""
from bisect import bisect_left
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure, finite_tree
from .co2_corrosion import PSI_PA
from .acid_sour_water import AcidSourRoute, route as acid_route, AcidSourAssessment, assessment as acid_assessment
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Units = Literal["printed_si","printed_us_converted"]
_C = (.02,.05,.1,.15)
_VSI = (3.05,4.57,6.10,7.62,9.14)
_VUS = tuple(v*.3048 for v in (10,15,20,25,30))
_SI = ((.08,.10,.13,.20,.28),(.15,.23,.30,.38,.46),(.51,.69,.89,1.09,1.27),(1.14,1.78,2.54,3.81,5.08))
_US = ((3,4,5,8,11),(6,9,12,15,18),(20,27,35,43,50),(45,70,100,150,200))


class H2SPartialPressure(Model):
    total_pressure_pa_abs: Positive
    h2s_mole_fraction: Fraction


@calculation("properties/h2s-partial-pressure", "H2S partial pressure from absolute pressure and mole fraction", H2SPartialPressure,
    ["Part2 Table2.B.7.1; PDF p379"],limitations=["Public mole fraction0..1, not printed mole-percent number multiplied without/100. AbsolutePa, not gauge. Product only; no gas-liquid equilibrium, dissolvedH2S or fugacity calculation."])
def partial_pressure(x):
    p = x.total_pressure_pa_abs*x.h2s_mole_fraction
    ensure(p > 0 or x.h2s_mole_fraction == 0,"H2S partial-pressure underflow","numerical_failure")
    return {"h2s_partial_pressure_pa_abs":p}


class NH4HSEstimate(Model):
    h2s_mass_fraction: Fraction
    nh3_mass_fraction: Fraction
    analytical_basis: str = Field(min_length=1)
    excess_h2s_policy: Literal["reject_disputed_branch","qualified_printed_literal"]
    excess_h2s_qualification_basis: str | None = None
    equality_policy: Literal["reject_unassigned_equality","qualified_lower_branch","qualified_upper_branch"]
    equality_qualification_basis: str | None = None


@calculation("damage/alkaline-sour-water-nh4hs-estimate", "Source NH4HS analytical approximation with disputed branch gate", NH4HSEstimate,
    ["Part2 Table2.B.7.1; PDF p379"],limitations=[
        "Source prefers ionic process model. Printed ifH2S<2*NH3:NH4HS=1.5*H2S; ifH2S>2*NH3:NH4HS=3*H2S, notNH3. Excess branch rejected unless qualified literal use; no undocumented ammonia-limited repair. Equality unassigned, requires explicit qualified lower/upper selection or error. Public mass fractions, same condensed-water analytical basis, H2S+NH3<=1. Literal estimate can exceed1; raw value/flag retained, not clipped or claimed mass-balanced chemistry. Integrated table rejects out-of-range concentration."])
def nh4hs_estimate(x):
    ensure(bool(x.analytical_basis.strip()) and x.h2s_mass_fraction+x.nh3_mass_fraction <= 1,"Analytical basis or common mass fractions invalid")
    excess = x.excess_h2s_policy == "qualified_printed_literal"
    ensure((x.excess_h2s_qualification_basis is not None and bool(x.excess_h2s_qualification_basis.strip())) if excess else x.excess_h2s_qualification_basis is None,"Disputed excess policy and basis must agree")
    equality = x.equality_policy != "reject_unassigned_equality"
    ensure((x.equality_qualification_basis is not None and bool(x.equality_qualification_basis.strip())) if equality else x.equality_qualification_basis is None,"Equality policy and basis must agree")
    equal = x.h2s_mass_fraction == 2*x.nh3_mass_fraction
    if equal:
        ensure(equality,"ExactH2S=2*NH3 boundary unassigned by source","nh4hs_unassigned_equality")
        upper = x.equality_policy == "qualified_upper_branch"
        branch = "qualified_equality_upper" if upper else "qualified_equality_lower"
    else:
        upper = x.h2s_mass_fraction > 2*x.nh3_mass_fraction
        branch = "printed_excess_h2s" if upper else "printed_lower_h2s"
    ensure(not upper or excess,"Disputed printed excess-H2S formula requires qualified literal policy","nh4hs_disputed_formula")
    value = x.h2s_mass_fraction*(3. if upper else 1.5)
    return {"estimated_nh4hs_mass_fraction":value,"concentration_estimate_branch":branch,"estimated_fraction_exceeds_one":value > 1}


class AlkalineVelocity(Model):
    phase_regime: Literal["two_phase","liquid_full"]
    vapor_velocity_m_s: NonNegative | None = None
    liquid_velocity_m_s: NonNegative | None = None
    qualification_basis: str = Field(min_length=1)


@calculation("damage/alkaline-sour-water-velocity-selection", "Select vapor or liquid velocity for NH4HS table", AlkalineVelocity,
    ["Part2 Table2.B.7.1; PDF p379"],limitations=[
        "Two-phase system uses vapor-phase velocity, liquid-full system uses liquid velocity. Bulk/mixture velocity is not substituted. Two-phase liquid velocity may be supplied as contextual input but is not selected. Vapor input in liquid-full case rejected. No phase fractions, holdup, slip velocity or wall-shear calculation inferred."])
def velocity_selection(x):
    ensure(bool(x.qualification_basis.strip()),"Phase-specific velocity qualification required")
    if x.phase_regime == "two_phase":
        ensure(x.vapor_velocity_m_s is not None,"Two-phase NH4HS table requires vapor velocity")
        v,phase = x.vapor_velocity_m_s,"vapor"
    else:
        ensure(x.liquid_velocity_m_s is not None and x.vapor_velocity_m_s is None,"Liquid-full case requires liquid velocity and no vapor velocity")
        v,phase = x.liquid_velocity_m_s,"liquid"
    return {"selected_velocity_m_s":v,"selected_velocity_phase":phase}


class AlkalineBase(Model):
    nh4hs_mass_fraction: Fraction
    selected_velocity_m_s: NonNegative
    unit_basis: Units
    lookup_policy: Literal["exact_nodes_only","bilinear","maximum_bracketing_value"]


def _bracket(nodes,value):
    value = next((n for n in nodes if abs(n-value) <= 1e-10),value)
    ensure(nodes[0] <= value <= nodes[-1],"NH4HS concentration/velocity outside source table; no extrapolation")
    i = bisect_left(nodes,value)
    return (i,i,0.) if value == nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


@calculation("damage/alkaline-sour-water-base-rate", "NH4HS and phase-velocity baseline carbon-steel corrosion rate", AlkalineBase,
    ["Part2 Tables2.B.7.2/7.2M; PDF pp379-380"],limitations=[
        "20cells per unit basis:NH4HS2/5/10/15wt%,SI3.05/4.57/6.10/7.62/9.14m/s,US10/15/20/25/30ft/s. Public fractions/m/s/m-year; rounded SI rates/grid versus exactUS conversions explicit. Exact/bilinear/max-bracketing numerical policy required; no concentration or velocity extrapolation/edge defaults. Baseline before pressure correction, not independently modeled temperature/hydrocarbon effects."])
def base_rate(x):
    a,b,wc = _bracket(_C,x.nh4hs_mass_fraction)
    c,d,wv = _bracket(_VSI if x.unit_basis == "printed_si" else _VUS,x.selected_velocity_m_s)
    ensure(x.lookup_policy != "exact_nodes_only" or (a == b and c == d),"Exact baseline node policy does not interpolate")
    table = _SI if x.unit_basis == "printed_si" else _US
    if x.lookup_policy == "maximum_bracketing_value":
        value = max(table[a][c],table[a][d],table[b][c],table[b][d])
    else:
        lo,hi = table[a][c]+wv*(table[a][d]-table[a][c]),table[b][c]+wv*(table[b][d]-table[b][c])
        value = lo+wc*(hi-lo)
    return {"baseline_corrosion_rate_m_year":value*(.001 if x.unit_basis == "printed_si" else .0000254)}


class AlkalinePressure(Model):
    baseline_corrosion_rate_m_year: NonNegative
    h2s_partial_pressure_pa_abs: NonNegative
    equation_basis: Units


@calculation("damage/alkaline-sour-water-pressure-adjustment", "NH4HS sour-water H2S partial-pressure correction", AlkalinePressure,
    ["Part2 Tables2.B.7.2/7.2M notes1-2; PDF pp379-380"],limitations=[
        "US factor=1+(p_psia-50)/25 below50, /40 above;SI=1+(p_kPa-345)/173 below345,/276 above. At reference both expressions return1. Finalrate=max(baseline*factor,0). Public absolutePa; rounded pressure thresholds/slopes differ, basis explicit. Negative factor/low-pressure zero clamp flagged, not actual immunity to sour-water/wetH2S damage. No extrapolation range is specified by source pressure notes; owner qualifies actual pressure applicability."])
def pressure_adjustment(x):
    p,ref,low,high = (x.h2s_partial_pressure_pa_abs/1000,345.,173.,276.) if x.equation_basis == "printed_si" else (x.h2s_partial_pressure_pa_abs/PSI_PA,50.,25.,40.)
    branch = "at_reference" if p == ref else "below_reference" if p < ref else "above_reference"
    raw = 1+(p-ref)/(low if p < ref else high)
    factor = max(raw,0.)
    rate = x.baseline_corrosion_rate_m_year*factor
    finite_tree([raw,factor,rate])
    ensure(rate > 0 or factor == 0 or x.baseline_corrosion_rate_m_year == 0,"Pressure-adjusted rate underflow","numerical_failure")
    return {"corrosion_rate_m_year":rate,"unclamped_pressure_factor":raw,"pressure_correction_factor":factor,
        "negative_pressure_factor_clamped":raw < 0,"pressure_correction_branch":branch}


class SuppliedNH4HS(Model):
    method: Literal["supplied"]
    nh4hs_mass_fraction: Fraction
    qualification_basis: str = Field(min_length=1)


class EstimatedNH4HS(NH4HSEstimate):
    method: Literal["source_approximation"]


class AlkalineWet(Model):
    concentration: SuppliedNH4HS | EstimatedNH4HS = Field(discriminator="method")
    velocity: AlkalineVelocity
    h2s_partial_pressure_pa_abs: NonNegative
    baseline_unit_basis: Units
    pressure_equation_basis: Units
    lookup_policy: Literal["exact_nodes_only","bilinear","maximum_bracketing_value"]
    thinning_threshold_basis: Units
    qualification_basis: str = Field(min_length=1)


class AlkalineAssessment(Model):
    material: Literal["carbon_steel"]
    free_water_present: bool
    ph: float | None = Field(default=None,gt=7,le=14,strict=True,allow_inf_nan=False)
    h2s_ammonia_service_qualified: bool
    applicability_basis: str = Field(min_length=1)
    wet_model: AlkalineWet | None = None


@calculation("damage/alkaline-sour-water-assessment", "Qualified alkaline NH4HS carbon-steel corrosion assessment", AlkalineAssessment,
    ["Part2 Annex2.B §7,Tables7.1-7.2M; Table1.2; PDF pp323,378-381"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Carbon-steel free-water/H2S/NH3 service above neutralpH only; wet concentration preferably supplied from qualified ionic model/analysis. Disputed source approximations retain gates. Phase-specific velocity selected once; pressure correction applied to same baseline. Source table general/local classification uses<=6.1m/s or<=20ft/s as explicit threshold basis. Temperature/HC-water ratio effects are secondary but no quantitative correction supplied; not invented. Dry0 is NH4HS-specific, not zero all-mechanismDF. Low-pressure source clamp0 not validated absence of damage. No wetH2S cracking, material-alloy extension or process equilibrium inferred."])
def alkaline_assessment(x):
    ensure(bool(x.applicability_basis.strip()),"Alkaline service/water/pH applicability basis required")
    if not x.free_water_present:
        ensure(x.ph is None and x.wet_model is None,"Dry alkaline branch cannot carry unused aqueous pH/model")
        return {"corrosion_rate_m_year":0.,"baseline_corrosion_rate_m_year":None,"nh4hs_mass_fraction_used":None,"concentration_source":None,
            "selected_velocity_m_s":None,"selected_velocity_phase":None,"unclamped_pressure_factor":None,"pressure_correction_factor":None,
            "negative_pressure_factor_clamped":False,"pressure_correction_branch":None,"source_thinning_type":None,"calculation_branch":"no_free_water"}
    ensure(x.ph is not None and x.h2s_ammonia_service_qualified and x.wet_model is not None,"Wet alkaline calculation requires qualifiedpH>7 H2S/NH3 and wet model")
    m = x.wet_model
    ensure(bool(m.qualification_basis.strip()),"Condensed-water concentration and pressure applicability qualification required")
    if m.concentration.method == "supplied":
        ensure(bool(m.concentration.qualification_basis.strip()),"Supplied NH4HS concentration qualification required")
        concentration = m.concentration.nh4hs_mass_fraction
    else:
        concentration = nh4hs_estimate(m.concentration)["estimated_nh4hs_mass_fraction"]
    vel = velocity_selection(m.velocity)
    base = base_rate(AlkalineBase(nh4hs_mass_fraction=concentration,selected_velocity_m_s=vel["selected_velocity_m_s"],unit_basis=m.baseline_unit_basis,lookup_policy=m.lookup_policy))
    adjusted = pressure_adjustment(AlkalinePressure(baseline_corrosion_rate_m_year=base["baseline_corrosion_rate_m_year"],h2s_partial_pressure_pa_abs=m.h2s_partial_pressure_pa_abs,equation_basis=m.pressure_equation_basis))
    threshold = 6.1 if m.thinning_threshold_basis == "printed_si" else 20*.3048
    return {**base,**vel,**adjusted,"nh4hs_mass_fraction_used":concentration,"concentration_source":m.concentration.method,
        "source_thinning_type":"general" if vel["selected_velocity_m_s"] <= threshold else "local","calculation_branch":"wet_nh4hs_model"}


class AlkalineThinning(Model):
    corrosion: AlkalineAssessment
    assessment_distribution: Literal["general","local"]
    distribution_qualification_basis: str = Field(min_length=1)
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/alkaline-sour-water-thinning-assessment", "NH4HS corrosion through qualified non-AST unclad thinning DF", AlkalineThinning,
    ["Part2 Annex2.B §7,Table1.2; Part2 §4.5.7,Table4.8"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Same selected phase velocity and rate drive sour-water monitoring and wall loss. Explicit source general/local classification retained separately from owner-qualified inspection/distribution; no automatic coverage validation. Source pressure-clamp0 does not force DF0: strength/uncertainty/floor remain. Non-AST unclad only; no ammonia/wetH2S cracking, material extension, two-phase EOS, all-mechanismDF or code/FFS."])
def alkaline_thinning(x):
    ensure(bool(x.distribution_qualification_basis.strip()),"Actual general/local distribution and inspection basis required")
    corrosion = alkaline_assessment(x.corrosion)
    monitor = x.conditions.monitoring.row
    ensure(monitor.mechanism == "sour_water","NH4HS model requires sour-water monitoring row")
    if corrosion["selected_velocity_m_s"] is not None:
        ensure(monitor.velocity_m_s == corrosion["selected_velocity_m_s"],"Monitoring must use same selected phase velocity as NH4HS rate model")
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,"assessment_distribution":x.assessment_distribution}


from .hydrochloric_acid import HClAssessment, assessment as hcl_assessment


class SourWaterAssessment(Model):
    screening: AcidSourRoute
    acid_model: AcidSourAssessment | None = None
    alkaline_model: AlkalineAssessment | None = None
    hcl_model: HClAssessment | None = None
    hcl_shared_phase_qualification_basis: str | None = None


@calculation("damage/sour-water-assessment", "Route qualified sour water to acid or alkaline quantitative model", SourWaterAssessment,
    ["Part2 Annex2.B §§2,7,10,Figures2.1,10.1; PDF pp324-330,378-381,392-396"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Reuses explicit free-water/pH/chloride policies. Executes only matching supplied acid/alkaline/HCl model, never sums them. Acid child screening must match entire shared request; alkaline child must have same free-water/pH. HCl child requires shared separated-phase qualification and matching available pH/chloride; screeningroute alone does not establish dilute HCl applicability. Neutral-unclassified errors, never zero. Returns common selected-rate fields; independent APIs retain detailed diagnostics including HCl999-cell flags. Dry0 source-specific; no all-mechanismDF or immunity statement."])
def sour_water_assessment(x):
    routed = acid_route(x.screening)
    choice = routed["corrosion_route"]
    if choice != "hydrochloric_acid":
        ensure(x.hcl_model is None and x.hcl_shared_phase_qualification_basis is None,"Non-HCl route cannot carry unused HCl model or basis")
    if choice == "no_free_water":
        ensure(x.acid_model is None and x.alkaline_model is None,"Dry route cannot carry unused quantitative models")
        result = {"corrosion_rate_m_year":0.,"base_corrosion_rate_m_year":None,"selected_rate_is_screening_bound":False,"localized_attack_review_required":False}
    elif choice == "acid_sour_water":
        ensure(x.acid_model is not None and x.alkaline_model is None,"Acid route requires only matching acid model")
        ensure(x.acid_model.screening == x.screening,"Acid child and shared screening requests must match")
        result = acid_assessment(x.acid_model)
    elif choice == "alkaline_sour_water":
        ensure(x.alkaline_model is not None and x.acid_model is None,"Alkaline route requires only matching alkaline model")
        ensure(x.alkaline_model.free_water_present == x.screening.free_water_present and x.alkaline_model.ph == x.screening.ph,"Alkaline model and shared pH/water must match")
        alkaline = alkaline_assessment(x.alkaline_model)
        result = {**alkaline,"base_corrosion_rate_m_year":alkaline["baseline_corrosion_rate_m_year"],"selected_rate_is_screening_bound":False,
            "localized_attack_review_required":alkaline["source_thinning_type"] == "local"}
    elif choice == "hydrochloric_acid":
        ensure(x.hcl_model is not None and x.acid_model is None and x.alkaline_model is None,"HCl route requires only matching HCl model")
        ensure(x.hcl_shared_phase_qualification_basis is not None and bool(x.hcl_shared_phase_qualification_basis.strip()),"HCl child and shared screening need same separated acid-phase qualification")
        ensure(x.hcl_model.free_water_present == x.screening.free_water_present,"HCl and shared free-water state must match")
        hcl = hcl_assessment(x.hcl_model)
        if hcl["ph_used"] is not None:
            ensure(hcl["ph_used"] == x.screening.ph,"HCl model and shared separated-phase pH must match")
        if hcl["chloride_mass_fraction_used"] is not None and x.screening.chloride_concentration_ppm is not None:
            ensure(abs(hcl["chloride_mass_fraction_used"]*1e6-x.screening.chloride_concentration_ppm) <= 1e-9,"HCl and shared chloride concentration must match")
        result = {"corrosion_rate_m_year":hcl["corrosion_rate_m_year"],"base_corrosion_rate_m_year":hcl["corrosion_rate_m_year"],
            "selected_rate_is_screening_bound":False,"localized_attack_review_required":True}
    else:
        ensure(False,"Sour-water route needs neutral-boundary resolution; no automatic zero","different_corrosion_mechanism")
    return {**routed,"corrosion_rate_m_year":result["corrosion_rate_m_year"],"selected_model_base_rate_m_year":result["base_corrosion_rate_m_year"],
        "selected_rate_is_screening_bound":result["selected_rate_is_screening_bound"],"localized_attack_review_required":result["localized_attack_review_required"]}
