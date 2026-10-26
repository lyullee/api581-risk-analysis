"""2016 thinning monitoring and localized-piping adjustment conditions."""
from typing import Literal
from pydantic import Field
from .core import Model, NonNegative, Positive, calculation, ensure, finite_tree
from .thinning import WallLoss, Posterior, UncladThinning, unclad
from .clad_thinning import CladWall, PressureStrength, CodeStrength, CladThinning, clad_thinning, UncladDesignThinning, unclad_design

Row = Literal["hydrochloric_acid","high_temperature_sulfidic_naphthenic","high_temperature_h2s_h2",
    "sulfuric_low_velocity","sulfuric_high_velocity","hydrofluoric_acid","sour_water_low_velocity",
    "sour_water_high_velocity","amine_low_velocity","amine_high_velocity","other"]
Method = Literal["key_process_variables","electrical_resistance_probes","corrosion_coupons"]
_METHODS = Method.__args__
_TABLE = dict(zip(Row.__args__,[(10.,10.,2.),(10.,10.,2.),(1.,10.,1.),(20.,10.,2.),(10.,10.,1.),
    (10.,1.,1.),(20.,10.,2.),(10.,2.,2.),(20.,10.,2.),(10.,10.,1.),(1.,1.,1.)]))
_JOINT_ROWS = ("hydrochloric_acid","sulfuric_high_velocity")


class MonitoringRow(Model):
    mechanism: Literal["hydrochloric_acid","high_temperature_sulfidic_naphthenic","high_temperature_h2s_h2",
        "sulfuric_acid","hydrofluoric_acid","sour_water","amine","other"]
    velocity_m_s: NonNegative | None = None
    sulfuric_material_group: Literal["carbon_steel","stainless_steel","higher_alloy"] | None = None
    amine_velocity_regime: Literal["low","high"] | None = None
    amine_regime_basis: str | None = None


@calculation("damage/thinning-monitoring-row", "Select thinning online-monitoring table row", MonitoringRow,
    ["Part2 Table4.8; PDF p164"],limitations=[
        "Sulfuric acid low/high thresholds3/5/7ft/s for CS/SS/higher alloys, sour water20ft/s; public m/s with exact.3048 conversion. Threshold equality is low. Amine low/high numeric threshold is not supplied by this table: owner regime and basis required. Mechanism applicability and actual material classification are external qualifications. Printed sulfuric-acid label appends H2S/H2; this API follows named sulfuric-acid row, preserves issue in documentation and does not assert official erratum."])
def monitoring_row(x):
    velocity_case = x.mechanism in ("sulfuric_acid","sour_water")
    ensure((x.velocity_m_s is not None) == velocity_case,"Velocity required only for sulfuric acid or sour water table classification")
    ensure((x.sulfuric_material_group is not None) == (x.mechanism == "sulfuric_acid"),"Sulfuric material group applies only to sulfuric-acid row")
    if x.mechanism == "amine":
        ensure(x.amine_velocity_regime is not None and x.amine_regime_basis is not None and bool(x.amine_regime_basis.strip()),"Amine regime requires owner qualification; no numeric threshold inferred")
        row, threshold = "amine_"+x.amine_velocity_regime+"_velocity", None
    else:
        ensure(x.amine_velocity_regime is None and x.amine_regime_basis is None,"Amine regime fields apply only to amine")
        if velocity_case:
            threshold = (dict(carbon_steel=3.,stainless_steel=5.,higher_alloy=7.)[x.sulfuric_material_group] if x.mechanism == "sulfuric_acid" else 20.)*.3048
            row = ("sulfuric" if x.mechanism == "sulfuric_acid" else "sour_water")+("_low_velocity" if x.velocity_m_s <= threshold else "_high_velocity")
        else:
            row, threshold = x.mechanism, None
    return {"monitoring_row":row,"velocity_threshold_m_s":threshold}


class MonitoringCell(Model):
    monitoring_row: Row
    monitoring_method: Method
    key_variables_with_probes: bool = False


@calculation("damage/thinning-monitoring-table-factor", "Thinning online-monitoring table cell and explicit joint exception", MonitoringCell,
    ["Part2 Table4.8; PDF p164"],limitations=[
        "Table row factors in column order key variables/ER probes/coupons. HCl and high-velocity sulfuric key-variable factor rises10 to20 only in conjunction with probes. This independent cell lookup does not establish a qualified organized monitoring plan; use thinning-online-monitoring-factor for credit gate. Other methods require specialist judgment, not guessed table equivalence."])
def monitoring_cell(x):
    if x.key_variables_with_probes:
        ensure(x.monitoring_row in _JOINT_ROWS and x.monitoring_method == "key_process_variables","Joint20 exception applies only to named key-variable cells")
        value = 20.
    else:
        value = _TABLE[x.monitoring_row][_METHODS.index(x.monitoring_method)]
    return {"table_monitoring_factor":value}


class OnlineMonitoring(Model):
    row: MonitoringRow
    methods: list[Method] = Field(max_length=3)
    organized_monitoring_plan: bool
    qualification_basis: str | None = None
    key_variables_probe_conjunction_confirmed: bool = False
    experience_factor: Positive | None = None
    experience_factor_basis: str | None = None


@calculation("damage/thinning-online-monitoring-factor", "Qualified thinning monitoring credit without stacking", OnlineMonitoring,
    ["Part2 §4.5.7 STEP15(1),Table4.8 notes1-3; PDF pp155,164"],limitations=[
        "No organized plan means applied factor1 regardless of installed methods. Qualified plan must recognize mechanism, appropriate variables and specialist intervals. Choose maximum applicable method factor, never sum/product. Joint20 needs both key variables and ER probes plus confirmed conjunction. Table estimates may be replaced by owner-experience positive factor with basis under note1; replacement is entire applied factor, not a stacked bonus. No methods and no override gives1. Other monitoring methods require qualified experience basis; no automatic sensor-data efficacy classification."])
def online_monitoring(x):
    selected = monitoring_row(x.row)
    row = selected["monitoring_row"]
    ensure(len(set(x.methods)) == len(x.methods),"Monitoring methods must be unique")
    override = x.experience_factor is not None
    ensure(override == (x.experience_factor_basis is not None),"Experience factor and basis must be provided together")
    if override:
        ensure(bool(x.experience_factor_basis.strip()),"Experience factor basis must not be blank")
    if x.key_variables_probe_conjunction_confirmed:
        ensure(x.organized_monitoring_plan and row in _JOINT_ROWS and {"key_process_variables","electrical_resistance_probes"}.issubset(x.methods),"Joint monitoring exception requires qualified conjunction of both methods in applicable row")
    candidates = {m:monitoring_cell(MonitoringCell(monitoring_row=row,monitoring_method=m,
        key_variables_with_probes=x.key_variables_probe_conjunction_confirmed and m == "key_process_variables"))["table_monitoring_factor"] for m in x.methods}
    if not x.organized_monitoring_plan:
        ensure(not override and x.qualification_basis is None,"Unqualified plan cannot claim experience credit or qualification basis")
        factor, reason = 1., "no_organized_plan"
    elif x.methods or override:
        ensure(x.qualification_basis is not None and bool(x.qualification_basis.strip()),"Monitoring credit requires qualified organized-plan basis")
        factor, reason = (x.experience_factor,"qualified_experience_replacement") if override else (max(candidates.values()),"maximum_table_method")
    else:
        factor, reason = 1., "no_monitoring_methods"
    return {**selected,"online_monitoring_factor":factor,"candidate_method_factors":candidates,
        "monitoring_credit_basis":reason,"joint_exception_applied":x.key_variables_probe_conjunction_confirmed and not override}


class InjectionPoint(Model):
    component_scope: Literal["piping","non_piping"]
    injection_or_mix_point_present: bool
    highly_effective_targeted_inspection: bool
    inspection_basis: str | None = None


class Deadleg(Model):
    component_scope: Literal["piping","non_piping"]
    deadleg_present: bool
    highly_effective_targeted_inspection: bool
    inspection_basis: str | None = None


def _piping_factor(scope,present,inspected,basis):
    if scope == "non_piping":
        ensure(not present and not inspected and basis is None,"Piping feature and inspection credit cannot be claimed for non-piping component")
    if inspected:
        ensure(present and basis is not None and bool(basis.strip()),"Highly effective targeted inspection requires feature and qualification basis")
    else:
        ensure(basis is None,"Inspection basis cannot accompany unclaimed inspection")
    return 3. if present and not inspected else 1.


@calculation("damage/thinning-injection-point-factor", "Thinning injection or corrosive mix point adjustment", InjectionPoint,
    ["Part2 §4.5.7 STEP15(2); PDF p156"],limitations=[
        "Piping with injection/mix point factor3, reduced1 only by highly effective targeted inspection per source API570 reference. Owner classifies actual mix corrosion: flashing liquid/vapor mixing, water-bearing streams or mixed temperature below combined dew point. Generic inspection does not earn automatic credit. Non-piping factor1."])
def injection_point(x):
    return {"injection_point_factor":_piping_factor(x.component_scope,x.injection_or_mix_point_present,x.highly_effective_targeted_inspection,x.inspection_basis)}


@calculation("damage/thinning-deadleg-factor", "Thinning intermittent-service or stagnant deadleg adjustment", Deadleg,
    ["Part2 §4.5.7 STEP15(3); PDF p156"],limitations=[
        "Piping deadleg factor3, reduced1 only by highly effective inspection specifically addressing localized deadleg corrosion. Owner classifies intermittent/no-significant-flow service; no automatic velocity threshold. Non-piping factor1."])
def deadleg(x):
    return {"deadleg_factor":_piping_factor(x.component_scope,x.deadleg_present,x.highly_effective_targeted_inspection,x.inspection_basis)}


class ThinningConditions(Model):
    monitoring: OnlineMonitoring
    injection: InjectionPoint
    deadleg: Deadleg


def condition_factors(x):
    ensure(x.injection.component_scope == x.deadleg.component_scope,"Injection and deadleg component scopes must agree")
    return {**online_monitoring(x.monitoring),**injection_point(x.injection),**deadleg(x.deadleg)}


class ConditionalAdjustment(Model):
    assessment_scope: Literal["non_ast"]
    base_damage_factor: NonNegative
    conditions: ThinningConditions


@calculation("damage/thinning-conditional-adjustment", "Apply qualified non-AST thinning adjustment conditions", ConditionalAdjustment,
    ["Part2 §4.5.7 STEP15,eq(2.23),Table4.8; PDF pp155-156,164"],origin="api581_composition",limitations=[
        "Non-AST conditions only: AST construction, maintenance and settlement factors1. FinalDF=max(baseDF*injection*deadleg/monitoring,.1). Monitoring uses maximum qualified method or documented experience replacement; no duplicate monitoring factors. No automatic corrosion/inspection applicability screening."])
def conditional_adjustment(x):
    factors = condition_factors(x.conditions)
    value = x.base_damage_factor*factors["injection_point_factor"]*factors["deadleg_factor"]/factors["online_monitoring_factor"]
    finite_tree(value)
    return {**factors,"base_damage_factor":x.base_damage_factor,"thinning_damage_factor":max(value,.1)}


class QualifiedUnclad(Model):
    assessment_scope: Literal["non_ast_unclad"]
    qualification_basis: str = Field(min_length=1)
    wall: WallLoss
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions


@calculation("damage/thinning-unclad-qualified", "Unclad non-AST thinning with condition-derived adjustment factors", QualifiedUnclad,
    ["Part2 §4.5.7,eqs(2.13),(2.17)-(2.23),Table4.8; PDF pp153-156,164"],origin="api581_composition",limitations=[
        "Qualified non-AST unclad component; shared wall/strength baseline required. Governing strength method explicit; code minima and load applicability remain supplied. Conditions derive piping/monitoring adjustments rather than accepting duplicate numeric factors. Table row classification is not corrosion-mechanism applicability screening or inspection validation. No all-mechanism DF or AST corrections."])
def qualified_unclad(x):
    ensure(bool(x.qualification_basis.strip()),"Applicability basis must not be blank")
    factors = condition_factors(x.conditions)
    args = dict(wall=x.wall,inspections=x.inspections,injection_point_factor=factors["injection_point_factor"],
        deadleg_factor=factors["deadleg_factor"],online_monitoring_factor=factors["online_monitoring_factor"])
    if x.strength.method == "design_thickness_eq2_17":
        from .clad_thinning import DesignStrengthRatio
        result = unclad_design(UncladDesignThinning(**args,assessment_scope="non_ast_unclad_design_thickness_governed",
            qualification_basis=x.qualification_basis,strength=DesignStrengthRatio(**x.strength.model_dump(exclude={"method"}))))
    else:
        from .thinning import StrengthRatio
        result = unclad(UncladThinning(**args,strength=StrengthRatio(**x.strength.model_dump(exclude={"method"}))))
    return {k:v for k,v in {**result,**factors,"strength_method":x.strength.method}.items() if k not in ("governing_minimum_thickness_m","governing_thickness_source")}


class QualifiedClad(Model):
    assessment_scope: Literal["non_ast_pressure_vessel_sequential_cladding"]
    qualification_basis: str = Field(min_length=1)
    wall: CladWall
    strength: PressureStrength | CodeStrength = Field(discriminator="method")
    inspections: Posterior
    conditions: ThinningConditions


@calculation("damage/thinning-clad-qualified", "Clad pressure-vessel thinning with condition-derived monitoring adjustment", QualifiedClad,
    ["Part2 §4.5.7,eqs(2.11),(2.13)-(2.23),Table4.8; PDF pp152-156,164"],origin="api581_composition_with_explicit_zero_rate_extension",limitations=[
        "Non-AST pressure vessel with sequential-cladding scope, owner-qualified corrosion rates and baseline. Injection/deadleg conditions must both be non-piping. Shared monitoring classification drives one applied factor. Reuses clad zero-rate extension and both strength methods; no coating/lining, simultaneous backside corrosion, code-minimum calculation or all-mechanism DF."])
def qualified_clad(x):
    ensure(x.conditions.injection.component_scope == x.conditions.deadleg.component_scope == "non_piping","Clad pressure-vessel composition requires non-piping condition scope")
    factors = condition_factors(x.conditions)
    result = clad_thinning(CladThinning(assessment_scope="non_ast_pressure_vessel_sequential_cladding",qualification_basis=x.qualification_basis,
        wall=x.wall,strength=x.strength,inspections=x.inspections,injection_point_factor=factors["injection_point_factor"],
        deadleg_factor=factors["deadleg_factor"],online_monitoring_factor=factors["online_monitoring_factor"]))
    return {**result,**factors}
