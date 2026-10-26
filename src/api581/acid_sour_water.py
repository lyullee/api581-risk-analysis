"""2016 Annex2.B section10 acid sour water routing, rate and thinning."""
from bisect import bisect_left
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, Fraction, calculation, ensure, finite_tree
from .thinning import Posterior, WallLoss
from .clad_thinning import PressureStrength, CodeStrength
from .thinning_conditions import ThinningConditions, QualifiedUnclad, qualified_unclad

Units = Literal["printed_si","printed_us_converted"]
_PH = (4.75,5.25,5.75,6.25,6.75)
_SI = ((.03,.08,.13,.18),(.02,.05,.08,.1),(.01,.04,.05,.08),(.01,.03,.04,.05),(.01,.01,.02,.03))
_US = ((1,3,5,7),(.7,2,3,4),(.4,1.5,2,3),(.3,1,1.5,2),(.2,.5,.7,1))


class AcidSourRoute(Model):
    free_water_present: bool
    ph: float | None = Field(default=None,ge=0,le=14,strict=True,allow_inf_nan=False)
    chlorides_present: bool | None = None
    chloride_concentration_ppm: NonNegative | None = None
    chloride_policy: Literal["figure_any_presence_routes_hcl","qualified_below_50ppm"] | None = None
    chloride_qualification_basis: str | None = None
    neutral_ph_policy: Literal["detailed_body_inclusive","unclassified_at_neutral"] | None = None
    qualification_basis: str = Field(min_length=1)


@calculation("damage/acid-sour-water-route", "Acid sour water free-water pH and chloride route", AcidSourRoute,
    ["Part2 Annex2.B Table1.1,§10.1-10.3,Figure10.1; PDF pp322,392-393,396"],limitations=[
        "No free water gives source-specific dry branch. Detailed pH<4.5 routesHCl,>7 routes alkaline sour water, otherwise acid sour. Overview sayspH<7: exact7 can follow explicit detailed-body inclusion or remain unclassified, not guessed. Figure any chloride presence routesHCl, while Annex screen permits<50ppm and body assumes insignificant chloride: qualified-below50ppm policy requires concentration and basis. Route result does not execute another mechanism or assert zero total damage; use lowest separated-water-phase pH, not unqualified bulk average."])
def route(x):
    ensure(bool(x.qualification_basis.strip()),"Water/pH/source qualification required")
    if not x.free_water_present:
        ensure(all(v is None for v in (x.ph,x.chlorides_present,x.chloride_concentration_ppm,x.chloride_policy,x.chloride_qualification_basis,x.neutral_ph_policy)),
            "Dry branch cannot carry unused water-phase screening inputs")
        decision = "no_free_water"
    else:
        ensure(x.ph is not None and x.neutral_ph_policy is not None,"Wet route requires pH and explicit neutral boundary policy")
        ensure(x.chlorides_present is not None and x.chloride_policy is not None,"Wet route requires explicit chloride screening")
        if x.chloride_concentration_ppm is not None:
            ensure((x.chloride_concentration_ppm > 0) == x.chlorides_present,"Chloride presence and supplied concentration must agree")
        qualified = x.chloride_policy == "qualified_below_50ppm"
        ensure((x.chloride_qualification_basis is not None and bool(x.chloride_qualification_basis.strip()) and x.chloride_concentration_ppm is not None) if qualified else x.chloride_qualification_basis is None,
            "Qualified chloride policy requires concentration and insignificant-corrosive basis")
        chloride_routes = (x.chloride_concentration_ppm >= 50) if qualified else x.chlorides_present
        if x.ph > 7:
            decision = "alkaline_sour_water"
        elif x.ph < 4.5:
            decision = "hydrochloric_acid"
        elif x.ph == 7 and x.neutral_ph_policy == "unclassified_at_neutral":
            decision = "neutral_boundary_unclassified"
        else:
            decision = "hydrochloric_acid" if chloride_routes else "acid_sour_water"
    return {"corrosion_route":decision}


class AcidSourBase(Model):
    ph: float = Field(ge=4.5,le=7,strict=True,allow_inf_nan=False)
    maximum_water_temperature_k: Positive
    unit_basis: Units
    lookup_policy: Literal["exact_nodes_only","bilinear","maximum_bracketing_value"]
    ph_edge_policy: Literal["reject_unprinted_ph","qualified_nearest_edge_row"]
    ph_edge_qualification_basis: str | None = None


def _bracket(nodes,value):
    value = next((n for n in nodes if abs(n-value) <= 1e-9),value)
    ensure(nodes[0] <= value <= nodes[-1],"Outside acid sour source table; no extrapolation")
    i = bisect_left(nodes,value)
    return (i,i,0.) if value == nodes[i] else (i-1,i,(value-nodes[i-1])/(nodes[i]-nodes[i-1]))


@calculation("damage/acid-sour-water-base-rate", "Acid sour water pH and temperature base corrosion rate", AcidSourBase,
    ["Part2 Tables2.B.10.2/10.2M; PDF pp394-395"],limitations=[
        "20SI and20US cells; pH4.75..6.75,SI38/52/79/93C orUS100/125/175/200F. Explicit basis preserves rounded temperatures/rates. Detailed scope4.5..7 extends beyond table: missing pH edge bands reject or use qualified nearest-edge row, flagged, never silent clamping. Temperature never extrapolated. Between-node handling exact/bilinear/max-bracketing explicit numerical policy, not source instruction. Lowest separated aqueous-phase pH and maximum water temperature, including local heating, must be qualified."])
def base_rate(x):
    qualified = x.ph_edge_policy == "qualified_nearest_edge_row"
    ensure((x.ph_edge_qualification_basis is not None and bool(x.ph_edge_qualification_basis.strip())) if qualified else x.ph_edge_qualification_basis is None,"pH edge policy and basis must agree")
    edge = x.ph < 4.75 or x.ph > 6.75
    ensure(not edge or qualified,"pH in source-scope edge band lacks printed rate row","acid_sour_ph_edge")
    ph = min(max(x.ph,4.75),6.75)
    temps = tuple(c+273.15 for c in (38,52,79,93)) if x.unit_basis == "printed_si" else tuple((f-32)*5/9+273.15 for f in (100,125,175,200))
    a,b,wp = _bracket(_PH,ph)
    c,d,wt = _bracket(temps,x.maximum_water_temperature_k)
    ensure(x.lookup_policy != "exact_nodes_only" or (a == b and c == d),"Exact-node policy does not interpolate")
    table = _SI if x.unit_basis == "printed_si" else _US
    if x.lookup_policy == "maximum_bracketing_value":
        native = max(table[a][c],table[a][d],table[b][c],table[b][d])
    else:
        lower = table[a][c]+wt*(table[a][d]-table[a][c])
        upper = table[b][c]+wt*(table[b][d]-table[b][c])
        native = lower+wp*(upper-lower)
    return {"base_corrosion_rate_m_year":native*(.001 if x.unit_basis == "printed_si" else .0000254),"ph_for_lookup":ph,"ph_edge_row_used":edge}


class AcidSourOxygen(Model):
    oxygen_content_ppb: NonNegative


@calculation("damage/acid-sour-water-oxygen-factor", "Acid sour water oxygen adjustment factor", AcidSourOxygen,
    ["Part2 Table2.B.10.3; PDF p395"],limitations=[
        "Table oxygen<=50ppb factor1,>50ppb factor2. Detailed scope says normal<50ppb; equality follows explicit table. High oxygen can introduce localized/pitting attack: factor2 is source general-rate correction, not a separate pitting prediction or wetH2S cracking assessment."])
def oxygen(x):
    return {"oxygen_factor":1. if x.oxygen_content_ppb <= 50 else 2.,"high_oxygen_localized_review":x.oxygen_content_ppb > 50}


class AcidSourVelocity(Model):
    velocity_m_s: NonNegative
    equation_basis: Units


@calculation("damage/acid-sour-water-velocity-factor", "Acid sour water piecewise velocity factor", AcidSourVelocity,
    ["Part2 eqs(2.B.2)-(2.B.7); PDF p393"],limitations=[
        "SI: below1.83m/s factor1,1.83..6.10 inclusive .82*v-.5,above6.10 factor5. US: below6ft/s1,6..20 inclusive .25*v-.5,above20 factor5. Publicm/s, explicit basis; equality and discontinuity at high threshold retained, not smoothed. High velocity requires localized-attack review; factor5 is not erosion/CFD or cracking model."])
def velocity(x):
    lo,hi = (1.83,6.10) if x.equation_basis == "printed_si" else (6*.3048,20*.3048)
    middle = .82*x.velocity_m_s-.5 if x.equation_basis == "printed_si" else .25*(x.velocity_m_s/.3048)-.5
    value = 1. if x.velocity_m_s < lo else middle if x.velocity_m_s <= hi else 5.
    return {"velocity_factor":value,"high_velocity_localized_review":x.velocity_m_s > lo}


class AcidSourEquation(Model):
    base_corrosion_rate_m_year: NonNegative
    oxygen_factor: Positive
    velocity_factor: Positive


@calculation("damage/acid-sour-water-rate-equation", "Acid sour water base rate times oxygen and velocity", AcidSourEquation,
    ["Part2 Annex2.B §10.3 eq(2.B.1); PDF p393"],limitations=["CR=CRpH*FO*FV. Context-specific duplicate equation number is Annex2.B §10, not other source equations2.B.1. Applicability, water/pH/chloride and material qualification are separate."])
def rate_equation(x):
    value = x.base_corrosion_rate_m_year*x.oxygen_factor*x.velocity_factor
    finite_tree(value)
    ensure(value > 0 or x.base_corrosion_rate_m_year == 0,"Acid sour corrosion product underflow","numerical_failure")
    return {"corrosion_rate_m_year":value}


class AcidSourOtherMaterial(Model):
    service_suitability_qualified: bool
    other_degradation_assessed: bool
    rate_policy: Literal["body_upper_bound_screening","figure_nominal_2mpy"]
    body_unit_basis: Units | None = None
    qualification_basis: str = Field(min_length=1)


@calculation("damage/acid-sour-water-other-material-rate", "Acid sour water suitable-other-material source estimate", AcidSourOtherMaterial,
    ["Part2 §10.1.2(c),Figure10.1; PDF pp392,396"],limitations=[
        "Body assumes suitable other material corrosion will not exceed.05mm/y(2mpy); figure assignsCR=2mpy. Explicit choice returns body upper-bound screening or figure nominal point. Rounded bodySI.00005m/y differs from exact2mpy=.0000508. Requires actual suitability and other-degradation assessment; no alloy-name immunity to wetH2S cracking/ClSCC/dealloying. No oxygen/velocity correction automatically applied to separate other-material branch."])
def other_material(x):
    ensure(x.service_suitability_qualified and x.other_degradation_assessed and bool(x.qualification_basis.strip()),"Other-material source estimate requires qualified suitability and separate degradation review")
    bound = x.rate_policy == "body_upper_bound_screening"
    ensure((x.body_unit_basis is not None) if bound else x.body_unit_basis is None,"Body unit basis applies only to body bound policy")
    value = .00005 if bound and x.body_unit_basis == "printed_si" else 2*.0000254
    return {"corrosion_rate_m_year":value,"selected_rate_is_screening_bound":bound}


class AcidSourCarbon(Model):
    maximum_water_temperature_k: Positive
    unit_basis: Units
    lookup_policy: Literal["exact_nodes_only","bilinear","maximum_bracketing_value"]
    ph_edge_policy: Literal["reject_unprinted_ph","qualified_nearest_edge_row"]
    ph_edge_qualification_basis: str | None = None
    oxygen_content_ppb: NonNegative
    velocity_m_s: NonNegative
    velocity_equation_basis: Units
    qualification_basis: str = Field(min_length=1)


class AcidSourAssessment(Model):
    screening: AcidSourRoute
    material: Literal["carbon_steel","low_alloy_steel","other_material"]
    total_alloy_mass_fraction: Fraction | None = None
    primary_h2s_and_insignificant_other_corrosives_qualified: bool
    applicability_basis: str = Field(min_length=1)
    carbon_model: AcidSourCarbon | None = None
    other_material_model: AcidSourOtherMaterial | None = None


@calculation("damage/acid-sour-water-assessment", "Acid sour water routed material and corrected corrosion estimate", AcidSourAssessment,
    ["Part2 Annex2.B §10,Tables10.1-10.3,Figure10.1; PDF pp392-396"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Free-water/pH/chloride routing first. HCl/alkaline/neutral-unclassified routes error rather than fake zero or silently calculate acid-sour rate. Dry branch0 is acid-sour-specific only, with null uncomputed factors. Wet acid branch requires primaryH2S and insignificant ammonia/CO2/cyanides/other-corrosive qualification; no actual mixed-chemistry model. Body quantitativeCS scope versus tablelow-alloy<=6% preserved through explicit low-alloy fraction. Other material requires qualified separate fallback policy. High oxygen/velocity flags localized-attack review; no automatic pit multiplier or wetH2S crackingDF. General thinning source classification is not proof localized attack absent."])
def assessment(x):
    ensure(bool(x.applicability_basis.strip()),"Acid-sour applicability basis required")
    routed = route(x.screening)
    decision = routed["corrosion_route"]
    if decision == "no_free_water":
        ensure(x.carbon_model is None and x.other_material_model is None and x.total_alloy_mass_fraction is None,"Dry branch cannot carry unused material-rate inputs")
        return {**routed,"corrosion_rate_m_year":0.,"base_corrosion_rate_m_year":None,"ph_for_lookup":None,"ph_edge_row_used":False,
            "oxygen_factor":None,"velocity_factor":None,"localized_attack_review_required":False,"selected_rate_is_screening_bound":False,"default_thinning_type":"general"}
    ensure(decision == "acid_sour_water","Source routes to another or unresolved corrosion mechanism; acid-sour model not evaluated","different_corrosion_mechanism")
    ensure(x.primary_h2s_and_insignificant_other_corrosives_qualified,"Mixed-corrosive scope not qualified for acid-sour model")
    if x.material == "other_material":
        ensure(x.other_material_model is not None and x.carbon_model is None and x.total_alloy_mass_fraction is None,"Other material requires only qualified other-material model")
        return {**routed,**other_material(x.other_material_model),"base_corrosion_rate_m_year":None,"ph_for_lookup":None,"ph_edge_row_used":False,
            "oxygen_factor":None,"velocity_factor":None,"localized_attack_review_required":False,"default_thinning_type":"general"}
    ensure(x.other_material_model is None and x.carbon_model is not None,"Carbon/low-alloy branch requires only carbon rate model")
    if x.material == "low_alloy_steel":
        ensure(x.total_alloy_mass_fraction is not None and x.total_alloy_mass_fraction <= .06,"Table10.1 low-alloy scope requires known total alloy<=6mass%")
    else:
        ensure(x.total_alloy_mass_fraction is None,"Carbon-steel branch cannot carry unused low-alloy fraction")
    m = x.carbon_model
    ensure(bool(m.qualification_basis.strip()),"Lowest aqueous pH/maximum water temperature qualification required")
    base = base_rate(AcidSourBase(ph=x.screening.ph,maximum_water_temperature_k=m.maximum_water_temperature_k,unit_basis=m.unit_basis,
        lookup_policy=m.lookup_policy,ph_edge_policy=m.ph_edge_policy,ph_edge_qualification_basis=m.ph_edge_qualification_basis))
    oxy,vel = oxygen(AcidSourOxygen(oxygen_content_ppb=m.oxygen_content_ppb)),velocity(AcidSourVelocity(velocity_m_s=m.velocity_m_s,equation_basis=m.velocity_equation_basis))
    rate = rate_equation(AcidSourEquation(base_corrosion_rate_m_year=base["base_corrosion_rate_m_year"],oxygen_factor=oxy["oxygen_factor"],velocity_factor=vel["velocity_factor"]))
    return {**routed,**base,**rate,"oxygen_factor":oxy["oxygen_factor"],"velocity_factor":vel["velocity_factor"],
        "localized_attack_review_required":oxy["high_oxygen_localized_review"] or vel["high_velocity_localized_review"],
        "selected_rate_is_screening_bound":False,"default_thinning_type":"general"}


class AcidSourThinning(Model):
    corrosion: AcidSourAssessment
    assessment_distribution: Literal["general","local"]
    localized_attack_review_basis: str | None = None
    starting_thickness_m: Positive
    elapsed_years: NonNegative
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions
    qualification_basis: str = Field(min_length=1)


@calculation("damage/acid-sour-water-thinning-assessment", "Acid sour water rate through qualified non-AST thinning DF", AcidSourThinning,
    ["Part2 Annex2.B §10; Part2 §4.5.7,Table4.8"],origin="api581_composition_with_explicit_source_policies",limitations=[
        "Unclad non-AST component; same selected rate and thickness drive loss/strength. General source classification versus owner general/local inspection coverage explicit. High oxygen/velocity requires additional localized-attack review basis; no unsupported pit multiplier. Uses sour-water monitoring row with same measured velocity, never unrelatedHCl credit; monitoring source threshold20ft/s differs from acid-sour velocity correction6ft/s threshold. Other-material nominal estimate does not exclude other DFs. No all-mechanism DF, wetH2S cracking, AST, cladding, code/FFS or actual chemistry qualification."])
def acid_sour_thinning(x):
    corrosion = assessment(x.corrosion)
    if corrosion["localized_attack_review_required"]:
        ensure(x.localized_attack_review_basis is not None and bool(x.localized_attack_review_basis.strip()),"High oxygen/velocity requires qualified localized-attack review before thinning composition")
    else:
        ensure(x.localized_attack_review_basis is None,"Localized-attack review field is unused without source high-attack flag")
    monitor = x.conditions.monitoring.row
    ensure(monitor.mechanism == "sour_water","Acid sour water monitoring must use source sour-water row")
    if x.corrosion.carbon_model is not None:
        ensure(monitor.velocity_m_s == x.corrosion.carbon_model.velocity_m_s,"Sour-water rate and monitoring velocities must agree")
    result = qualified_unclad(QualifiedUnclad(assessment_scope="non_ast_unclad",qualification_basis=x.qualification_basis,
        wall=WallLoss(starting_thickness_m=x.starting_thickness_m,corrosion_rate_m_year=corrosion["corrosion_rate_m_year"],elapsed_years=x.elapsed_years),
        strength=x.strength,inspections=x.inspections,conditions=x.conditions))
    return {**corrosion,**result,"assessment_distribution":x.assessment_distribution}
